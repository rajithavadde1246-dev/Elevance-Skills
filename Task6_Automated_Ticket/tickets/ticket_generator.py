import os
import hashlib

# ------------------------------------------------------------------
# ReportLab / Python 3.8 compatibility fix
# ------------------------------------------------------------------
# Some ReportLab versions call hashlib.md5(usedforsecurity=False).
# Python 3.8's OpenSSL implementation may not accept that argument.
# This wrapper removes only that unsupported keyword.
# ------------------------------------------------------------------

_original_md5 = hashlib.md5


def _reportlab_compatible_md5(data=b'', *args, **kwargs):
    kwargs.pop("usedforsecurity", None)
    return _original_md5(data, *args, **kwargs)


# Apply the patch only once
if not getattr(hashlib.md5, "_reportlab_compatible", False):
    _reportlab_compatible_md5._reportlab_compatible = True
    hashlib.md5 = _reportlab_compatible_md5


# ------------------------------------------------------------------
# QR Code
# ------------------------------------------------------------------

import qrcode

from django.conf import settings

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)


def generate_qr_code(booking):
    """
    Generate a QR code containing the booking information.
    """

    qr_data = (
        f"BOOKING ID: {booking.booking_id}\n"
        f"MOVIE: {booking.movie_name}\n"
        f"THEATER: {booking.theater}\n"
        f"SCREEN: {booking.screen}\n"
        f"DATE: {booking.show_date}\n"
        f"TIME: {booking.show_time}\n"
        f"SEATS: {booking.seats}\n"
        f"PAYMENT: {booking.payment_reference}"
    )

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4,
    )

    qr.add_data(qr_data)
    qr.make(fit=True)

    image = qr.make_image()

    qr_directory = os.path.join(
        settings.MEDIA_ROOT,
        "tickets",
        "qr",
    )

    os.makedirs(
        qr_directory,
        exist_ok=True,
    )

    qr_filename = (
        f"{booking.booking_id}_qr.png"
    )

    qr_path = os.path.join(
        qr_directory,
        qr_filename,
    )

    image.save(qr_path)

    return qr_path


def generate_pdf_ticket(booking):
    """
    Generate a professional PDF movie ticket
    containing booking details and QR code.
    """

    # --------------------------------------------------------------
    # Create ticket directory
    # --------------------------------------------------------------

    ticket_directory = os.path.join(
        settings.MEDIA_ROOT,
        "tickets",
    )

    os.makedirs(
        ticket_directory,
        exist_ok=True,
    )

    pdf_filename = (
        f"{booking.booking_id}.pdf"
    )

    pdf_path = os.path.join(
        ticket_directory,
        pdf_filename,
    )

    # --------------------------------------------------------------
    # Generate QR code
    # --------------------------------------------------------------

    qr_path = generate_qr_code(booking)

    # --------------------------------------------------------------
    # PDF document
    # --------------------------------------------------------------

    document = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    # --------------------------------------------------------------
    # Styles
    # --------------------------------------------------------------

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TicketTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        alignment=1,
        spaceAfter=10,
    )

    confirmed_style = ParagraphStyle(
        "Confirmed",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        alignment=1,
        spaceAfter=12,
    )

    normal_style = ParagraphStyle(
        "NormalTicket",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
    )

    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        alignment=1,
    )

    # --------------------------------------------------------------
    # Story
    # --------------------------------------------------------------

    story = []

    # --------------------------------------------------------------
    # Title
    # --------------------------------------------------------------

    story.append(
        Paragraph(
            "MOVIE BOOKING TICKET",
            title_style,
        )
    )

    story.append(
        Paragraph(
            "CONFIRMED BOOKING",
            confirmed_style,
        )
    )

    story.append(
        Spacer(1, 8)
    )

    # --------------------------------------------------------------
    # Movie / Booking Information
    # --------------------------------------------------------------

    movie_data = [
        [
            "Movie",
            str(booking.movie_name),
        ],
        [
            "Theater",
            str(booking.theater),
        ],
        [
            "Screen",
            str(booking.screen),
        ],
        [
            "Show Date",
            str(booking.show_date),
        ],
        [
            "Show Time",
            str(booking.show_time),
        ],
        [
            "Booked Seats",
            str(booking.seats),
        ],
        [
            "Booking ID",
            str(booking.booking_id),
        ],
        [
            "Payment Reference",
            str(booking.payment_reference),
        ],
        [
            "Payment Status",
            str(booking.payment_status),
        ],
    ]

    table = Table(
        movie_data,
        colWidths=[
            45 * mm,
            110 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.lightgrey,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (1, 0),
                    (1, -1),
                    "Helvetica",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    story.append(table)

    story.append(
        Spacer(1, 20)
    )

    # --------------------------------------------------------------
    # QR Code Section
    # --------------------------------------------------------------

    qr_image = Image(
        qr_path,
        width=45 * mm,
        height=45 * mm,
    )

    qr_text = Paragraph(
        "Scan this QR code for ticket verification.",
        normal_style,
    )

    qr_table = Table(
        [
            [
                qr_text,
                qr_image,
            ]
        ],
        colWidths=[
            100 * mm,
            55 * mm,
        ],
    )

    qr_table.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "ALIGN",
                    (1, 0),
                    (1, 0),
                    "CENTER",
                ),
            ]
        )
    )

    story.append(qr_table)

    story.append(
        Spacer(1, 20)
    )

    # --------------------------------------------------------------
    # Footer
    # --------------------------------------------------------------

    story.append(
        Paragraph(
            "Please carry this ticket during your visit.",
            footer_style,
        )
    )

    story.append(
        Spacer(1, 5)
    )

    story.append(
        Paragraph(
            "This ticket was generated automatically "
            "after successful payment.",
            footer_style,
        )
    )

    story.append(
        Spacer(1, 5)
    )

    story.append(
        Paragraph(
            "Movie Booking Team",
            footer_style,
        )
    )

    # --------------------------------------------------------------
    # Build PDF
    # --------------------------------------------------------------

    document.build(story)

    return pdf_path, qr_path