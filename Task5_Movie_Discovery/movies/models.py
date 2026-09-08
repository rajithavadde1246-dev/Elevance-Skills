from django.db import models
from django.contrib.auth.models import User


class Genre(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True
    )

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True
    )

    def __str__(self):
        return self.name


class Theater(models.Model):
    name = models.CharField(
        max_length=150
    )

    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name="theaters"
    )

    def __str__(self):
        return self.name


class Movie(models.Model):
    LANGUAGE_CHOICES = [
        ("Telugu", "Telugu"),
        ("Hindi", "Hindi"),
        ("Tamil", "Tamil"),
        ("Kannada", "Kannada"),
        ("English", "English"),
    ]

    title = models.CharField(
        max_length=200,
        db_index=True
    )

    genre = models.ForeignKey(
        Genre,
        on_delete=models.CASCADE,
        related_name="movies"
    )

    language = models.CharField(
        max_length=50,
        choices=LANGUAGE_CHOICES,
        db_index=True
    )

    release_date = models.DateField(
        db_index=True
    )

    rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=0
    )

    ticket_price = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )

    popularity = models.PositiveIntegerField(
        default=0,
        db_index=True
    )

    theaters = models.ManyToManyField(
        Theater,
        related_name="movies"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["title", "language"]
            ),
            models.Index(
                fields=["release_date", "rating"]
            ),
            models.Index(
                fields=["popularity"]
            ),
        ]

    def __str__(self):
        return self.title


class Show(models.Model):
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="shows"
    )

    theater = models.ForeignKey(
        Theater,
        on_delete=models.CASCADE,
        related_name="shows"
    )

    show_time = models.DateTimeField(
        db_index=True
    )

    ticket_price = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["movie", "show_time"]
            ),
            models.Index(
                fields=["theater", "show_time"]
            ),
        ]

    def __str__(self):
        return (
            f"{self.movie.title} - "
            f"{self.theater.name} - "
            f"{self.show_time}"
        )


class Booking(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="movie_bookings"
    )

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    show = models.ForeignKey(
        Show,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    booked_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["user", "booked_at"]
            ),
            models.Index(
                fields=["movie", "booked_at"]
            ),
        ]

    def __str__(self):
        return f"Booking #{self.id}"


class RecentlyViewed(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recently_viewed"
    )

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name="recent_views"
    )

    viewed_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        ordering = ["-viewed_at"]

        indexes = [
            models.Index(
                fields=["user", "viewed_at"]
            ),
        ]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.movie.title}"
        )