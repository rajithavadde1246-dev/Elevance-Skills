from django.urls import path

from . import views


urlpatterns = [

    path(
        '',
        views.create_booking,
        name='create_booking'
    ),

    path(
        'success/<str:booking_id>/',
        views.booking_success,
        name='booking_success'
    ),

    path(
        'history/',
        views.booking_history,
        name='booking_history'
    ),

    path(
        'download/<str:booking_id>/',
        views.download_ticket,
        name='download_ticket'
    ),
]