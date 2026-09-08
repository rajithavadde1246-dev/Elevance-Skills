from django.urls import path
from . import views


urlpatterns = [

    # Login / Register

    path(
        "login/",
        views.login_view,
        name="login_view"
    ),

    path(
        "register/",
        views.register,
        name="register"
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout_view"
    ),


    # Shows

    path(
        "",
        views.show_list,
        name="show_list"
    ),


    # Seats

    path(
        "show/<int:show_id>/seats/",
        views.seat_selection,
        name="seat_selection"
    ),

    path(
        "show/<int:show_id>/reserve/",
        views.reserve_seats,
        name="reserve_seats"
    ),


    # Payment

    path(
        "booking/<int:booking_id>/payment/",
        views.payment_page,
        name="payment_page"
    ),

    path(
        "booking/<int:booking_id>/create-payment/",
        views.create_payment,
        name="create_payment"
    ),

    path(
        "payment/verify/",
        views.verify_payment,
        name="verify_payment"
    ),

    path(
        "payment/success/",
        views.payment_success,
        name="payment_success"
    ),

    path(
        "payment/failed/",
        views.payment_failed,
        name="payment_failed"
    ),

    path(
        "payment/cancel/<int:payment_id>/",
        views.payment_cancelled,
        name="payment_cancelled"
    ),

    path(
        "booking/<int:booking_id>/retry/",
        views.retry_payment,
        name="retry_payment"
    ),


    # Booking History

    path(
        "booking/history/",
        views.booking_history,
        name="booking_history"
    ),


    # Demo Payment

    path(
        "booking/<int:booking_id>/demo-success/",
        views.demo_payment,
        name="demo_payment"
    ),

    path(
        "booking/<int:booking_id>/demo-failed/",
        views.demo_failed_payment,
        name="demo_failed_payment"
    ),

    path(
        "booking/<int:booking_id>/demo-cancelled/",
        views.demo_cancelled_payment,
        name="demo_cancelled_payment"
    ),


    # Razorpay Webhook

    path(
        "razorpay/webhook/",
        views.razorpay_webhook,
        name="razorpay_webhook"
    ),
]