"""
Generate sample invoices for testing the Invoice Processing Human-in-the-Loop demo.

Produces:
  1. Clean digital PDFs (different vendors/layouts)
  2. Scanned-looking documents (noise, skew, shadows)
  3. Low-resolution / degraded documents
  4. Documents with extraneous content (marketing, T&C, stamps)
"""

import os
import random
import math
from io import BytesIO

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas as pdfcanvas

from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageEnhance

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "sample-invoices")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Invoice data sets — each dict is a different vendor / format
# ---------------------------------------------------------------------------

INVOICES = [
    {
        "id": "INV-2025-0042",
        "vendor": "Acme Office Supplies Co.",
        "vendor_address": "123 Industrial Blvd, Suite 400\nAustin, TX 78701",
        "vendor_phone": "(512) 555-0198",
        "vendor_email": "billing@acmeoffice.com",
        "bill_to": "TechStart Inc.\n456 Innovation Dr\nSan Francisco, CA 94107",
        "date": "2025-04-15",
        "due_date": "2025-05-15",
        "po_number": "PO-7891",
        "items": [
            ("Ergonomic Office Chair", 2, 349.99),
            ("Standing Desk 60x30", 3, 599.00),
            ("Monitor Arm Dual Mount", 5, 89.95),
            ("Cable Management Kit", 10, 24.99),
        ],
        "tax_rate": 0.0825,
        "notes": "Net 30. Late payments subject to 1.5% monthly interest.",
        "currency": "USD",
    },
    {
        "id": "2025/UK/00317",
        "vendor": "British Cloud Services Ltd",
        "vendor_address": "14 Kensington High Street\nLondon W8 4PT, United Kingdom",
        "vendor_phone": "+44 20 7946 0958",
        "vendor_email": "accounts@britishcloud.co.uk",
        "bill_to": "GlobalTech GmbH\nFriedrichstr. 112\n10117 Berlin, Germany",
        "date": "12 March 2025",
        "due_date": "12 April 2025",
        "po_number": None,
        "items": [
            ("Cloud Hosting - Pro Plan (Annual)", 1, 4800.00),
            ("Managed Database Service (12 mo)", 1, 2400.00),
            ("SSL Certificate - Wildcard", 3, 150.00),
            ("DDoS Protection Add-on", 1, 600.00),
            ("24/7 Priority Support", 1, 1200.00),
        ],
        "tax_rate": 0.20,
        "notes": "VAT Registration: GB 123 4567 89\nPayment via BACS transfer preferred.",
        "currency": "GBP",
    },
    {
        "id": "FAC-00891",
        "vendor": "Martinez & Hijos Construcción S.A.",
        "vendor_address": "Av. Reforma 505, Piso 12\nCol. Cuauhtémoc, CDMX 06500\nMéxico",
        "vendor_phone": "+52 55 5123 4567",
        "vendor_email": "facturas@martinezconstruccion.mx",
        "bill_to": "Desarrollos Modernos SA de CV\nBlvd. Manuel Ávila Camacho 40\nLomas de Chapultepec, CDMX",
        "date": "28/02/2025",
        "due_date": "30/03/2025",
        "po_number": "OC-2025-0044",
        "items": [
            ("Cemento Portland 50kg (pallet)", 20, 185.00),
            ("Varilla corrugada 3/8\" (ton)", 5, 12500.00),
            ("Arena sílica m³", 15, 350.00),
            ("Servicio de transporte", 1, 8500.00),
        ],
        "tax_rate": 0.16,
        "notes": "RFC: MCO-850101-XY9\nPago a 30 días. Factura fiscal incluida.",
        "currency": "MXN",
    },
    {
        "id": "INV-9920",
        "vendor": "Sakura Electronics Japan",
        "vendor_address": "2-3-1 Nishi-Shinjuku\nShinjuku-ku, Tokyo 163-0001\nJapan",
        "vendor_phone": "+81 3-1234-5678",
        "vendor_email": "invoice@sakura-elec.jp",
        "bill_to": "Pacific Rim Trading Co.\n88 Market Street, Floor 22\nSingapore 048948",
        "date": "2025-01-20",
        "due_date": "2025-02-20",
        "po_number": "SGP-PO-2025-112",
        "items": [
            ("PCB Assembly Unit Type-A", 500, 12.50),
            ("PCB Assembly Unit Type-B", 300, 18.75),
            ("LED Display Module 5\"", 200, 45.00),
            ("Custom Connector Set XR-7", 1000, 3.25),
            ("Quality Inspection Fee", 1, 500.00),
            ("Freight (Air - Tokyo to SG)", 1, 2200.00),
        ],
        "tax_rate": 0.10,
        "notes": "Consumption Tax (10%) included.\nBank: Mizuho Bank, Shinjuku Branch\nAccount: 1234567",
        "currency": "JPY",
    },
    {
        "id": "REC-2025-0003",
        "vendor": "Sunny Side Café & Catering",
        "vendor_address": "78 Main Street\nPortland, OR 97201",
        "vendor_phone": "(503) 555-0147",
        "vendor_email": None,
        "bill_to": "WeWork - Pioneer Square\n720 SW Washington St\nPortland, OR 97205",
        "date": "April 3, 2025",
        "due_date": "Upon Receipt",
        "po_number": None,
        "items": [
            ("Corporate Lunch Platter (serves 20)", 2, 189.00),
            ("Beverage Station Setup", 1, 75.00),
            ("Dessert Assortment Box", 3, 45.00),
            ("Delivery & Setup Fee", 1, 50.00),
        ],
        "tax_rate": 0.0,
        "notes": "Thank you for your business! Tips appreciated.",
        "currency": "USD",
    },
    {
        "id": "LS-INV-20250222",
        "vendor": "LegalShield Professional Services",
        "vendor_address": "One Liberty Plaza, 45th Floor\nNew York, NY 10006",
        "vendor_phone": "(212) 555-0321",
        "vendor_email": "billing@legalshield.example.com",
        "bill_to": "Horizon Ventures LLC\n1200 Brickell Ave, Suite 900\nMiami, FL 33131",
        "date": "2025-02-22",
        "due_date": "2025-03-22",
        "po_number": "HV-LEGAL-0091",
        "items": [
            ("Contract Review - Series A Financing", 1, 7500.00),
            ("IP Due Diligence (40 hrs @ $450/hr)", 1, 18000.00),
            ("Regulatory Filing Preparation", 1, 3200.00),
            ("Travel Expenses (Miami trip)", 1, 1850.00),
        ],
        "tax_rate": 0.08875,
        "notes": "Payment terms: Net 30\nMatter Reference: HV-2025-SeriesA",
        "currency": "USD",
    },
]

