# forms.py
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile
from django import forms

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
            UserProfile.objects.create(user=user, handle=self.cleaned_data['handle'])
        return user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['description', 'location', 'date_of_birth', 'banner', 'avatar']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell us about yourself'}),
            'banner': forms.FileInput(attrs={'accept': 'image/*'}),
            'avatar': forms.FileInput(attrs={'accept': 'image/*'}),
        }

class ProfileSetupForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar', 'banner']
        widgets = {
            'avatar': forms.FileInput(attrs={'accept': 'image/*'}),
            'banner': forms.FileInput(attrs={'accept': 'image/*'}),
        }

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            if avatar.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError("Avatar file size must be under 5MB.")
            if not avatar.content_type.startswith('image/'):
                raise forms.ValidationError("Avatar must be an image file.")
        return avatar

    def clean_banner(self):
        banner = self.cleaned_data.get('banner')
        if banner:
            if banner.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError("Banner file size must be under 5MB.")
            if not banner.content_type.startswith('image/'):
                raise forms.ValidationError("Banner must be an image file.")
        return banner

class KYCForm(forms.Form):
    full_name = forms.CharField(max_length=100, label="Full Name")
    date_of_birth = forms.DateField(label="Date of Birth")
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), label="Address")