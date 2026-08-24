from django.contrib import admin

from .models import (
    Genre,
    Language,
    CastMember,
    Movie,
    MoviePoster,
    Theater,
    Show,
    Booking,
    Review,
)


class MoviePosterInline(admin.TabularInline):
    model = MoviePoster
    extra = 1


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(CastMember)
class CastMemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'role']
    search_fields = ['name', 'role']


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):

    list_display = [
        'title',
        'language',
        'age_certification',
        'duration',
        'release_date',
        'views',
        'average_rating',
    ]

    list_filter = [
        'language',
        'age_certification',
        'genre',
    ]

    search_fields = [
        'title',
        'description',
    ]

    filter_horizontal = [
        'genre',
        'cast',
    ]

    inlines = [
        MoviePosterInline,
    ]


@admin.register(Theater)
class TheaterAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'location',
        'total_seats',
    ]

    search_fields = [
        'name',
        'location',
    ]


@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):

    list_display = [
        'movie',
        'theater',
        'start_time',
        'end_time',
        'price',
        'available_seats',
    ]

    list_filter = [
        'movie',
        'theater',
    ]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):

    list_display = [
        'user',
        'show',
        'seats',
        'status',
        'watched',
        'booked_at',
    ]

    list_filter = [
        'status',
        'watched',
    ]

    search_fields = [
        'user__username',
        'show__movie__title',
    ]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):

    list_display = [
        'user',
        'movie',
        'rating',
        'is_reported',
        'created_at',
    ]

    list_filter = [
        'rating',
        'is_reported',
    ]

    search_fields = [
        'user__username',
        'movie__title',
        'comment',
    ]