EXTRANEOUS_PARAGRAPHS = [
    "IMPORTANT: By accepting this invoice you agree to our terms and conditions. "
    "All disputes shall be resolved through binding arbitration in the state of "
    "Delaware. The prevailing party shall be entitled to recover reasonable "
    "attorney's fees. This invoice is confidential and intended solely for the "
    "named recipient.",
    "*** SPECIAL OFFER *** Refer a friend and receive 15% off your next order! "
    "Visit our website at www.example-promo.com/refer for details. "
    "Offer valid through December 31, 2025. Cannot be combined with other promotions.",
    "Our company is ISO 9001:2015 certified and committed to delivering the highest "
    "quality products and services. We have been serving satisfied customers since 1987. "
    "For feedback or concerns, please contact our customer satisfaction team at "
    "feedback@example.com or call 1-800-555-0199.",
    "REMITTANCE ADVICE: Please detach this portion and return with your payment. "
    "Make checks payable to the vendor name listed above. Include the invoice number "
    "on your check memo line. For wire transfer instructions, contact our accounts "
    "receivable department.",
]


def _currency_symbol(code):
    return {"USD": "$", "GBP": "£", "MXN": "$", "JPY": "¥"}.get(code, "$")


# ---------------------------------------------------------------------------
# 1. Clean digital PDF
# ---------------------------------------------------------------------------

