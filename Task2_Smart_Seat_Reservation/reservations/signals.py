from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import MovieShow, Seat, ShowSeat


@receiver(post_save, sender=MovieShow)
def create_show_seats(sender, instance, created, **kwargs):
    if not created:
        return

    seats = Seat.objects.all()

    for seat in seats:
        ShowSeat.objects.get_or_create(
            show=instance,
            seat=seat,
        )