import json
import os
import razorpay

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt

from .models import MovieShow, Seat, ShowSeat, Booking, Payment


# =========================================================
# RAZORPAY CLIENT
# =========================================================

def get_razorpay_client():

    return razorpay.Client({
        "key_id": settings.RAZORPAY_KEY_ID,
        "key_secret": settings.RAZORPAY_KEY_SECRET,
    })


# =========================================================
# LOGIN
# =========================================================

def login_view(request):

    if request.user.is_authenticated:
        return redirect("show_list")

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect("show_list")

        messages.error(
            request,
            "Invalid username or password."
        )

    return render(
        request,
        "login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@login_required
def logout_view(request):

    logout(request)

    return redirect("login_view")


# =========================================================
# REGISTER
# =========================================================

def register(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        if User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                "Username already exists."
            )

            return render(
                request,
                "register.html"
            )

        User.objects.create_user(
            username=username,
            password=password
        )

        messages.success(
            request,
            "Registration successful. Please login."
        )

        return redirect("login_view")

    return render(
        request,
        "register.html"
    )


# =========================================================
# SHOW LIST
# =========================================================

@login_required
def show_list(request):

    shows = MovieShow.objects.all().order_by(
        "show_time"
    )

    return render(
        request,
        "shows.html",
        {
            "shows": shows
        }
    )


# =========================================================
# SEAT SELECTION
# =========================================================

@login_required
def seat_selection(request, show_id):

    show = get_object_or_404(
        MovieShow,
        id=show_id
    )

    show_seats = ShowSeat.objects.filter(
        show=show
    ).select_related(
        "seat"
    ).order_by(
        "seat__seat_number"
    )

    # Release expired reservations

    for show_seat in show_seats:

        if show_seat.is_reservation_expired():

            show_seat.release_if_expired()

    show_seats = ShowSeat.objects.filter(
        show=show
    ).select_related(
        "seat"
    ).order_by(
        "seat__seat_number"
    )

    return render(
        request,
        "seat_selection.html",
        {
            "show": show,
            "show_seats": show_seats
        }
    )


# =========================================================
# RESERVE SEATS
# =========================================================

@login_required
@transaction.atomic
def reserve_seats(request, show_id):

    if request.method != "POST":

        return JsonResponse(
            {
                "error": "POST request required."
            },
            status=405
        )

    show = get_object_or_404(
        MovieShow.objects.select_for_update(),
        id=show_id
    )

    seat_ids = request.POST.getlist(
        "seat_ids[]"
    )

    if not seat_ids:

        seat_ids = request.POST.getlist(
            "seat_ids"
        )

    # Support JSON request

    if not seat_ids:

        try:

            data = json.loads(
                request.body.decode("utf-8")
            )

            seat_ids = data.get(
                "seat_ids",
                []
            )

        except Exception:

            seat_ids = []

    if not seat_ids:

        return JsonResponse(
            {
                "error":
                    "Please select at least one seat."
            },
            status=400
        )

    try:

        seat_ids = [
            int(seat_id)
            for seat_id in seat_ids
        ]

    except (ValueError, TypeError):

        return JsonResponse(
            {
                "error":
                    "Invalid seat selection."
            },
            status=400
        )

    show_seats = list(
        ShowSeat.objects
        .select_for_update()
        .select_related("seat")
        .filter(
            show=show,
            id__in=seat_ids
        )
    )

    if len(show_seats) != len(set(seat_ids)):

        return JsonResponse(
            {
                "error":
                    "One or more selected seats are invalid."
            },
            status=400
        )

    # Check availability

    for show_seat in show_seats:

        if show_seat.is_reservation_expired():

            show_seat.release_if_expired()

        elif (
            show_seat.status == ShowSeat.RESERVED
            and show_seat.reserved_by != request.user
        ):

            return JsonResponse(
                {
                    "error":
                        f"Seat "
                        f"{show_seat.seat.seat_number} "
                        f"is reserved."
                },
                status=400
            )

        elif show_seat.status == ShowSeat.BOOKED:

            return JsonResponse(
                {
                    "error":
                        f"Seat "
                        f"{show_seat.seat.seat_number} "
                        f"is already booked."
                },
                status=400
            )

    # Reserve seats

    for show_seat in show_seats:

        show_seat.reserve(
            request.user
        )

        show_seat.save(
            update_fields=[
                "status",
                "reserved_by",
                "reserved_until"
            ]
        )

    # Ticket price

    ticket_price = 200

    total_amount = ticket_price * len(
        show_seats
    )

    # Create pending booking

    booking = Booking.objects.create(
        user=request.user,
        show=show,
        total_amount=total_amount,
        status=Booking.PENDING
    )

    booking.seats.set(
        show_seats
    )

    return JsonResponse(
        {
            "success": True,
            "booking_id": booking.id,
            "amount": total_amount,
            "redirect_url":
                f"/booking/{booking.id}/payment/"
        }
    )


# =========================================================
# CREATE RAZORPAY PAYMENT
# =========================================================

@login_required
@transaction.atomic
def create_payment(request, booking_id):

    if request.method != "POST":

        return JsonResponse(
            {
                "error":
                    "POST request required."
            },
            status=405
        )

    booking = get_object_or_404(
        Booking.objects.select_for_update(),
        id=booking_id,
        user=request.user
    )

    # Check successful payment

    successful_payment = Payment.objects.filter(
        booking=booking,
        status=Payment.SUCCESS
    ).first()

    if successful_payment:

        return JsonResponse(
            {
                "success": True,
                "message":
                    "Booking is already paid.",
                "booking_id":
                    booking.id
            }
        )

    # Check existing pending payment

    existing_payment = Payment.objects.filter(
        booking=booking,
        status=Payment.PENDING
    ).first()

    if existing_payment:

        return JsonResponse(
            {
                "success": True,
                "payment_id":
                    existing_payment.id,
                "order_id":
                    existing_payment.razorpay_order_id,
                "amount":
                    int(existing_payment.amount * 100),
                "currency":
                    "INR",
                "key":
                    settings.RAZORPAY_KEY_ID
            }
        )

    # Check booking amount

    if booking.total_amount <= 0:

        return JsonResponse(
            {
                "error":
                    "Invalid booking amount."
            },
            status=400
        )

    amount_paise = int(
        booking.total_amount * 100
    )

    try:

        client = get_razorpay_client()

        razorpay_order = client.order.create(
            {
                "amount": amount_paise,
                "currency": "INR",
                "payment_capture": 1
            }
        )

    except Exception as e:

        print("=" * 50)
        print("RAZORPAY ORDER CREATION ERROR:")
        print(str(e))
        print("=" * 50)

        return JsonResponse(
            {
                "error":
                    "Razorpay Test API credentials are not available. "
                    "Use Test Payment mode for local demonstration."
            },
            status=500
        )

    payment = Payment.objects.create(
        booking=booking,
        razorpay_order_id=razorpay_order["id"],
        amount=booking.total_amount,
        status=Payment.PENDING
    )

    return JsonResponse(
        {
            "success": True,
            "payment_id":
                payment.id,
            "order_id":
                razorpay_order["id"],
            "amount":
                amount_paise,
            "currency":
                "INR",
            "key":
                settings.RAZORPAY_KEY_ID
        }
    )


# =========================================================
# PAYMENT PAGE
# =========================================================

@login_required
def payment_page(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user
    )

    return render(
        request,
        "payment.html",
        {
            "booking": booking,
            "razorpay_key":
                settings.RAZORPAY_KEY_ID
        }
    )


# =========================================================
# VERIFY PAYMENT
# =========================================================

@login_required
@transaction.atomic
def verify_payment(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "error":
                    "POST request required."
            },
            status=405
        )

    razorpay_payment_id = request.POST.get(
        "razorpay_payment_id"
    )

    razorpay_order_id = request.POST.get(
        "razorpay_order_id"
    )

    razorpay_signature = request.POST.get(
        "razorpay_signature"
    )

    if not all(
        [
            razorpay_payment_id,
            razorpay_order_id,
            razorpay_signature
        ]
    ):

        return JsonResponse(
            {
                "error":
                    "Payment verification data is missing."
            },
            status=400
        )

    payment = get_object_or_404(
        Payment.objects
        .select_for_update()
        .select_related("booking"),
        razorpay_order_id=razorpay_order_id,
        booking__user=request.user
    )

    # Prevent duplicate confirmation

    if payment.status == Payment.SUCCESS:

        return JsonResponse(
            {
                "success": True,
                "message":
                    "Payment already verified.",
                "booking_id":
                    payment.booking.id
            }
        )

    client = get_razorpay_client()

    try:

        client.utility.verify_payment_signature(
            {
                "razorpay_order_id":
                    razorpay_order_id,

                "razorpay_payment_id":
                    razorpay_payment_id,

                "razorpay_signature":
                    razorpay_signature
            }
        )

    except razorpay.errors.SignatureVerificationError:

        payment.status = Payment.FAILED

        payment.razorpay_payment_id = (
            razorpay_payment_id
        )

        payment.razorpay_signature = (
            razorpay_signature
        )

        payment.save()

        release_booking_seats(
            payment.booking
        )

        return JsonResponse(
            {
                "error":
                    "Payment verification failed."
            },
            status=400
        )

    # Payment successful

    payment.status = Payment.SUCCESS

    payment.razorpay_payment_id = (
        razorpay_payment_id
    )

    payment.razorpay_signature = (
        razorpay_signature
    )

    payment.save()

    booking = payment.booking

    # Confirm booking

    if booking.status != Booking.CONFIRMED:

        booking.status = Booking.CONFIRMED

        booking.save(
            update_fields=["status"]
        )

    # Book seats

    show_seats = booking.seats.select_for_update()

    for show_seat in show_seats:

        if (
            show_seat.status == ShowSeat.RESERVED
            and show_seat.reserved_by_id ==
                request.user.id
        ):

            show_seat.book()

            show_seat.save(
                update_fields=[
                    "status",
                    "reserved_until"
                ]
            )

    return JsonResponse(
        {
            "success": True,
            "message":
                "Payment successful. Booking confirmed.",
            "booking_id":
                booking.id
        }
    )