def generate_clean_pdf(inv, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                            topMargin=0.6 * inch, bottomMargin=0.6 * inch)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle("InvTitle", parent=styles["Heading1"],
                                  fontSize=22, spaceAfter=6, textColor=colors.HexColor("#1a1a2e"))
    subtitle_style = ParagraphStyle("InvSub", parent=styles["Normal"],
                                     fontSize=10, textColor=colors.grey)
    normal = styles["Normal"]
    bold_style = ParagraphStyle("Bold", parent=normal, fontName="Helvetica-Bold")

    story.append(Paragraph(f"INVOICE", title_style))
    story.append(Paragraph(f"#{inv['id']}", subtitle_style))
    story.append(Spacer(1, 12))

    vendor_info = inv["vendor"] + "<br/>" + inv["vendor_address"].replace("\n", "<br/>")
    if inv.get("vendor_phone"):
        vendor_info += f"<br/>Phone: {inv['vendor_phone']}"
    if inv.get("vendor_email"):
        vendor_info += f"<br/>Email: {inv['vendor_email']}"
    bill_to_info = "<b>Bill To:</b><br/>" + inv["bill_to"].replace("\n", "<br/>")

    header_data = [[Paragraph(vendor_info, normal), Paragraph(bill_to_info, normal)]]
    header_table = Table(header_data, colWidths=[3.5 * inch, 3.5 * inch])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 12))

    meta_lines = [f"<b>Date:</b> {inv['date']}",
                  f"<b>Due Date:</b> {inv['due_date']}"]
    if inv.get("po_number"):
        meta_lines.append(f"<b>PO Number:</b> {inv['po_number']}")
    meta_lines.append(f"<b>Currency:</b> {inv['currency']}")
    for line in meta_lines:
        story.append(Paragraph(line, normal))
    story.append(Spacer(1, 16))

    sym = _currency_symbol(inv["currency"])
    table_data = [["#", "Description", "Qty", "Unit Price", "Amount"]]
    subtotal = 0.0
    for i, (desc, qty, price) in enumerate(inv["items"], 1):
        amt = qty * price
        subtotal += amt
        table_data.append([str(i), desc, str(qty), f"{sym}{price:,.2f}", f"{sym}{amt:,.2f}"])

    tax_amount = subtotal * inv["tax_rate"]
    total = subtotal + tax_amount

    table_data.append(["", "", "", "Subtotal", f"{sym}{subtotal:,.2f}"])
    tax_label = f"Tax ({inv['tax_rate']*100:.2f}%)" if inv["tax_rate"] > 0 else "Tax"
    table_data.append(["", "", "", tax_label, f"{sym}{tax_amount:,.2f}"])
    table_data.append(["", "", "", "TOTAL", f"{sym}{total:,.2f}"])

    col_widths = [0.4 * inch, 3.2 * inch, 0.6 * inch, 1.2 * inch, 1.2 * inch]
    t = Table(table_data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -len(["sub", "tax", "total"]) - 1), 0.5, colors.HexColor("#cccccc")),
        ("LINEABOVE", (3, -3), (-1, -3), 1, colors.HexColor("#cccccc")),
        ("FONTNAME", (3, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (3, -1), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))

    if inv.get("notes"):
        story.append(Paragraph("<b>Notes:</b>", bold_style))
        for line in inv["notes"].split("\n"):
            story.append(Paragraph(line, normal))

    doc.build(story)
    with open(path, "wb") as f:
        f.write(buf.getvalue())
    return path


# ---------------------------------------------------------------------------
# 2. Alternate layout — minimal / receipt-style
# ---------------------------------------------------------------------------

