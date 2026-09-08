from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class MovieShow(models.Model):
    movie_name = models.CharField(max_length=150)
    theater_name = models.CharField(max_length=150)
    show_time = models.DateTimeField()

    def __str__(self):
        return f"{self.movie_name} - {self.theater_name}"


class Seat(models.Model):
    seat_number = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.seat_number


class ShowSeat(models.Model):
    AVAILABLE = "available"
    RESERVED = "reserved"
    BOOKED = "booked"

    STATUS_CHOICES = [
        (AVAILABLE, "Available"),
        (RESERVED, "Reserved"),
        (BOOKED, "Booked"),
    ]

    show = models.ForeignKey(
        MovieShow,
        on_delete=models.CASCADE,
        related_name="show_seats"
    )

    seat = models.ForeignKey(
        Seat,
        on_delete=models.CASCADE,
        related_name="show_seats"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=AVAILABLE
    )

    reserved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reserved_show_seats"
    )

    reserved_until = models.DateTimeField(
        null=True,
        blank=True
    )

    def is_reservation_expired(self):
        return (
            self.status == self.RESERVED
            and (
                self.reserved_until is None
                or timezone.now() >= self.reserved_until
            )
        )

    def release_if_expired(self):
        if self.is_reservation_expired():
            self.status = self.AVAILABLE
            self.reserved_by = None
            self.reserved_until = None

            self.save(
                update_fields=[
                    "status",
                    "reserved_by",
                    "reserved_until"
                ]
            )

    def reserve(self, user):
        self.status = self.RESERVED
        self.reserved_by = user
        self.reserved_until = timezone.now() + timedelta(minutes=2)

    def book(self):
        self.status = self.BOOKED
        self.reserved_until = None

    def __str__(self):
        return f"{self.show} - {self.seat.seat_number}"


class Booking(models.Model):

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (CONFIRMED, "Confirmed"),
        (CANCELLED, "Cancelled"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    show = models.ForeignKey(
        MovieShow,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    seats = models.ManyToManyField(
        ShowSeat,
        related_name="bookings"
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING
    )

    booked_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Booking #{self.id} - {self.user.username}"


class Payment(models.Model):

    CREATED = "created"
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (CREATED, "Created"),
        (PENDING, "Pending"),
        (SUCCESS, "Success"),
        (FAILED, "Failed"),
        (CANCELLED, "Cancelled"),
    ]

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    razorpay_order_id = models.CharField(
        max_length=100,
        unique=True
    )

    razorpay_payment_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    razorpay_signature = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=CREATED
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"Payment #{self.id} - {self.status}"