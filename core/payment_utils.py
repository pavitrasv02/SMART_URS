"""Payment helpers: Razorpay, invoices, amount calculation."""

import hashlib
import hmac
import uuid
from decimal import Decimal
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

from .models import Booking, Payment, Invoice
from .provider_utils import get_booking_amount


RAZORPAY_ONLINE_MODES = {'razorpay', 'googlepay', 'phonepe', 'paytm', 'debitcard', 'creditcard', 'netbanking', 'wallet', 'emi'}


def get_razorpay_client():
    import razorpay
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def booking_has_completed_payment(booking):
    return booking.payments.filter(status='completed').exists()


def get_or_create_pending_payment(booking, amount, mode='googlepay'):
    """Get existing pending payment or create one — prevents duplicate completed payments."""
    if booking_has_completed_payment(booking):
        return None, 'Payment already completed for this booking.'

    existing = booking.payments.filter(status__in=['pending', 'processing']).order_by('-id').first()
    if existing:
        return existing, None

    payment = Payment.objects.create(
        booking=booking,
        amount=amount,
        mode=mode,
        status='pending',
    )
    return payment, None


def create_razorpay_order(payment):
    """Create Razorpay order and store order id on Payment."""
    client = get_razorpay_client()
    amount_paise = int(Decimal(str(payment.amount)) * 100)
    order = client.order.create({
        'amount': amount_paise,
        'currency': 'INR',
        'receipt': f'booking_{payment.booking_id}_pay_{payment.id}',
        'payment_capture': 1,
    })
    payment.razorpay_order_id = order['id']
    payment.status = 'processing'
    payment.save(update_fields=['razorpay_order_id', 'status', 'updated_at'])
    return order


def verify_razorpay_signature(order_id, payment_id, signature):
    """Verify Razorpay payment signature (HMAC-SHA256)."""
    message = f'{order_id}|{payment_id}'
    expected = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def complete_payment(payment, razorpay_payment_id='', razorpay_signature='', transaction_id=''):
    """Mark payment completed after verification."""
    if payment.status == 'completed':
        return payment
    payment.status = 'completed'
    payment.paid_at = timezone.now()
    if razorpay_payment_id:
        payment.razorpay_payment_id = razorpay_payment_id
    if razorpay_signature:
        payment.razorpay_signature = razorpay_signature
    if transaction_id:
        payment.transaction_id = transaction_id
    elif razorpay_payment_id:
        payment.transaction_id = razorpay_payment_id
    payment.save()
    return payment


def generate_invoice_number():
    return f'INV-{timezone.now().strftime("%Y%m")}-{uuid.uuid4().hex[:8].upper()}'


