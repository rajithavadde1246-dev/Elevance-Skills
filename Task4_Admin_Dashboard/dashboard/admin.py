from django.contrib import admin

from .models import Movie, Theater, Booking, Refund


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]


@admin.register(Theater)
class TheaterAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "total_seats"
    ]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "movie",
        "theater",
        "amount",
        "seats_booked",
        "status",
        "booked_at"
    ]

    list_filter = [
        "status",
        "booked_at"
    ]

    search_fields = [
        "user__username",
        "movie__name",
        "theater__name"
    ]


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "booking",
        "amount",
        "status",
        "created_at"
    ]

    list_filter = [
        "status",
        "created_at"
    ]