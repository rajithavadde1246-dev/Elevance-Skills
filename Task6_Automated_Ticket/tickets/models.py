from django.db import models
from django.contrib.auth.models import User


class Booking(models.Model):

    PAYMENT_STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    booking_id = models.CharField(
        max_length=100,
        unique=True
    )

    movie_name = models.CharField(
        max_length=200
    )

    theater = models.CharField(
        max_length=200
    )

    screen = models.CharField(
        max_length=100
    )

    show_date = models.DateField()

    show_time = models.TimeField()

    seats = models.CharField(
        max_length=200
    )

    payment_reference = models.CharField(
        max_length=200
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='SUCCESS'
    )

    ticket_pdf = models.FileField(
        upload_to='tickets/',
        blank=True,
        null=True
    )

    qr_code = models.ImageField(
        upload_to='tickets/qr/',
        blank=True,
        null=True
    )

    email_sent = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.booking_id
