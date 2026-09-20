from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):

    list_display = [
        'booking_id',
        'movie_name',
        'theater',
        'show_date',
        'show_time',
        'seats',
        'payment_status',
        'email_sent',
        'created_at',
    ]

    list_filter = [
        'payment_status',
        'email_sent',
        'show_date',
    ]

    search_fields = [
        'booking_id',
        'movie_name',
        'payment_reference',
    ]