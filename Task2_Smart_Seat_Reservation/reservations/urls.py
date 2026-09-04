from django.urls import path
from . import views

urlpatterns = [
    path(
        "",
        views.home,
        name="home",
    ),

    path(
        "login/",
        views.login_view,
        name="login_view",
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout_view",
    ),

    path(
        "show/<int:show_id>/seats/",
        views.show_seats,
        name="show_seats",
    ),

    path(
        "show/<int:show_id>/seat-status/",
        views.seat_status,
        name="seat_status",
    ),

    path(
        "show/<int:show_id>/reserve/",
        views.reserve_selected_seats,
        name="reserve_selected_seats",
    ),

    path(
        "show/<int:show_id>/confirm/",
        views.confirm_booking,
        name="confirm_booking",
    ),

    path(
        "my-bookings/",
        views.my_bookings,
        name="my_bookings",
    ),
]