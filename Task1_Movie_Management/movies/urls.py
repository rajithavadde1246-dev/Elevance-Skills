from django.urls import path
from . import views


urlpatterns = [
    path("", views.home, name="home"),

    path(
        "movie/<int:movie_id>/",
        views.movie_detail,
        name="movie_detail"
    ),

    path(
        "register/",
        views.register,
        name="register"
    ),

    path(
        "login/",
        views.user_login,
        name="login"
    ),

    path(
        "logout/",
        views.user_logout,
        name="logout"
    ),

    path(
        "movie/<int:movie_id>/book/",
        views.book_movie,
        name="book_movie"
    ),

    path(
        "movie/<int:movie_id>/review/",
        views.add_review,
        name="add_review"
    ),

    path(
        "review/<int:review_id>/edit/",
        views.edit_review,
        name="edit_review"
    ),

    path(
        "review/<int:review_id>/report/",
        views.report_review,
        name="report_review"
    ),
]