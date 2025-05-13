# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile
from datetime import datetime

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Required. Enter a valid email address.")
    handle = forms.CharField(max_length=15, label="Handle", help_text="Your unique handle starting with @ (e.g., @username)", required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'handle', 'password1', 'password2')

    def clean_handle(self):
        handle = self.cleaned_data.get('handle')
        if not handle.startswith('@'):
            handle = f"@{handle}"
        if UserProfile.objects.filter(handle=handle).exists():
            raise forms.ValidationError("This handle is already taken.")
        if len(handle) > 15:
            raise forms.ValidationError("Handle must be 15 characters or less, including the @.")
        return handle

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class KYCForm(forms.Form):
    full_name = forms.CharField(max_length=100, label="Full Name")
    dob_day = forms.IntegerField(min_value=1, max_value=31, label="Day", widget=forms.NumberInput(attrs={'placeholder': 'DD', 'min': 1, 'max': 31}))
    dob_month = forms.IntegerField(min_value=1, max_value=12, label="Month", widget=forms.NumberInput(attrs={'placeholder': 'MM', 'min': 1, 'max': 12}))
    dob_year = forms.IntegerField(min_value=1900, max_value=datetime.now().year - 18, label="Year", widget=forms.NumberInput(attrs={'placeholder': 'YYYY', 'min': 1900, 'max': datetime.now().year - 18}))
    street_address = forms.CharField(max_length=255, label="Street Address")
    city = forms.CharField(max_length=100, label="City")
    postal_code = forms.CharField(max_length=20, label="Postal Code")
    country = forms.CharField(max_length=100, label="Country")

    def clean(self):
        cleaned_data = super().clean()
        dob_day = cleaned_data.get('dob_day')
        dob_month = cleaned_data.get('dob_month')
        dob_year = cleaned_data.get('dob_year')

        # Validate DOB
        if dob_day and dob_month and dob_year:
            try:
                date_of_birth = datetime.strptime(f"{dob_year}-{dob_month}-{dob_day}", "%Y-%m-%d").date()
                cleaned_data['date_of_birth'] = date_of_birth
            except ValueError:
                raise forms.ValidationError("Invalid date of birth.")
            if date_of_birth > datetime.now().date():
                raise forms.ValidationError("Date of birth cannot be in the future.")
            if date_of_birth.year < 1900:
                raise forms.ValidationError("Year of birth is too far in the past.")

        # Combine address fields
        street_address = cleaned_data.get('street_address')
        city = cleaned_data.get('city')
        postal_code = cleaned_data.get('postal_code')
        country = cleaned_data.get('country')
        if street_address and city and postal_code and country:
            cleaned_data['address'] = f"{street_address}, {city}, {postal_code}, {country}"

        return cleaned_data

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar', 'banner']
        widgets = {
            'avatar': forms.FileInput(attrs={'accept': 'image/*'}),
            'banner': forms.FileInput(attrs={'accept': 'image/*'}),
        }

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar and avatar.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Avatar file size must be under 5MB.")
        if avatar and not avatar.content_type.startswith('image/'):
            raise forms.ValidationError("Avatar must be an image file.")
        return avatar

    def clean_banner(self):
        banner = self.cleaned_data.get('banner')
        if banner and banner.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Banner file size must be under 5MB.")
        if banner and not banner.content_type.startswith('image/'):
            raise forms.ValidationError("Banner must be an image file.")
        return banner