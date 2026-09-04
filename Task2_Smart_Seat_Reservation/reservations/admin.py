from django.contrib import admin
from .models import MovieShow, Seat, ShowSeat, Booking


@admin.register(MovieShow)
class MovieShowAdmin(admin.ModelAdmin):
    list_display = ("movie_name", "theater_name", "show_time")
    list_filter = ("theater_name", "show_time")
    search_fields = ("movie_name", "theater_name")


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ("seat_number",)
    search_fields = ("seat_number",)


@admin.register(ShowSeat)
class ShowSeatAdmin(admin.ModelAdmin):
    list_display = (
        "show",
        "seat",
        "status",
        "reserved_by",
        "reserved_until",
    )
    list_filter = ("status", "show")
    search_fields = ("seat__seat_number",)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "show",
        "status",
        "booked_at",
    )
    list_filter = ("status", "show")
    search_fields = ("user__username", "show__movie_name")