# =========================================================
# RELEASE BOOKING SEATS
# =========================================================

def release_booking_seats(booking):

    for show_seat in booking.seats.select_for_update():

        if show_seat.status == ShowSeat.RESERVED:

            show_seat.status = ShowSeat.AVAILABLE

            show_seat.reserved_by = None

            show_seat.reserved_until = None

            show_seat.save(
                update_fields=[
                    "status",
                    "reserved_by",
                    "reserved_until"
                ]
            )

    booking.status = Booking.CANCELLED

    booking.save(
        update_fields=["status"]
    )


# =========================================================
# PAYMENT SUCCESS PAGE
# =========================================================

@login_required
def payment_success(request):

    return render(
        request,
        "payment_success.html"
    )


# =========================================================
# PAYMENT FAILED
# =========================================================

@login_required
@transaction.atomic
def payment_failed(request):

    payment_id = (
        request.POST.get("payment_id")
        or
        request.GET.get("payment_id")
    )

    if payment_id:

        payment = get_object_or_404(
            Payment.objects.select_for_update(),
            id=payment_id,
            booking__user=request.user
        )

        if payment.status != Payment.SUCCESS:

            payment.status = Payment.FAILED

            payment.save(
                update_fields=["status"]
            )

            release_booking_seats(
                payment.booking
            )

    return render(
        request,
        "payment_failed.html"
    )


