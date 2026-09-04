# Smart Seat Reservation System

A Django-based movie seat reservation system that allows users to view seat availability, select multiple seats, temporarily reserve seats, and confirm bookings.

## Features

- User Login and Logout
- Movie show listing
- Multiple seat selection
- Live seat availability
- Available, Reserved and Booked seat status
- 2-minute temporary seat reservation
- Automatic release of expired reservations
- Booking confirmation
- My Bookings page
- Concurrent booking protection
- Django database transactions
- Cinema-style seat layout

## Technologies Used

- Python
- Django
- SQLite
- HTML
- CSS
- JavaScript

## Project Structure

```text
Task2_Smart_Seat_Reservation/
│
├── manage.py
│
├── seat_reservation/
│   ├── settings.py
│   ├── urls.py
│   └── ...
│
├── reservations/
│   ├── migrations/
│   ├── templates/
│   │   └── reservations/
│   │       ├── home.html
│   │       ├── login.html
│   │       ├── show_seats.html
│   │       └── my_bookings.html
│   │
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── signals.py
│   └── apps.py
│
└── db.sqlite3