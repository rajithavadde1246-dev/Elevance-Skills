from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import render, redirect

from .models import Booking
from .tasks import generate_and_send_ticket


@login_required
def create_booking(request):

    if request.method == 'POST':

        booking = Booking.objects.create(

            user=request.user,

            booking_id=(
                f"BOOK-{request.user.id}-"
                f"{Booking.objects.count() + 1}"
            ),

            movie_name=request.POST.get(
                'movie_name'
            ),

            theater=request.POST.get(
                'theater'
            ),

            screen=request.POST.get(
                'screen'
            ),

            show_date=request.POST.get(
                'show_date'
            ),

            show_time=request.POST.get(
                'show_time'
            ),

            seats=request.POST.get(
                'seats'
            ),

            payment_reference=request.POST.get(
                'payment_reference'
            ),

            payment_status='SUCCESS'
        )

        # IMPORTANT:
        # This starts Celery in the background.
        # The booking request does NOT wait
        # for PDF/email completion.

        generate_and_send_ticket.delay(
            booking.id
        )

        return redirect(
            'booking_success',
            booking_id=booking.booking_id
        )

    return render(
        request,
        'tickets/create_booking.html'
    )


@login_required
def booking_success(
    request,
    booking_id
):

    booking = Booking.objects.get(
        booking_id=booking_id,
        user=request.user
    )

    return render(
        request,
        'tickets/booking_success.html',
        {
            'booking': booking
        }
    )


@login_required
def booking_history(request):

    bookings = Booking.objects.filter(
        user=request.user
    ).order_by(
        '-created_at'
    )

    return render(
        request,
        'tickets/booking_history.html',
        {
            'bookings': bookings
        }
    )


@login_required
def download_ticket(
    request,
    booking_id
):

    try:

        booking = Booking.objects.get(
            booking_id=booking_id,
            user=request.user
        )

    except Booking.DoesNotExist:

        raise Http404(
            "Booking not found"
        )

    if not booking.ticket_pdf:

        return render(
            request,
            'tickets/ticket_not_ready.html',
            {
                'booking': booking
            }
        )

    response = FileResponse(
        booking.ticket_pdf.open('rb'),
        as_attachment=True,
        filename=(
            f"{booking.booking_id}.pdf"
        )
    )

    return response