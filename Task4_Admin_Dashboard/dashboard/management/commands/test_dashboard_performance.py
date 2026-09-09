import time

from django.core.management.base import BaseCommand
from django.db.models import Count, Sum
from django.db.models.functions import ExtractHour, TruncDate

from dashboard.models import Booking


class Command(BaseCommand):

    help = "Test dashboard performance with large booking data"

    def test_query(self, name, query_function):

        start_time = time.perf_counter()

        result = query_function()

        end_time = time.perf_counter()

        execution_time = (
            end_time - start_time
        ) * 1000

        self.stdout.write(
            f"{name}: {execution_time:.2f} ms"
        )

        return result

    def handle(self, *args, **kwargs):

        self.stdout.write(
            "\n===== DASHBOARD PERFORMANCE TEST =====\n"
        )

        # 1. Total bookings
        self.test_query(
            "Total Bookings",
            lambda: Booking.objects.count()
        )

        # 2. Confirmed bookings
        self.test_query(
            "Confirmed Bookings",
            lambda: Booking.objects.filter(
                status=Booking.CONFIRMED
            ).count()
        )

        # 3. Total revenue
        self.test_query(
            "Total Revenue",
            lambda: Booking.objects.filter(
                status=Booking.CONFIRMED
            ).aggregate(
                total=Sum("amount")
            )
        )

        # 4. Most booked movies
        self.test_query(
            "Most Booked Movies",
            lambda: list(
                Booking.objects
                .filter(status=Booking.CONFIRMED)
                .values("movie_id")
                .annotate(
                    total=Count("id")
                )
                .order_by("-total")[:5]
            )
        )

        # 5. Top theaters
        self.test_query(
            "Top Performing Theaters",
            lambda: list(
                Booking.objects
                .filter(status=Booking.CONFIRMED)
                .values("theater_id")
                .annotate(
                    total=Count("id")
                )
                .order_by("-total")[:5]
            )
        )

        # 6. Peak booking hours
        self.test_query(
            "Peak Booking Hours",
            lambda: list(
                Booking.objects
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
        )

        # 7. Booking trends
        self.test_query(
            "Booking Trends",
            lambda: list(
                Booking.objects
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
        )

        # 8. Explain indexed query
        self.stdout.write(
            "\n===== QUERY OPTIMIZATION =====\n"
        )

        query = (
            Booking.objects
            .filter(
                status=Booking.CONFIRMED
            )
            .values("movie_id")
            .annotate(
                total=Count("id")
            )
            .order_by("-total")[:5]
        )

        self.stdout.write(
            query.explain()
        )

        self.stdout.write(
            "\n===== PERFORMANCE TEST COMPLETED =====\n"
        )