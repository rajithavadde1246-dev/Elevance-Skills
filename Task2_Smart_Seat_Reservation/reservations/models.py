from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class MovieShow(models.Model):
    movie_name = models.CharField(max_length=150)
    theater_name = models.CharField(max_length=150)
    show_time = models.DateTimeField()

    def __str__(self):
        return (
            f"{self.movie_name} - {self.theater_name} - "
            f"{self.show_time:%d %b %Y %I:%M %p}"
        )


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
        related_name="show_seats",
    )

    seat = models.ForeignKey(
        Seat,
        on_delete=models.CASCADE,
        related_name="show_seats",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=AVAILABLE,
    )

    reserved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reserved_seats",
    )

    reserved_until = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["show", "seat"],
                name="unique_seat_for_show",
            )
        ]

    def is_temporary_reservation_expired(self):
        if self.status != self.RESERVED:
            return False

        if not self.reserved_until:
            return True

        return timezone.now() >= self.reserved_until

    def make_available_if_expired(self):
        if self.is_temporary_reservation_expired():
            self.status = self.AVAILABLE
            self.reserved_by = None
            self.reserved_until = None

            self.save(
                update_fields=[
                    "status",
                    "reserved_by",
                    "reserved_until",
                ]
            )

    def reserve_for_user(self, user):
        self.status = self.RESERVED
        self.reserved_by = user
        self.reserved_until = timezone.now() + timedelta(minutes=2)

    def book(self):
        self.status = self.BOOKED
        self.reserved_until = None

    def __str__(self):
        return f"{self.show} - Seat {self.seat.seat_number}"


class Booking(models.Model):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (CONFIRMED, "Confirmed"),
        (CANCELLED, "Cancelled"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="seat_bookings",
    )

    show = models.ForeignKey(
        MovieShow,
        on_delete=models.CASCADE,
        related_name="bookings",
    )

    seats = models.ManyToManyField(
        ShowSeat,
        related_name="bookings",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=CONFIRMED,
    )

    booked_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return (
            f"Booking #{self.id} - "
            f"{self.user.username} - "
            f"{self.show.movie_name}"
        )