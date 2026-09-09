import csv

from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Avg
from django.db.models.functions import TruncDate, ExtractHour
from django.http import HttpResponse
from django.shortcuts import render

from .models import Movie, Theater, Booking, Refund


# ==========================================================
# ADMIN ACCESS
# ==========================================================

def admin_required(view_func):
    return user_passes_test(
        lambda user: user.is_authenticated and user.is_staff
    )(view_func)


# ==========================================================
# DASHBOARD
# ==========================================================

@admin_required
def dashboard_home(request):

    # ------------------------------------------------------
    # DATE FILTER
    # ------------------------------------------------------

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    bookings = Booking.objects.all()

    if start_date:
        bookings = bookings.filter(
            booked_at__date__gte=start_date
        )

    if end_date:
        bookings = bookings.filter(
            booked_at__date__lte=end_date
        )

    # ------------------------------------------------------
    # BASIC STATISTICS
    # ------------------------------------------------------

    total_bookings = bookings.count()

    confirmed_bookings = bookings.filter(
        status=Booking.CONFIRMED
    ).count()

    cancelled_bookings = bookings.filter(
        status=Booking.CANCELLED
    ).count()

    total_users = bookings.values(
        "user_id"
    ).distinct().count()

    # ------------------------------------------------------
    # TOTAL REVENUE
    # ------------------------------------------------------

    total_revenue = (
        bookings
        .filter(status=Booking.CONFIRMED)
        .aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

    # ------------------------------------------------------
    # REVENUE OVERVIEW
    # ------------------------------------------------------

    if start_date or end_date:

        filtered_confirmed = bookings.filter(
            status=Booking.CONFIRMED
        )

        filtered_revenue = (
            filtered_confirmed
            .aggregate(
                total=Sum("amount")
            )["total"] or 0
        )

        daily_revenue = filtered_revenue
        weekly_revenue = filtered_revenue
        monthly_revenue = filtered_revenue
        yearly_revenue = filtered_revenue

    else:

        from django.utils import timezone

        today = timezone.localdate()

        daily_revenue = (
            Booking.objects
            .filter(
                status=Booking.CONFIRMED,
                booked_at__date=today
            )
            .aggregate(
                total=Sum("amount")
            )["total"] or 0
        )

        weekly_revenue = (
            Booking.objects
            .filter(
                status=Booking.CONFIRMED,
                booked_at__date__gte=(
                    today - timezone.timedelta(days=6)
                ),
                booked_at__date__lte=today
            )
            .aggregate(
                total=Sum("amount")
            )["total"] or 0
        )

        monthly_revenue = (
            Booking.objects
            .filter(
                status=Booking.CONFIRMED,
                booked_at__year=today.year,
                booked_at__month=today.month
            )
            .aggregate(
                total=Sum("amount")
            )["total"] or 0
        )

        yearly_revenue = (
            Booking.objects
            .filter(
                status=Booking.CONFIRMED,
                booked_at__year=today.year
            )
            .aggregate(
                total=Sum("amount")
            )["total"] or 0
        )

    # ------------------------------------------------------
    # MOST BOOKED MOVIES
    # ------------------------------------------------------

    most_booked_movies = (
        bookings
        .filter(status=Booking.CONFIRMED)
        .values("movie__name")
        .annotate(
            booking_count=Count("id")
        )
        .order_by("-booking_count")[:5]
    )

    # ------------------------------------------------------
    # TOP PERFORMING THEATERS
    # ------------------------------------------------------

    top_theaters = (
        bookings
        .filter(status=Booking.CONFIRMED)
        .values("theater__name")
        .annotate(
            booking_count=Count("id")
        )
        .order_by("-booking_count")[:5]
    )

    # ------------------------------------------------------
    # THEATER OCCUPANCY
    # ------------------------------------------------------

    theater_occupancy = (
        bookings
        .filter(status=Booking.CONFIRMED)
        .values(
            "theater_id",
            "theater__name",
            "theater__total_seats"
        )
        .annotate(
            booking_count=Count("id"),
            total_seats_booked=Sum("seats_booked"),
            average_seats_booked=Avg("seats_booked")
        )
        .order_by("theater__name")
    )

    occupancy_data = []

    for theater in theater_occupancy:

        total_seats = (
            theater["theater__total_seats"] or 0
        )

        average_seats = (
            theater["average_seats_booked"] or 0
        )

        if total_seats > 0:

            occupancy_percentage = round(
                (
                    float(average_seats)
                    / total_seats
                ) * 100,
                2
            )

        else:
            occupancy_percentage = 0

        occupancy_data.append({
            "name": theater["theater__name"],
            "total_seats": total_seats,
            "seats_booked": round(
                float(average_seats),
                2
            ),
            "occupancy_percentage":
                occupancy_percentage,
        })

    # ------------------------------------------------------
    # ADD THEATERS WITH ZERO BOOKINGS
    # ------------------------------------------------------

    booked_theater_ids = {
        theater["theater_id"]
        for theater in theater_occupancy
    }

    empty_theaters = (
        Theater.objects
        .exclude(
            id__in=booked_theater_ids
        )
        .values(
            "id",
            "name",
            "total_seats"
        )
        .order_by("name")
    )

    for theater in empty_theaters:

        occupancy_data.append({
            "name": theater["name"],
            "total_seats":
                theater["total_seats"],
            "seats_booked": 0,
            "occupancy_percentage": 0,
        })

    # ------------------------------------------------------
    # PEAK BOOKING HOURS
    # ------------------------------------------------------

    peak_hours = (
        bookings
        .annotate(
            booking_hour=ExtractHour(
                "booked_at"
            )
        )
        .values("booking_hour")
        .annotate(
            total=Count("id")
        )
        .order_by("-total")[:5]
    )

    # ------------------------------------------------------
    # BOOKING TRENDS
    # ------------------------------------------------------

    booking_trend = (
        bookings
        .annotate(
            booking_date=TruncDate(
                "booked_at"
            )
        )
        .values("booking_date")
        .annotate(
            total=Count("id")
        )
        .order_by("booking_date")
    )

    # ------------------------------------------------------
    # CANCELLATION & REFUND STATISTICS
    # ------------------------------------------------------

    refund_queryset = Refund.objects.filter(
        booking__in=bookings
    )

    refund_count = refund_queryset.filter(
        status=Refund.COMPLETED
    ).count()

    refund_amount = (
        refund_queryset
        .filter(status=Refund.COMPLETED)
        .aggregate(
            total=Sum("amount")
        )["total"] or 0
    )

    # ------------------------------------------------------
    # USER GROWTH
    # ------------------------------------------------------

    users = User.objects.all()

    if start_date:
        users = users.filter(
            date_joined__date__gte=start_date
        )

    if end_date:
        users = users.filter(
            date_joined__date__lte=end_date
        )

    user_growth = (
        users
        .annotate(
            registration_date=TruncDate(
                "date_joined"
            )
        )
        .values("registration_date")
        .annotate(
            users=Count("id")
        )
        .order_by("registration_date")
    )

    # ------------------------------------------------------
    # BOOKING DETAILS
    # ------------------------------------------------------

    booking_details = (
        bookings
        .select_related(
            "user",
            "movie",
            "theater"
        )
        .order_by("-booked_at")[:100]
    )

    # ------------------------------------------------------
    # CONTEXT
    # ------------------------------------------------------

    context = {

        "total_revenue":
            total_revenue,

        "total_bookings":
            total_bookings,

        "confirmed_bookings":
            confirmed_bookings,

        "cancelled_bookings":
            cancelled_bookings,

        "total_users":
            total_users,

        "daily_revenue":
            daily_revenue,

        "weekly_revenue":
            weekly_revenue,

        "monthly_revenue":
            monthly_revenue,

        "yearly_revenue":
            yearly_revenue,

        "refund_count":
            refund_count,

        "refund_amount":
            refund_amount,

        "most_booked_movies":
            most_booked_movies,

        "top_theaters":
            top_theaters,

        "theater_occupancy":
            occupancy_data,

        "peak_hours":
            peak_hours,

        "booking_trend":
            booking_trend,

        "user_growth":
            user_growth,

        "bookings":
            booking_details,

        "start_date":
            start_date or "",

        "end_date":
            end_date or "",
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context
    )


# ==========================================================
# EXPORT CSV
# ==========================================================

@admin_required
def export_csv(request):

    start_date = request.GET.get(
        "start_date"
    )

    end_date = request.GET.get(
        "end_date"
    )

    bookings = (
        Booking.objects
        .select_related(
            "user",
            "movie",
            "theater"
        )
        .all()
    )

    if start_date:

        bookings = bookings.filter(
            booked_at__date__gte=start_date
        )

    if end_date:

        bookings = bookings.filter(
            booked_at__date__lte=end_date
        )

    response = HttpResponse(
        content_type="text/csv"
    )

    response["Content-Disposition"] = (
        'attachment; filename="booking_report.csv"'
    )

    writer = csv.writer(response)

    writer.writerow([
        "Booking ID",
        "User",
        "Movie",
        "Theater",
        "Amount",
        "Seats",
        "Status",
        "Booked At"
    ])

    for booking in bookings.iterator():

        writer.writerow([
            booking.id,
            booking.user.username,
            booking.movie.name,
            booking.theater.name,
            booking.amount,
            booking.seats_booked,
            booking.status,
            booking.booked_at.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ])

    return response