# =========================================================
# PAYMENT CANCELLED
# =========================================================

@login_required
@transaction.atomic
def payment_cancelled(request, payment_id):

    payment = get_object_or_404(
        Payment.objects.select_for_update(),
        id=payment_id,
        booking__user=request.user
    )

    if payment.status == Payment.SUCCESS:

        return JsonResponse(
            {
                "error":
                    "Successful payment cannot be cancelled."
            },
            status=400
        )

    payment.status = Payment.CANCELLED

    payment.save(
        update_fields=["status"]
    )

    release_booking_seats(
        payment.booking
    )

    return JsonResponse(
        {
            "success": True,
            "message":
                "Payment cancelled and seats released."
        }
    )


# =========================================================
# RETRY PAYMENT
# =========================================================

@login_required
def retry_payment(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user
    )

    successful_payment = Payment.objects.filter(
        booking=booking,
        status=Payment.SUCCESS
    ).first()

    if successful_payment:

        return redirect(
            "payment_page",
            booking_id=booking.id
        )

    return redirect(
        "payment_page",
        booking_id=booking.id
    )


# =========================================================
# BOOKING HISTORY
# =========================================================

@login_required
def booking_history(request):

    bookings = Booking.objects.filter(
        user=request.user
    ).prefetch_related(
        "seats__seat",
        "payments"
    ).select_related(
        "show"
    ).order_by(
        "-booked_at"
    )

    payments = Payment.objects.filter(
        booking__user=request.user
    ).select_related(
        "booking"
    ).order_by(
        "-created_at"
    )

    return render(
        request,
        "history.html",
        {
            "bookings": bookings,
            "payments": payments
        }
    )


