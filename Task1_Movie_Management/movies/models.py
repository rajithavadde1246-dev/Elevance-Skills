from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Language(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class CastMember(models.Model):
    name = models.CharField(max_length=150)
    role = models.CharField(max_length=150, blank=True)
    photo = models.ImageField(
        upload_to='cast/',
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name


class Movie(models.Model):

    AGE_CERTIFICATION_CHOICES = [
        ('U', 'U'),
        ('UA', 'UA'),
        ('A', 'A'),
        ('S', 'S'),
    ]

    title = models.CharField(max_length=200)

    description = models.TextField()

    genre = models.ManyToManyField(
        Genre,
        related_name='movies'
    )

    language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        related_name='movies'
    )

    cast = models.ManyToManyField(
        CastMember,
        related_name='movies',
        blank=True
    )

    age_certification = models.CharField(
        max_length=5,
        choices=AGE_CERTIFICATION_CHOICES
    )

    duration = models.PositiveIntegerField(
        help_text='Duration in minutes'
    )

    release_date = models.DateField()

    trailer_video_id = models.CharField(
        max_length=50,
        blank=True,
        help_text='Enter only the YouTube video ID'
    )

    views = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def average_rating(self):
        ratings = self.reviews.filter(
            is_reported=False
        ).values_list(
            'rating',
            flat=True
        )

        if not ratings:
            return 0

        return round(
            sum(ratings) / len(ratings),
            1
        )

    def review_count(self):
        return self.reviews.filter(
            is_reported=False
        ).count()

    def __str__(self):
        return self.title


class MoviePoster(models.Model):

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name='posters'
    )

    image = models.ImageField(
        upload_to='posters/'
    )

    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.movie.title} Poster'


class Theater(models.Model):

    name = models.CharField(max_length=150)

    location = models.CharField(max_length=250)

    total_seats = models.PositiveIntegerField(default=100)

    def __str__(self):
        return f'{self.name} - {self.location}'


class Show(models.Model):

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name='shows'
    )

    theater = models.ForeignKey(
        Theater,
        on_delete=models.CASCADE,
        related_name='shows'
    )

    start_time = models.DateTimeField()

    end_time = models.DateTimeField()

    price = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )

    available_seats = models.PositiveIntegerField()

    def has_finished(self):
        return timezone.now() >= self.end_time

    def __str__(self):
        return (
            f'{self.movie.title} - '
            f'{self.theater.name} - '
            f'{self.start_time}'
        )


class Booking(models.Model):

    STATUS_CHOICES = [
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    show = models.ForeignKey(
        Show,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    seats = models.PositiveIntegerField(default=1)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='CONFIRMED'
    )

    booked_at = models.DateTimeField(auto_now_add=True)

    watched = models.BooleanField(default=False)

    def save(self, *args, **kwargs):

        if self.show.has_finished():
            self.watched = True

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f'{self.user.username} - '
            f'{self.show.movie.title}'
        )


class Review(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    rating = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )

    comment = models.TextField()

    is_reported = models.BooleanField(default=False)

    report_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

        constraints = [
            models.UniqueConstraint(
                fields=['user', 'movie'],
                name='one_review_per_user_movie'
            )
        ]

    def is_verified_viewer(self):
        return Booking.objects.filter(
            user=self.user,
            show__movie=self.movie,
            status='CONFIRMED',
            watched=True
        ).exists()

    def __str__(self):
        return (
            f'{self.user.username} - '
            f'{self.movie.title}'
        )