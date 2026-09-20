import os

from celery import shared_task
from django.core.mail import EmailMessage
from django.conf import settings

from .models import Booking
from .ticket_generator import generate_pdf_ticket


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30
)
def generate_and_send_ticket(self, booking_id):

    try:

        booking = Booking.objects.get(
            id=booking_id
        )

        # Generate PDF and QR
        pdf_path, qr_path = generate_pdf_ticket(
            booking
        )

        # Save generated files
        with open(pdf_path, 'rb') as pdf_file:

            booking.ticket_pdf.save(
                os.path.basename(pdf_path),
                pdf_file,
                save=False
            )

        with open(qr_path, 'rb') as qr_file:

            booking.qr_code.save(
                os.path.basename(qr_path),
                qr_file,
                save=False
            )

        booking.save()

        # Email subject
        subject = (
            f"Movie Ticket Confirmation - "
            f"{booking.booking_id}"
        )

        # Email body
        message = f"""
Hello {booking.user.username},

Your movie booking has been confirmed successfully.

Movie: {booking.movie_name}
Theater: {booking.theater}
Screen: {booking.screen}
Date: {booking.show_date}
Time: {booking.show_time}
Seats: {booking.seats}

Booking ID: {booking.booking_id}

Payment Reference:
{booking.payment_reference}

Please find your movie ticket attached to this email.

Thank you for booking with us.

Movie Booking Team
"""

        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[booking.user.email],
        )

        # Attach PDF
        with open(pdf_path, 'rb') as pdf_file:

            email.attach(
                os.path.basename(pdf_path),
                pdf_file.read(),
                'application/pdf'
            )

        # Send email
        email.send(
            fail_silently=False
        )

        booking.email_sent = True

        booking.save(
            update_fields=['email_sent']
        )

        return (
            f"Ticket generated and email sent "
            f"for {booking.booking_id}"
        )

    except Exception as exc:

        # Automatically retry failed email/task
        raise self.retry(
            exc=exc
        )