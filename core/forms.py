from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile
from django import forms


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Required. Enter a valid email address.")
    handle = forms.CharField(
        max_length=15,
        label="Handle",
        help_text="Your unique handle starting with @ (e.g., @username)",
        required=True,
    )

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
            # Create UserProfile with the handle
            UserProfile.objects.create(
                user=user,
                handle=self.cleaned_data['handle']
            )
        return user


class UserProfileForm(forms.ModelForm):
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell us about yourself'}),
        max_length=160,
        required=False,
        label="Bio"
    )

    class Meta:
        model = UserProfile
        fields = ['description', 'location', 'date_of_birth', 'banner', 'avatar']