def generate_minimal_pdf(inv, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    c = pdfcanvas.Canvas(path, pagesize=letter)
    w, h = letter
    y = h - 50

    c.setFont("Helvetica-Bold", 28)
    c.drawString(50, y, inv["vendor"])
    y -= 30
    c.setFont("Helvetica", 9)
    for line in inv["vendor_address"].split("\n"):
        c.drawString(50, y, line)
        y -= 13

    y -= 10
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, f"Invoice {inv['id']}")
    c.setFont("Helvetica", 10)
    c.drawRightString(w - 50, y, f"Date: {inv['date']}")
    y -= 16
    c.drawRightString(w - 50, y, f"Due: {inv['due_date']}")
    y -= 25

    c.setFont("Helvetica", 9)
    c.drawString(50, y, "Bill To:")
    y -= 13
    for line in inv["bill_to"].split("\n"):
        c.drawString(50, y, line)
        y -= 13
    y -= 15

    c.setStrokeColor(colors.HexColor("#888888"))
    c.line(50, y, w - 50, y)
    y -= 18

    sym = _currency_symbol(inv["currency"])
    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, y, "Description")
    c.drawRightString(350, y, "Qty")
    c.drawRightString(440, y, "Price")
    c.drawRightString(w - 50, y, "Amount")
    y -= 5
    c.line(50, y, w - 50, y)
    y -= 15

    c.setFont("Helvetica", 9)
    subtotal = 0.0
    for desc, qty, price in inv["items"]:
        amt = qty * price
        subtotal += amt
        c.drawString(50, y, desc[:50])
        c.drawRightString(350, y, str(qty))
        c.drawRightString(440, y, f"{sym}{price:,.2f}")
        c.drawRightString(w - 50, y, f"{sym}{amt:,.2f}")
        y -= 16

    y -= 5
    c.line(350, y, w - 50, y)
    y -= 16
    tax = subtotal * inv["tax_rate"]
    total = subtotal + tax
    c.drawRightString(440, y, "Subtotal:")
    c.drawRightString(w - 50, y, f"{sym}{subtotal:,.2f}")
    y -= 14
    c.drawRightString(440, y, f"Tax ({inv['tax_rate']*100:.1f}%):")
    c.drawRightString(w - 50, y, f"{sym}{tax:,.2f}")
    y -= 14
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(440, y, "Total:")
    c.drawRightString(w - 50, y, f"{sym}{total:,.2f}")

    if inv.get("notes"):
        y -= 40
        c.setFont("Helvetica", 8)
        for line in inv["notes"].split("\n"):
            c.drawString(50, y, line)
            y -= 12

    c.save()
    return path


# ---------------------------------------------------------------------------
# 3. PDF with extraneous content
# ---------------------------------------------------------------------------