def generate_invoice_pdf(booking, payment=None):
    """Generate premium corporate invoice PDF with ReportLab; returns bytes."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch, mm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable,
    )

    amount = get_booking_amount(booking)
    subtotal = Decimal(str(amount))
    gst_rate = Decimal(str(getattr(settings, 'GST_RATE', 0.18)))
    gst_amount = (subtotal * gst_rate).quantize(Decimal('0.01'))
    grand_total = subtotal + gst_amount

    inv_num = generate_invoice_number()
    txn_id = payment.transaction_id if payment and payment.transaction_id else (
        payment.razorpay_payment_id if payment and payment.razorpay_payment_id else '—'
    )
    pay_mode = payment.get_mode_display() if payment else '—'
    pay_status = payment.get_status_display() if payment else 'Pending'
    is_paid = payment and payment.status == 'completed'
    service_name = booking.service.name if booking.service else 'Home Service'
    invoice_date = booking.booking_date or timezone.now().date()

    # Brand colors
    TEAL = colors.HexColor('#14B8A6')
    DARK = colors.HexColor('#0F172A')
    GRAY = colors.HexColor('#64748B')
    LIGHT_BG = colors.HexColor('#F8FAFC')
    BORDER = colors.HexColor('#CBD5E1')
    PAID_GREEN = colors.HexColor('#16A34A')

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='BrandTitle', fontName='Helvetica-Bold', fontSize=22,
        textColor=DARK, alignment=TA_CENTER, spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name='BrandSub', fontName='Helvetica', fontSize=9,
        textColor=GRAY, alignment=TA_CENTER, spaceAfter=0,
    ))
    styles.add(ParagraphStyle(
        name='InvLabel', fontName='Helvetica-Bold', fontSize=10,
        textColor=DARK, spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name='InvBody', fontName='Helvetica', fontSize=9,
        textColor=colors.HexColor('#334155'), leading=13,
    ))
    styles.add(ParagraphStyle(
        name='InvSection', fontName='Helvetica-Bold', fontSize=11,
        textColor=TEAL, spaceBefore=6, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name='Footer', fontName='Helvetica-Oblique', fontSize=8,
        textColor=GRAY, alignment=TA_CENTER,
    ))

    elements = []

    # ── Header band ──
    header_data = [[
        Paragraph('SMART URS', styles['BrandTitle']),
    ], [
        Paragraph('Smart Urban Residential Services', styles['BrandSub']),
    ]]
    header_tbl = Table(header_data, colWidths=[doc.width])
    header_tbl.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(header_tbl)
    elements.append(HRFlowable(width='100%', thickness=2, color=TEAL, spaceAfter=8, spaceBefore=4))
    elements.append(Paragraph('INVOICE', ParagraphStyle(
        name='InvHead', fontName='Helvetica-Bold', fontSize=16,
        textColor=DARK, alignment=TA_CENTER, spaceAfter=12,
    )))
    elements.append(HRFlowable(width='100%', thickness=1, color=BORDER, spaceAfter=14))

    # ── Invoice meta ──
    meta_rows = [
        ['Invoice #:', inv_num, 'Booking ID:', f'BKG-{booking.id:05d}'],
        ['Transaction:', txn_id, 'Date:', str(invoice_date)],
        ['Payment Method:', pay_mode, 'Status:', pay_status],
    ]
    meta_tbl = Table(meta_rows, colWidths=[80, 170, 80, 170])
    meta_tbl.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), GRAY),
        ('TEXTCOLOR', (2, 0), (2, -1), GRAY),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(meta_tbl)
    elements.append(Spacer(1, 0.15 * inch))
    elements.append(HRFlowable(width='100%', thickness=1, color=BORDER, spaceAfter=12))

    # ── Customer & Provider side-by-side ──
    customer_block = (
        f"<b>{booking.user.name}</b><br/>"
        f"{booking.user.email}<br/>"
        f"{booking.user.phone or '—'}"
    )
    if booking.provider:
        provider_block = (
            f"<b>{booking.provider.name}</b><br/>"
            f"{booking.provider.phone or '—'}<br/>"
            f"Service Provider"
        )
    else:
        provider_block = '—'

    party_tbl = Table([
        [Paragraph('Customer Details', styles['InvSection']),
         Paragraph('Provider Details', styles['InvSection'])],
        [Paragraph(customer_block, styles['InvBody']),
         Paragraph(provider_block, styles['InvBody'])],
    ], colWidths=[doc.width / 2 - 10, doc.width / 2 - 10])
    party_tbl.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, 0), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(party_tbl)
    elements.append(Spacer(1, 0.2 * inch))

    # ── Line items ──
    elements.append(Paragraph('Service Details', styles['InvSection']))
    line_rows = [
        ['Description', 'Amount (₹)'],
        [service_name, f'{subtotal:,.2f}'],
        ['GST (18%)', f'{gst_amount:,.2f}'],
    ]
    line_tbl = Table(line_rows, colWidths=[doc.width - 120, 120])
    line_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TEAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(line_tbl)
    elements.append(Spacer(1, 0.1 * inch))

    # ── Total row ──
    total_tbl = Table([
        ['TOTAL', f'₹{grand_total:,.2f}'],
    ], colWidths=[doc.width - 120, 120])
    total_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), DARK),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(total_tbl)
    elements.append(Spacer(1, 0.25 * inch))
    elements.append(HRFlowable(width='100%', thickness=1, color=BORDER, spaceAfter=12))

    # ── Payment status badge ──
    if is_paid:
        badge_style = ParagraphStyle(
            name='PaidBadge', fontName='Helvetica-Bold', fontSize=14,
            textColor=PAID_GREEN, alignment=TA_CENTER, spaceAfter=8,
        )
        elements.append(Paragraph('PAID ✓', badge_style))
    else:
        elements.append(Paragraph(
            f'STATUS: {pay_status.upper()}',
            ParagraphStyle(
                name='PendingBadge', fontName='Helvetica-Bold', fontSize=12,
                textColor=colors.HexColor('#D97706'), alignment=TA_CENTER,
            ),
        ))

    elements.append(Spacer(1, 0.3 * inch))
    elements.append(HRFlowable(width='100%', thickness=0.5, color=BORDER, spaceAfter=8))
    elements.append(Paragraph('Generated by SMART URS · www.smarturs.in', styles['Footer']))

    doc.build(elements)
    return buffer.getvalue(), inv_num, subtotal, gst_amount, grand_total


def create_invoice_for_booking(booking):
    """Create Invoice record + PDF when booking is completed."""
    if hasattr(booking, 'invoice') and booking.invoice:
        return booking.invoice

    payment = booking.payments.filter(status='completed').order_by('-paid_at').first()
    pdf_bytes, inv_num, subtotal, gst, total = generate_invoice_pdf(booking, payment)

    invoice = Invoice.objects.create(
        booking=booking,
        invoice_number=inv_num,
        payment=payment,
        subtotal=subtotal,
        gst_amount=gst,
        grand_total=total,
    )
    invoice.pdf_file.save(f'{inv_num}.pdf', ContentFile(pdf_bytes), save=True)
    return invoice