# =========================================================
# DEMO PAYMENT SUCCESS
# =========================================================

@login_required
@transaction.atomic
def demo_payment(request, booking_id):

    booking = get_object_or_404(
        Booking.objects.select_for_update(),
        id=booking_id,
        user=request.user
    )

    payment = Payment.objects.filter(
        booking=booking,
        status=Payment.SUCCESS
    ).first()

    if payment:

        return redirect(
            "payment_success"
        )

    payment = Payment.objects.filter(
        booking=booking,
        status=Payment.PENDING
    ).first()

    if not payment:

        payment = Payment.objects.create(
            booking=booking,
            razorpay_order_id=
                f"TEST_ORDER_{booking.id}",
            amount=booking.total_amount,
            status=Payment.SUCCESS
        )

    else:

        payment.status = Payment.SUCCESS

        payment.razorpay_payment_id = (
            f"TEST_PAYMENT_{booking.id}"
        )

        payment.save()

    booking.status = Booking.CONFIRMED

    booking.save(
        update_fields=["status"]
    )

    for show_seat in booking.seats.select_for_update():

        show_seat.status = ShowSeat.BOOKED

        show_seat.reserved_until = None

        show_seat.save(
            update_fields=[
                "status",
                "reserved_until"
            ]
        )

    return redirect(
        "payment_success"
    )


# =========================================================
# DEMO PAYMENT FAILED
# =========================================================

@login_required
@transaction.atomic
def demo_failed_payment(request, booking_id):

    booking = get_object_or_404(
        Booking.objects.select_for_update(),
        id=booking_id,
        user=request.user
    )

    payment = Payment.objects.filter(
        booking=booking,
        status=Payment.PENDING
    ).first()

    if not payment:

        payment = Payment.objects.create(
            booking=booking,
            razorpay_order_id=
                f"TEST_FAILED_ORDER_{booking.id}",
            razorpay_payment_id=
                f"TEST_FAILED_PAYMENT_{booking.id}",
            amount=booking.total_amount,
            status=Payment.FAILED
        )

    else:

        payment.status = Payment.FAILED

        payment.razorpay_payment_id = (
            f"TEST_FAILED_PAYMENT_{booking.id}"
        )

        payment.save(
            update_fields=[
                "status",
                "razorpay_payment_id"
            ]
        )

    release_booking_seats(
        booking
    )

    return redirect(
        "payment_failed"
    )


# =========================================================
# DEMO PAYMENT CANCELLED
# =========================================================

