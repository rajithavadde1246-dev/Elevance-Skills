from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm

from .models import Booking, Review, Show


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        min_length=6
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()

        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password:
            if password != confirm_password:
                raise forms.ValidationError(
                    'Passwords do not match.'
                )

        return cleaned_data


class LoginForm(AuthenticationForm):
    username = forms.CharField()
    password = forms.CharField(
        widget=forms.PasswordInput
    )


class BookingForm(forms.ModelForm):

    class Meta:
        model = Booking
        fields = ['seats']

    def __init__(self, *args, show=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.show = show

    def clean_seats(self):
        seats = self.cleaned_data['seats']

        if self.show and seats > self.show.available_seats:
            raise forms.ValidationError(
                f'Only {self.show.available_seats} seats are available.'
            )

        return seats


class ReviewForm(forms.ModelForm):

    class Meta:
        model = Review
        fields = ['rating', 'comment']

        widgets = {
            'rating': forms.Select(
                choices=[
                    (1, '⭐ 1'),
                    (2, '⭐⭐ 2'),
                    (3, '⭐⭐⭐ 3'),
                    (4, '⭐⭐⭐⭐ 4'),
                    (5, '⭐⭐⭐⭐⭐ 5'),
                ]
            ),
            'comment': forms.Textarea(
                attrs={
                    'rows': 4,
                    'placeholder': 'Write your review...'
                }
            ),
        }