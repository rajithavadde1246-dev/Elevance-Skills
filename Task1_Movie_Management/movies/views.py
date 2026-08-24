from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Movie, Show, Booking, Review
from .forms import RegisterForm, LoginForm, BookingForm, ReviewForm


def home(request):

    movies = Movie.objects.all()

    return render(
        request,
        "movies/home.html",
        {
            "movies": movies
        }
    )


def movie_detail(request, movie_id):

    movie = get_object_or_404(
        Movie,
        id=movie_id
    )

    return render(
        request,
        "movies/movie_detail.html",
        {
            "movie": movie
        }
    )


def register(request):

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save(
                commit=False
            )

            user.set_password(
                form.cleaned_data["password"]
            )

            user.save()

            messages.success(
                request,
                "Registration successful! Please login."
            )

            return redirect("login")

    else:

        form = RegisterForm()

    return render(
        request,
        "movies/register.html",
        {
            "form": form
        }
    )


def user_login(request):

    if request.method == "POST":

        form = LoginForm(
            request,
            data=request.POST
        )

        if form.is_valid():

            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            user = authenticate(
                request,
                username=username,
                password=password
            )

            if user is not None:

                login(
                    request,
                    user
                )

                messages.success(
                    request,
                    f"Welcome, {user.username}!"
                )

                return redirect("home")

    else:

        form = LoginForm()

    return render(
        request,
        "movies/login.html",
        {
            "form": form
        }
    )


def user_logout(request):

    logout(request)

    messages.success(
        request,
        "You have been logged out successfully."
    )

    return redirect("home")



@login_required
def book_movie(request, movie_id):

    movie = get_object_or_404(
        Movie,
        id=movie_id
    )

    shows = Show.objects.filter(
        movie=movie
    ).order_by(
        "start_time"
    )

    if request.method == "POST":

        show_id = request.POST.get(
            "show"
        )

        show = get_object_or_404(
            Show,
            id=show_id,
            movie=movie
        )

        form = BookingForm(
            request.POST,
            show=show
        )

        if form.is_valid():

            booking = form.save(
                commit=False
            )

            booking.user = request.user
            booking.show = show
            booking.status = "CONFIRMED"

            booking.save()

            show.available_seats -= booking.seats
            show.save()

            messages.success(
                request,
                "Movie booked successfully!"
            )

            return redirect(
                "movie_detail",
                movie_id=movie.id
            )

    else:

        form = BookingForm()

    return render(
        request,
        "movies/book_movie.html",
        {
            "movie": movie,
            "shows": shows,
            "form": form
        }
    )



@login_required
def add_review(request, movie_id):

    movie = get_object_or_404(
        Movie,
        id=movie_id
    )


    has_watched = Booking.objects.filter(
        user=request.user,
        show__movie=movie,
        status="CONFIRMED",
        watched=True
    ).exists()

    if not has_watched:

        messages.warning(
            request,
            "You can review this movie only after booking and watching it."
        )

        return redirect(
            "movie_detail",
            movie_id=movie.id
        )


    existing_review = Review.objects.filter(
        user=request.user,
        movie=movie
    ).first()

    if existing_review:

        messages.warning(
            request,
            "You have already reviewed this movie."
        )

        return redirect(
            "movie_detail",
            movie_id=movie.id
        )


    if request.method == "POST":

        form = ReviewForm(
            request.POST
        )

        if form.is_valid():

            review = form.save(
                commit=False
            )

            review.user = request.user
            review.movie = movie

            review.save()

            messages.success(
                request,
                "Review added successfully!"
            )

            return redirect(
                "movie_detail",
                movie_id=movie.id
            )

    else:

        form = ReviewForm()

    return render(
        request,
        "movies/review.html",
        {
            "movie": movie,
            "form": form
        }
    )


@login_required
def edit_review(request, review_id):

    review = get_object_or_404(
        Review,
        id=review_id,
        user=request.user
    )

    if request.method == "POST":

        form = ReviewForm(
            request.POST,
            instance=review
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Review updated successfully!"
            )

            return redirect(
                "movie_detail",
                movie_id=review.movie.id
            )

    else:

        form = ReviewForm(
            instance=review
        )

    return render(
        request,
        "movies/review.html",
        {
            "movie": review.movie,
            "form": form,
            "edit_mode": True
        }
    )


@login_required
def report_review(request, review_id):

    review = get_object_or_404(
        Review,
        id=review_id
    )

    if request.method == "POST":

        reason = request.POST.get(
            "report_reason",
            ""
        )

        review.is_reported = True
        review.report_reason = reason

        review.save()

        messages.success(
            request,
            "Review reported successfully."
        )

    return redirect(
        "movie_detail",
        movie_id=review.movie.id
    )