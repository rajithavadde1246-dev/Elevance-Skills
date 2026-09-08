from django.db import models
from django.contrib.auth.models import User


# ==========================================================
# MOVIE
# ==========================================================

class Movie(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


# ==========================================================
# THEATER
# ==========================================================

class Theater(models.Model):
    name = models.CharField(max_length=150)

    total_seats = models.PositiveIntegerField(
        default=100
    )

    def __str__(self):
        return self.name


# ==========================================================
# BOOKING
# ==========================================================

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
        related_name="dashboard_bookings"
    )

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    theater = models.ForeignKey(
        Theater,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    seats_booked = models.PositiveIntegerField(
        default=1
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
        db_index=True
    )

    booked_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["status", "booked_at"]
            ),
            models.Index(
                fields=["theater", "status"]
            ),
            models.Index(
                fields=["movie", "status"]
            ),
        ]

    def __str__(self):
        return f"Booking #{self.id}"


# ==========================================================
# REFUND
# ==========================================================

class Refund(models.Model):

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (COMPLETED, "Completed"),
        (FAILED, "Failed"),
    ]

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name="refund"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
        db_index=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["status", "created_at"]
            ),
        ]

    def __str__(self):
        return f"Refund for Booking #{self.booking.id}"