def generate_noisy_content_pdf(inv, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=0.6 * inch, rightMargin=0.6 * inch,
                            topMargin=0.5 * inch, bottomMargin=0.5 * inch)
    styles = getSampleStyleSheet()
    story = []
    normal = styles["Normal"]
    small = ParagraphStyle("Small", parent=normal, fontSize=7, textColor=colors.HexColor("#666666"))

    random.shuffle(EXTRANEOUS_PARAGRAPHS)
    story.append(Paragraph(EXTRANEOUS_PARAGRAPHS[0], small))
    story.append(Spacer(1, 8))

    story.append(Paragraph(f"<b>{inv['vendor']}</b>", styles["Heading2"]))
    story.append(Paragraph(inv["vendor_address"].replace("\n", ", "), normal))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"Invoice: {inv['id']}  |  Date: {inv['date']}  |  Due: {inv['due_date']}", normal))
    if inv.get("po_number"):
        story.append(Paragraph(f"PO: {inv['po_number']}", normal))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"<b>To:</b> {inv['bill_to'].replace(chr(10), ', ')}", normal))
    story.append(Spacer(1, 10))

    story.append(Paragraph(EXTRANEOUS_PARAGRAPHS[1], small))
    story.append(Spacer(1, 10))

    sym = _currency_symbol(inv["currency"])
    table_data = [["Item", "Qty", "Rate", "Total"]]
    subtotal = 0.0
    for desc, qty, price in inv["items"]:
        amt = qty * price
        subtotal += amt
        table_data.append([desc, str(qty), f"{sym}{price:,.2f}", f"{sym}{amt:,.2f}"])
    tax = subtotal * inv["tax_rate"]
    total = subtotal + tax
    table_data.append(["", "", "Subtotal", f"{sym}{subtotal:,.2f}"])
    table_data.append(["", "", f"Tax ({inv['tax_rate']*100:.1f}%)", f"{sym}{tax:,.2f}"])
    table_data.append(["", "", "TOTAL DUE", f"{sym}{total:,.2f}"])

    t = Table(table_data, colWidths=[3 * inch, 0.8 * inch, 1.3 * inch, 1.3 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#444444")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -4), 0.3, colors.HexColor("#aaaaaa")),
        ("FONTNAME", (-2, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))

    if inv.get("notes"):
        story.append(Paragraph(f"<i>{inv['notes'].replace(chr(10), '<br/>')}</i>", normal))
        story.append(Spacer(1, 10))

    story.append(Paragraph(EXTRANEOUS_PARAGRAPHS[2], small))
    story.append(Spacer(1, 6))
    story.append(Paragraph(EXTRANEOUS_PARAGRAPHS[3], small))

    doc.build(story)
    with open(path, "wb") as f:
        f.write(buf.getvalue())
    return path


# ---------------------------------------------------------------------------
# Image degradation helpers
# ---------------------------------------------------------------------------

def pdf_to_image(pdf_path, dpi=200):
    """Render the first page of a PDF to a PIL Image using reportlab + simple approach."""
    from reportlab.graphics import renderPM
    img = Image.open(pdf_path) if pdf_path.endswith((".png", ".jpg")) else None
    if img:
        return img
    # Fallback: use a simple pixel-based rasterization workaround
    # Since we don't have pdf2image/poppler, we'll generate the invoice
    # directly as an image instead.
    return None


def _render_invoice_as_image(inv, width=1700, height=2200):
    """Render an invoice directly as a PIL Image for degradation."""
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
        font_med = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
        font_tiny = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
    except (OSError, IOError):
        font_large = ImageFont.load_default()
        font_med = font_large
        font_small = font_large
        font_tiny = font_large

    y = 60
    draw.text((60, y), inv["vendor"], fill="black", font=font_large)
    y += 50
    for line in inv["vendor_address"].split("\n"):
        draw.text((60, y), line, fill="#444444", font=font_small)
        y += 24

    y += 20
    draw.text((60, y), f"INVOICE  {inv['id']}", fill="#1a1a2e", font=font_med)
    draw.text((width - 450, y), f"Date: {inv['date']}", fill="black", font=font_small)
    y += 30
    draw.text((width - 450, y), f"Due: {inv['due_date']}", fill="black", font=font_small)
    y += 40

    draw.text((60, y), "Bill To:", fill="black", font=font_med)
    y += 32
    for line in inv["bill_to"].split("\n"):
        draw.text((60, y), line, fill="#333333", font=font_small)
        y += 24
    y += 30

    draw.line([(60, y), (width - 60, y)], fill="#999999", width=2)
    y += 15

    sym = _currency_symbol(inv["currency"])
    headers = ["Description", "Qty", "Unit Price", "Amount"]
    x_positions = [60, 900, 1100, 1400]
    draw.rectangle([(55, y - 5), (width - 55, y + 30)], fill="#1a1a2e")
    for hdr, xp in zip(headers, x_positions):
        draw.text((xp, y), hdr, fill="white", font=font_small)
    y += 38

    subtotal = 0.0
    for desc, qty, price in inv["items"]:
        amt = qty * price
        subtotal += amt
        draw.text((60, y), desc[:45], fill="black", font=font_small)
        draw.text((920, y), str(qty), fill="black", font=font_small)
        draw.text((1100, y), f"{sym}{price:,.2f}", fill="black", font=font_small)
        draw.text((1400, y), f"{sym}{amt:,.2f}", fill="black", font=font_small)
        y += 30
        draw.line([(60, y - 4), (width - 60, y - 4)], fill="#dddddd", width=1)

    y += 15
    tax = subtotal * inv["tax_rate"]
    total = subtotal + tax
    draw.text((1100, y), "Subtotal:", fill="black", font=font_small)
    draw.text((1400, y), f"{sym}{subtotal:,.2f}", fill="black", font=font_small)
    y += 28
    draw.text((1100, y), f"Tax ({inv['tax_rate']*100:.1f}%):", fill="black", font=font_small)
    draw.text((1400, y), f"{sym}{tax:,.2f}", fill="black", font=font_small)
    y += 28
    draw.text((1100, y), "TOTAL:", fill="black", font=font_med)
    draw.text((1400, y), f"{sym}{total:,.2f}", fill="#1a1a2e", font=font_med)

    if inv.get("notes"):
        y += 60
        draw.text((60, y), "Notes:", fill="black", font=font_med)
        y += 30
        for line in inv["notes"].split("\n"):
            draw.text((60, y), line, fill="#555555", font=font_tiny)
            y += 20

    return img


def apply_scan_effect(img):
    """Simulate a scanned document: slight rotation, noise, contrast shift, edges."""
    angle = random.uniform(-2.5, 2.5)
    img = img.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=(245, 242, 235))
    img = img.filter(ImageFilter.GaussianBlur(radius=0.7))

    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(random.uniform(0.75, 0.9))

    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(random.uniform(0.88, 0.95))

    noise = Image.effect_noise(img.size, 25)
    noise = noise.convert("RGB")
    img = Image.blend(img, noise, alpha=0.06)

    draw = ImageDraw.Draw(img)
    w, h = img.size
    shadow_w = random.randint(15, 40)
    for i in range(shadow_w):
        alpha = int(30 * (1 - i / shadow_w))
        draw.line([(w - shadow_w + i, 0), (w - shadow_w + i, h)],
                  fill=(alpha, alpha, alpha), width=1)
    for i in range(shadow_w):
        alpha = int(25 * (1 - i / shadow_w))
        draw.line([(0, h - shadow_w + i), (w, h - shadow_w + i)],
                  fill=(alpha, alpha, alpha), width=1)

    return img


def apply_low_resolution(img, target_width=600):
    """Drastically reduce resolution and add heavy noise/blur."""
    ratio = target_width / img.width
    small_size = (target_width, int(img.height * ratio))
    img = img.resize(small_size, Image.BILINEAR)
    img = img.filter(ImageFilter.GaussianBlur(radius=1.2))

    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(0.7)
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(0.5)

    noise = Image.effect_noise(img.size, 40)
    noise = noise.convert("RGB")
    img = Image.blend(img, noise, alpha=0.12)

    img = img.resize((int(img.width * 1.8), int(img.height * 1.8)), Image.BILINEAR)

    return img


def image_to_pdf(img, pdf_path, jpeg_quality=85):
    """Wrap a PIL Image inside a single-page PDF (simulating a scanned PDF)."""
    img_buf = BytesIO()
    rgb_img = img.convert("RGB")
    rgb_img.save(img_buf, format="JPEG", quality=jpeg_quality)
    img_buf.seek(0)

    from reportlab.lib.utils import ImageReader
    img_w, img_h = img.size
    page_w = 8.5 * inch
    scale = page_w / img_w
    page_h = img_h * scale

    c = pdfcanvas.Canvas(pdf_path, pagesize=(page_w, page_h))
    c.drawImage(ImageReader(img_buf), 0, 0, width=page_w, height=page_h)
    c.save()
    return pdf_path


def add_stamp_and_handwriting(img):
    """Add a fake 'RECEIVED' stamp and some handwritten-style scribbles."""
    draw = ImageDraw.Draw(img)
    w, h = img.size

    try:
        stamp_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 72)
    except (OSError, IOError):
        stamp_font = ImageFont.load_default()

    stamp_img = Image.new("RGBA", (420, 120), (255, 255, 255, 0))
    stamp_draw = ImageDraw.Draw(stamp_img)
    stamp_draw.rectangle([(5, 5), (415, 115)], outline=(200, 30, 30, 180), width=4)
    stamp_draw.text((20, 18), "RECEIVED", fill=(200, 30, 30, 160), font=stamp_font)
    stamp_img = stamp_img.rotate(random.uniform(-18, -8), expand=True,
                                  fillcolor=(255, 255, 255, 0))
    stamp_x = random.randint(int(w * 0.5), int(w * 0.7))
    stamp_y = random.randint(int(h * 0.05), int(h * 0.2))
    img.paste(stamp_img, (stamp_x, stamp_y), stamp_img)

    draw = ImageDraw.Draw(img)
    try:
        hw_font = ImageFont.truetype("/System/Library/Fonts/Noteworthy.ttc", 28)
    except (OSError, IOError):
        hw_font = ImageFont.load_default()

    notes = ["OK - checked 4/20", "Acct# 4471", "→ Approved JM"]
    note = random.choice(notes)
    nx = random.randint(int(w * 0.55), int(w * 0.75))
    ny = random.randint(int(h * 0.75), int(h * 0.85))
    draw.text((nx, ny), note, fill=(30, 30, 180), font=hw_font)

    return img


