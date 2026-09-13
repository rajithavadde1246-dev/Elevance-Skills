from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from .models import (
    Movie,
    Genre,
    City,
    Theater,
    Show,
    Booking,
    RecentlyViewed,
)


@login_required
def movie_list(request):

    # -----------------------------
    # Get filter values from URL
    # -----------------------------
    search = request.GET.get("search", "").strip()
    genre = request.GET.get("genre", "").strip()
    language = request.GET.get("language", "").strip()
    city = request.GET.get("city", "").strip()
    theater = request.GET.get("theater", "").strip()
    release_date = request.GET.get("release_date", "").strip()
    rating = request.GET.get("rating", "").strip()
    show_time = request.GET.get("show_time", "").strip()
    sort = request.GET.get("sort", "popularity").strip()

    # -----------------------------
    # Start with all movies
    # -----------------------------
    movies = (
        Movie.objects
        .select_related("genre")
        .prefetch_related("theaters__city")
    )

    # -----------------------------
    # Search by movie title
    # -----------------------------
    if search:
        movies = movies.filter(
            title__icontains=search
        )

    # -----------------------------
    # Genre filter
    # -----------------------------
    if genre:
        try:
            movies = movies.filter(
                genre_id=int(genre)
            )
        except (ValueError, TypeError):
            pass

    # -----------------------------
    # Language filter
    # -----------------------------
    if language:
        movies = movies.filter(
            language=language
        )

    # -----------------------------
    # City filter
    # Movie -> Theater -> City
    # -----------------------------
    if city:
        try:
            movies = movies.filter(
                theaters__city_id=int(city)
            )
        except (ValueError, TypeError):
            pass

    # -----------------------------
    # Theater filter
    # -----------------------------
    if theater:
        try:
            movies = movies.filter(
                theaters__id=int(theater)
            )
        except (ValueError, TypeError):
            pass

    # -----------------------------
    # Release date filter
    # -----------------------------
    if release_date:
        movies = movies.filter(
            release_date=release_date
        )

    # -----------------------------
    # Minimum rating filter
    # -----------------------------
    if rating:
        try:
            movies = movies.filter(
                rating__gte=float(rating)
            )
        except (ValueError, TypeError):
            pass

    # -----------------------------
    # Show time filter
    # -----------------------------
    if show_time:
        try:
            movies = movies.filter(
                shows__show_time__hour=int(show_time)
            )
        except (ValueError, TypeError):
            pass

    # -----------------------------
    # Remove duplicate movies
    # -----------------------------
    movies = movies.distinct()

    # -----------------------------
    # Sorting
    # -----------------------------
    if sort == "newest":

        movies = movies.order_by(
            "-release_date"
        )

    elif sort == "rating":

        movies = movies.order_by(
            "-rating"
        )

    elif sort == "price_low":

        movies = movies.order_by(
            "ticket_price"
        )

    elif sort == "price_high":

        movies = movies.order_by(
            "-ticket_price"
        )

    else:

        movies = movies.order_by(
            "-popularity"
        )

    # -----------------------------
    # Count matching movies
    # -----------------------------
    matching_movies = movies.count()

    # -----------------------------
    # Pagination
    # -----------------------------
    paginator = Paginator(
        movies,
        6
    )

    page_number = request.GET.get(
        "page"
    )

    page_obj = paginator.get_page(
        page_number
    )

    # -----------------------------
    # Filter dropdown data
    # -----------------------------
    genres = Genre.objects.all().order_by(
        "name"
    )

    cities = City.objects.all().order_by(
        "name"
    )

    theaters = Theater.objects.select_related(
        "city"
    ).order_by(
        "name"
    )

    # -----------------------------
    # Recommended movies
    # -----------------------------
    booked_movie_ids = Booking.objects.filter(
        user=request.user
    ).values_list(
        "movie_id",
        flat=True
    )

    viewed_movie_ids = RecentlyViewed.objects.filter(
        user=request.user
    ).order_by(
        "-viewed_at"
    ).values_list(
        "movie_id",
        flat=True
    )[:10]

    # -----------------------------
    # Genres from booking history
    # -----------------------------
    booked_genre_ids = Movie.objects.filter(
        id__in=booked_movie_ids
    ).values_list(
        "genre_id",
        flat=True
    )

    # -----------------------------
    # Recommended movies based on:
    # 1. Previously booked genres
    # 2. Recently viewed movies
    # -----------------------------
    recommended_movies = (
        Movie.objects
        .select_related("genre")
        .filter(
            Q(genre_id__in=booked_genre_ids)
            |
            Q(id__in=viewed_movie_ids)
        )
        .exclude(
            id__in=booked_movie_ids
        )
        .order_by(
            "-popularity"
        )
        .distinct()[:5]
    )

    # -----------------------------
    # Send data to HTML
    # -----------------------------
    context = {

        # Movie results
        "movies": page_obj,
        "page_obj": page_obj,

        # Matching movie count
        "matching_movies": matching_movies,

        # Dropdown data
        "genres": genres,
        "cities": cities,
        "theaters": theaters,

        # Selected filter values
        "search": search,
        "selected_genre": genre,
        "selected_language": language,
        "selected_city": city,
        "selected_theater": theater,
        "selected_release_date": release_date,
        "selected_rating": rating,
        "selected_show_time": show_time,
        "selected_sort": sort,

        # Language choices
        "languages": Movie.LANGUAGE_CHOICES,

        # Recommendations
        "recommended_movies": recommended_movies,
    }

    return render(
        request,
        "movies/movie_list.html",
        context
    )


@login_required
def movie_detail(request, movie_id):

    movie = get_object_or_404(
        Movie.objects
        .select_related("genre")
        .prefetch_related("theaters__city"),
        id=movie_id
    )

    # -----------------------------
    # Save/update recently viewed movie
    # -----------------------------
    RecentlyViewed.objects.update_or_create(
        user=request.user,
        movie=movie,
        defaults={
            "viewed_at": timezone.now()
        }
    )

    return render(
        request,
        "movies/movie_detail.html",
        {
            "movie": movie
        }
    )