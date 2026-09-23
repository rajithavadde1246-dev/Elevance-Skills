from django.shortcuts import render


def home(request):
    tasks = [
        {
            "number": 1,
            "title": "Movie Management",
            "description": "Movie management, registration, login, booking and reviews.",
        },
        {
            "number": 2,
            "title": "Smart Seat Reservation",
            "description": "Movie shows and smart seat reservation system.",
        },
        {
            "number": 3,
            "title": "Payment & Booking",
            "description": "Booking, payment, cancellation and payment history.",
        },
        {
            "number": 4,
            "title": "Admin Dashboard",
            "description": "Revenue, bookings, occupancy and admin analytics.",
        },
        {
            "number": 5,
            "title": "Movie Discovery",
            "description": "Movie discovery and recommendation features.",
        },
        {
            "number": 6,
            "title": "Automated Ticket",
            "description": "Ticket generation and automated booking workflow.",
        },
    ]

    return render(request, "home.html", {"tasks": tasks})