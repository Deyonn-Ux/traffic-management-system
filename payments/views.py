
from io import BytesIO
import re

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Payment, TicketReference

PAYMENT_METHOD_GROUPS = {
    'in_app': {
        'label': 'In-App Payment',
        'methods': ('GCash', 'Maya', 'Visa'),
    },
    'digital': {
        'label': 'Digital Payment',
        'methods': ('Bank App', 'E-Wallet', 'QR Transfer'),
    },
    'counter': {
        'label': 'Over-the-Counter',
        'methods': ('Cash', 'Payment Center', 'LTO Cashier'),
    },
}


def normalize_plate(value):
    return re.sub(r'[^A-Z0-9]', '', value.upper())


def payment_list(request):
    payments = Payment.objects.select_related('user').order_by('-created_at')

    if request.user.is_staff:
        visible_payments = payments
    elif request.user.is_authenticated:
        visible_payments = payments.filter(user=request.user)
    else:
        visible_payments = Payment.objects.none()

    return render(request, 'payments/list.html', {'payments': visible_payments})


@login_required
def payment_checkout(request):
    receipt = None
    form_data = {}
    selected_channel = request.GET.get('channel', 'in_app')

    if request.method == 'POST':
        form_data = request.POST
        selected_channel = request.POST.get('payment_channel', 'in_app')
        method_group = PAYMENT_METHOD_GROUPS.get(selected_channel, PAYMENT_METHOD_GROUPS['in_app'])
        payment_method = request.POST.get('payment_method', method_group['methods'][0])
        ticket_number = request.POST.get('ticket_number', '').strip().upper()
        plate_number = request.POST.get('plate_number', '').strip().upper()

        if payment_method not in method_group['methods']:
            messages.error(request, f'Please choose a valid {method_group["label"].lower()} option.')
            return render(request, 'payments/checkout.html', {
                'receipt': receipt,
                'form_data': form_data,
                'payment_channel': selected_channel,
                'payment_channel_label': method_group['label'],
                'payment_methods': method_group['methods'],
                'default_payment_method': method_group['methods'][0],
                'is_counter_payment': selected_channel == 'counter',
            })

        ticket_reference = (
            TicketReference.objects
            .select_related('violation__vehicle')
            .filter(reference_number=ticket_number, is_active=True)
            .first()
        )

        if not ticket_reference or normalize_plate(ticket_reference.violation.vehicle.plate_number) != normalize_plate(plate_number):
            messages.error(request, 'The ticket/reference number does not match that plate number. Please check the ticket issued by the enforcer.')
            return render(request, 'payments/checkout.html', {
                'receipt': receipt,
                'form_data': form_data,
                'payment_channel': selected_channel,
                'payment_channel_label': method_group['label'],
                'payment_methods': method_group['methods'],
                'default_payment_method': method_group['methods'][0],
                'is_counter_payment': selected_channel == 'counter',
            })

        existing_payment = Payment.objects.filter(
            Q(ticket_reference=ticket_reference) | Q(ticket_number=ticket_reference.reference_number),
            status__in=('pending', 'paid'),
        ).first()
        if existing_payment:
            messages.error(request, f'This ticket reference already has a {existing_payment.get_status_display().lower()} payment record.')
            return render(request, 'payments/checkout.html', {
                'receipt': receipt,
                'form_data': form_data,
                'payment_channel': selected_channel,
                'payment_channel_label': method_group['label'],
                'payment_methods': method_group['methods'],
                'default_payment_method': method_group['methods'][0],
                'is_counter_payment': selected_channel == 'counter',
            })

        violation = ticket_reference.violation
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S%f')[:-3]
        receipt = Payment.objects.create(
            user=request.user,
            violation=violation,
            ticket_reference=ticket_reference,
            ticket_number=ticket_reference.reference_number,
            plate_number=violation.vehicle.plate_number,
            violation_type=violation.violation_type,
            payment_method=payment_method,
            amount_paid=violation.fine_amount,
            receipt_number=f'TVS-{timestamp}',
            status='pending',
        )
        if selected_channel == 'counter':
            messages.success(request, 'Cash payment slip created. Present this slip to staff and pay the fine in cash.')
        else:
            messages.success(request, 'Temporary receipt created. Your payment is pending staff verification.')

    method_group = PAYMENT_METHOD_GROUPS.get(selected_channel, PAYMENT_METHOD_GROUPS['in_app'])

    return render(request, 'payments/checkout.html', {
        'receipt': receipt,
        'form_data': form_data,
        'payment_channel': selected_channel,
        'payment_channel_label': method_group['label'],
        'payment_methods': method_group['methods'],
        'default_payment_method': method_group['methods'][0],
        'is_counter_payment': selected_channel == 'counter',
    })