@login_required
@transaction.atomic
def demo_cancelled_payment(request, booking_id):

    booking = get_object_or_404(
        Booking.objects.select_for_update(),
        id=booking_id,
        user=request.user
    )

    payment = Payment.objects.filter(
        booking=booking,
        status=Payment.PENDING
    ).first()

    if not payment:

        payment = Payment.objects.create(
            booking=booking,
            razorpay_order_id=
                f"TEST_CANCELLED_ORDER_{booking.id}",
            razorpay_payment_id=
                f"TEST_CANCELLED_PAYMENT_{booking.id}",
            amount=booking.total_amount,
            status=Payment.CANCELLED
        )

    else:

        payment.status = Payment.CANCELLED

        payment.razorpay_payment_id = (
            f"TEST_CANCELLED_PAYMENT_{booking.id}"
        )

        payment.save(
            update_fields=[
                "status",
                "razorpay_payment_id"
            ]
        )

    release_booking_seats(
        booking
    )

    return render(
        request,
        "payment_cancelled.html",
        {
            "booking": booking,
            "payment": payment
        }
    )


# =========================================================
# RAZORPAY WEBHOOK
# =========================================================

@csrf_exempt
def razorpay_webhook(request):

    if request.method != "POST":

        return HttpResponse(
            "Only POST requests allowed.",
            status=405
        )

    webhook_secret = os.getenv(
        "RAZORPAY_WEBHOOK_SECRET",
        getattr(
            settings,
            "RAZORPAY_WEBHOOK_SECRET",
            ""
        )
    )

    signature = request.headers.get(
        "X-Razorpay-Signature"
    )

    if not signature:

        return HttpResponse(
            "Missing signature.",
            status=400
        )

    client = get_razorpay_client()

    try:

        client.utility.verify_webhook_signature(
            request.body,
            signature,
            webhook_secret
        )

    except razorpay.errors.SignatureVerificationError:

        return HttpResponse(
            "Invalid webhook signature.",
            status=400
        )

    try:

        payload = json.loads(
            request.body.decode("utf-8")
        )

        event = payload.get(
            "event"
        )

        payment_entity = (
            payload
            .get("payload", {})
            .get("payment", {})
            .get("entity", {})
        )

        razorpay_order_id = payment_entity.get(
            "order_id"
        )

        razorpay_payment_id = payment_entity.get(
            "id"
        )

        if razorpay_order_id:

            with transaction.atomic():

                payment = (
                    Payment.objects
                    .select_for_update()
                    .filter(
                        razorpay_order_id=
                            razorpay_order_id
                    )
                    .first()
                )

                if payment:

                    if event == "payment.captured":

                        if payment.status != Payment.SUCCESS:

                            payment.status = (
                                Payment.SUCCESS
                            )

                            payment.razorpay_payment_id = (
                                razorpay_payment_id
                            )

                            payment.save()

                            booking = payment.booking

                            booking.status = (
                                Booking.CONFIRMED
                            )

                            booking.save(
                                update_fields=[
                                    "status"
                                ]
                            )

                            for show_seat in (
                                booking.seats
                                .select_for_update()
                            ):

                                if (
                                    show_seat.status ==
                                    ShowSeat.RESERVED
                                ):

                                    show_seat.book()

                                    show_seat.save(
                                        update_fields=[
                                            "status",
                                            "reserved_until"
                                        ]
                                    )

                    elif event == "payment.failed":

                        if payment.status != Payment.SUCCESS:

                            payment.status = (
                                Payment.FAILED
                            )

                            payment.razorpay_payment_id = (
                                razorpay_payment_id
                            )

                            payment.save()

                            release_booking_seats(
                                payment.booking
                            )

    except Exception as e:

        print(
            "Webhook processing error:",
            str(e)
        )

        return HttpResponse(
            "Webhook processing failed.",
            status=400
        )

    return HttpResponse(
        "Webhook verified and processed.",
        status=200
    )