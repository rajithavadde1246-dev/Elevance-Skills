from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Booking, MovieShow, ShowSeat

def release_expired_seats(show):
    now = timezone.now()

    ShowSeat.objects.filter(
        show=show,
        status=ShowSeat.RESERVED,
        reserved_until__lte=now,
    ).update(
        status=ShowSeat.AVAILABLE,
        reserved_by=None,
        reserved_until=None,
    )


def show_seats(request, show_id):
    show = get_object_or_404(MovieShow, id=show_id)

    release_expired_seats(show)

    show_seats = (
        show.show_seats
        .select_related("seat")
        .order_by("seat__seat_number")
    )

    return render(
        request,
        "reservations/show_seats.html",
        {
            "show": show,
            "show_seats": show_seats,
        },
    )
@login_required
def seat_status(request, show_id):
    """
    Returns live seat availability.
    """

    show = get_object_or_404(MovieShow, id=show_id)

    release_expired_seats(show)

    show_seats = show.show_seats.select_related("seat")

    seats = []

    for show_seat in show_seats:
        seats.append(
            {
                "id": show_seat.id,
                "number": show_seat.seat.seat_number,
                "status": show_seat.status,
                "reserved_by_me": (
                    show_seat.status == ShowSeat.RESERVED
                    and show_seat.reserved_by_id == request.user.id
                ),
                "reserved_until": (
                    show_seat.reserved_until.isoformat()
                    if show_seat.reserved_until
                    else None
                ),
            }
        )

    return JsonResponse(
        {
            "seats": seats
        }
    )
@login_required
@transaction.atomic
def reserve_selected_seats(request, show_id):
    
    if request.method != "POST":
        return redirect(
            "show_seats",
            show_id=show_id,
        )
    show = get_object_or_404(
        MovieShow,
        id=show_id,
    )
    selected_ids = request.POST.getlist(
        "seat_ids"
    )
    if not selected_ids:
        return redirect(
            "show_seats",
            show_id=show_id,
        )
    show_seats = list(
        ShowSeat.objects
        .select_for_update()
        .select_related("seat")
        .filter(show=show)
        .order_by("id")
    )
    now = timezone.now()
    # Release expired reservations.
    for show_seat in show_seats:

        if (
            show_seat.status == ShowSeat.RESERVED
            and (
                not show_seat.reserved_until
                or show_seat.reserved_until <= now
            )
        ):
            show_seat.status = ShowSeat.AVAILABLE
            show_seat.reserved_by = None
            show_seat.reserved_until = None

            show_seat.save(
                update_fields=[
                    "status",
                    "reserved_by",
                    "reserved_until",
                ]
            )

    try:
        selected_ids = {
            int(seat_id)
            for seat_id in selected_ids
        }
    except ValueError:
        return redirect(
            "show_seats",
            show_id=show_id,
        )
    selected_seats = [
        show_seat
        for show_seat in show_seats
        if show_seat.id in selected_ids
    ]
    # Make sure all selected seats belong to this show.
    if len(selected_seats) != len(selected_ids):
        return redirect(
            "show_seats",
            show_id=show_id,
        )
    # Check availability.
    for show_seat in selected_seats:
        if show_seat.status == ShowSeat.BOOKED:
            return redirect(
                "show_seats",
                show_id=show_id,
            )
        if (
            show_seat.status == ShowSeat.RESERVED
            and show_seat.reserved_by_id != request.user.id
        ):
            return redirect(
                "show_seats",
                show_id=show_id,
            )
    for show_seat in show_seats:
        if (
            show_seat.status == ShowSeat.RESERVED
            and show_seat.reserved_by_id == request.user.id
            and show_seat.id not in selected_ids
        ):
            show_seat.status = ShowSeat.AVAILABLE
            show_seat.reserved_by = None
            show_seat.reserved_until = None
            show_seat.save(
                update_fields=[
                    "status",
                    "reserved_by",
                    "reserved_until",
                ]
            )
    reservation_time = (
        now + timezone.timedelta(minutes=2)
    )
    # Reserve selected seats.
    for show_seat in selected_seats:
        show_seat.status = ShowSeat.RESERVED
        show_seat.reserved_by = request.user
        show_seat.reserved_until = reservation_time
        show_seat.save(
            update_fields=[
                "status",
                "reserved_by",
                "reserved_until",
            ]
        )
    return redirect(
        "show_seats",
        show_id=show_id,
    )
@login_required
@transaction.atomic
def confirm_booking(request, show_id):
    if request.method != "POST":
        return redirect(
            "show_seats",
            show_id=show_id,
        )
    show = get_object_or_404(
        MovieShow,
        id=show_id,
    )
    reserved_seats = list(
        ShowSeat.objects
        .select_for_update()
        .filter(
            show=show,
            status=ShowSeat.RESERVED,
            reserved_by=request.user,
        )
        .order_by("id")
    )
    now = timezone.now()
    valid_seats = []
    for show_seat in reserved_seats:
        if (
            show_seat.reserved_until
            and show_seat.reserved_until > now
        ):
            valid_seats.append(
                show_seat
            )
        else:

            show_seat.status = ShowSeat.AVAILABLE
            show_seat.reserved_by = None
            show_seat.reserved_until = None
            show_seat.save(
                update_fields=[
                    "status",
                    "reserved_by",
                    "reserved_until",
                ]
            )
    if not valid_seats:
        return redirect(
            "show_seats",
            show_id=show_id,
        )
    booking = Booking.objects.create(
        user=request.user,
        show=show,
        status=Booking.CONFIRMED,
    )
    booking.seats.set(
        valid_seats
    )
    # Convert RESERVED → BOOKED.
    for show_seat in valid_seats:
        show_seat.book()
        show_seat.save(
            update_fields=[
                "status",
                "reserved_until",
            ]
        )
    return redirect(
        "my_bookings"
    )
@login_required
def my_bookings(request):
    bookings = (
        Booking.objects
        .filter(user=request.user)
        .prefetch_related("seats__seat")
        .select_related("show")
        .order_by("-booked_at")
    )
    return render(
        request,
        "reservations/my_bookings.html",
        {
            "bookings": bookings,
        },
    )
def login_view(request):
    if request.user.is_authenticated:
        return redirect(
            "show_seats",
            show_id=1,
        )
    if request.method == "POST":

        username = request.POST.get(
            "username"
        )
        password = request.POST.get(
            "password"
        )

        user = authenticate(
            request,
            username=username,
            password=password,
        )
        if user is not None:
            login(
                request,
                user,
            )
            return redirect(
                "show_seats",
                show_id=1,
            )
        return render(
            request,
            "reservations/login.html",
            {
                "error":
                    "Invalid username or password."
            },
        )
    return render(
        request,
        "reservations/login.html",
    )
def logout_view(request):

    logout(request)

    return redirect(
        "login_view"
    )
def home(request):
    shows = MovieShow.objects.all().order_by("show_time")

    return render(
        request,
        "reservations/home.html",
        {
            "shows": shows,
        },
    )