@login_required
def download_receipt(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    if payment.user != request.user and not request.user.is_staff:
        return HttpResponse('Unauthorized', status=401)

    receipt_lines = [
        'Traffic Violation System Receipt',
        '================================',
        f'Receipt Number: {payment.receipt_number}',
        f'Ticket Number: {payment.ticket_number}',
        f'Plate Number: {payment.plate_number}',
        f'Violation: {payment.violation_type}',
        f'Payment Method: {payment.payment_method}',
        f'Amount Paid: PHP {payment.amount_paid}',
        f'Status: {payment.get_status_display()}',
        f'Submitted At: {payment.created_at.strftime("%Y-%m-%d %H:%M:%S")}',
        '',
        'Thank you for using the Traffic Violation System.',
    ]
    content = '\n'.join(receipt_lines)
    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="receipt-{payment.receipt_number}.txt"'
    return response


@login_required
def download_pdf_receipt(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    if payment.user != request.user and not request.user.is_staff:
        return HttpResponse('Unauthorized', status=401)

    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError:
        return HttpResponse(
            'PDF receipt generation is unavailable. Please install reportlab or download the receipt as text.',
            status=503,
        )

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=50, bottomMargin=50)
    styles = {
        'default': ParagraphStyle('default', fontName='Helvetica', fontSize=10, leading=14, textColor=colors.black),
        'title': ParagraphStyle('title', fontName='Helvetica-Bold', fontSize=18, leading=22, spaceAfter=12, textColor=colors.HexColor('#071a3d')),
        'subtitle': ParagraphStyle('subtitle', fontName='Helvetica-Bold', fontSize=12, leading=14, spaceAfter=10, textColor=colors.HexColor('#0647b8')),
        'footnote': ParagraphStyle('footnote', fontName='Helvetica', fontSize=9, leading=12, textColor=colors.grey),
    }

    elements = [
        Paragraph('Traffic Violation System', styles['title']),
        Paragraph('Official Payment Receipt', styles['subtitle']),
        Spacer(1, 12),
    ]

    table_data = [
        ['Receipt Number:', payment.receipt_number],
        ['Ticket Number:', payment.ticket_number or 'N/A'],
        ['Plate Number:', payment.plate_number or 'N/A'],
        ['Violation:', payment.violation_type or 'N/A'],
        ['Payment Method:', payment.payment_method],
        ['Amount Paid:', f'PHP {payment.amount_paid:.2f}'],
        ['Status:', payment.get_status_display()],
        ['Submitted At:', payment.created_at.strftime('%B %d, %Y %I:%M %p')],
    ]

    table = Table(table_data, colWidths=[2.4 * inch, 3.6 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#071a3d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#f7fbff')),
        ('BACKGROUND', (1, 1), (1, -1), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 1), (0, -1), colors.HexColor('#0647b8')),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 18))
    elements.append(Paragraph('Thank you for settling your traffic violation. Keep this receipt for your records.', styles['footnote']))

    doc.build(elements)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt-{payment.receipt_number}.pdf"'
    response.write(buffer.getvalue())
    buffer.close()
    return response