# ---------------------------------------------------------------------------
# Main generation
# ---------------------------------------------------------------------------

def main():
    generated = []

    # --- Clean digital PDFs (3 invoices) ---
    p = generate_clean_pdf(INVOICES[0], "01_clean_acme_office.pdf")
    generated.append(("Clean digital PDF", p))

    p = generate_clean_pdf(INVOICES[1], "02_clean_british_cloud.pdf")
    generated.append(("Clean digital PDF", p))

    p = generate_minimal_pdf(INVOICES[4], "03_clean_minimal_cafe.pdf")
    generated.append(("Clean minimal PDF", p))

    # --- PDF with extraneous content (2 invoices) ---
    p = generate_noisy_content_pdf(INVOICES[5], "04_extraneous_legalshield.pdf")
    generated.append(("PDF with extraneous content", p))

    p = generate_noisy_content_pdf(INVOICES[2], "05_extraneous_martinez.pdf")
    generated.append(("PDF with extraneous content", p))

    # --- Scanned document PDFs (2 invoices — image embedded in PDF) ---
    img = _render_invoice_as_image(INVOICES[3])
    img = apply_scan_effect(img)
    img = add_stamp_and_handwriting(img)
    scan_path = os.path.join(OUTPUT_DIR, "06_scanned_sakura_electronics.pdf")
    image_to_pdf(img, scan_path, jpeg_quality=80)
    generated.append(("Scanned PDF (with stamp)", scan_path))

    img = _render_invoice_as_image(INVOICES[2])
    img = apply_scan_effect(img)
    scan_path = os.path.join(OUTPUT_DIR, "07_scanned_martinez.pdf")
    image_to_pdf(img, scan_path, jpeg_quality=72)
    generated.append(("Scanned PDF", scan_path))

    # --- Low-resolution degraded PDFs (2 invoices — low-res image in PDF) ---
    img = _render_invoice_as_image(INVOICES[0])
    img = apply_low_resolution(img, target_width=500)
    lo_path = os.path.join(OUTPUT_DIR, "08_lowres_acme_office.pdf")
    image_to_pdf(img, lo_path, jpeg_quality=60)
    generated.append(("Low-resolution PDF", lo_path))

    img = _render_invoice_as_image(INVOICES[5])
    img = apply_scan_effect(img)
    img = apply_low_resolution(img, target_width=550)
    lo_path = os.path.join(OUTPUT_DIR, "09_lowres_scanned_legalshield.pdf")
    image_to_pdf(img, lo_path, jpeg_quality=45)
    generated.append(("Low-res scanned PDF", lo_path))

    # --- Scanned with stamp + handwriting (PDF) ---
    img = _render_invoice_as_image(INVOICES[1])
    img = apply_scan_effect(img)
    img = add_stamp_and_handwriting(img)
    path = os.path.join(OUTPUT_DIR, "10_scanned_stamped_british_cloud.pdf")
    image_to_pdf(img, path, jpeg_quality=75)
    generated.append(("Scanned + stamp PDF", path))

    print("\n=== Generated Sample Invoices ===\n")
    for desc, filepath in generated:
        print(f"  [{desc}] {os.path.basename(filepath)}")
    print(f"\nTotal: {len(generated)} files in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
