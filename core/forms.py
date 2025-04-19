from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile
from django import forms

# Custom form for user registration with additional fields
class CustomUserCreationForm(UserCreationForm):
    """Extends UserCreationForm to include email and handle fields for Tipster Arena signup."""
    email = forms.EmailField(
        required=True,
        help_text="Required. Enter a valid email address."
    )  # Email field for user registration
    handle = forms.CharField(
        max_length=15,
        label="Handle",
        help_text="Your unique handle starting with @ (e.g., @username)",
        required=True,
    )  # Unique social handle for the user

    class Meta:
        model = User  # Ties the form to the Django User model
        fields = ('username', 'email', 'handle', 'password1', 'password2')  # Fields to include in the form

    def clean_handle(self):
        """Validate and normalize the handle field."""
        handle = self.cleaned_data.get('handle')
        if not handle.startswith('@'):
            handle = f"@{handle}"  # Ensure handle starts with @
        if UserProfile.objects.filter(handle=handle).exists():
            raise forms.ValidationError("This handle is already taken.")  # Check for uniqueness
        if len(handle) > 15:
            raise forms.ValidationError("Handle must be 15 characters or less, including the @.")  # Enforce length
        return handle

    def save(self, commit=True):
        """Save the user and create a corresponding UserProfile with the handle."""
        user = super().save(commit=False)  # Get the user instance without saving yet
        user.email = self.cleaned_data['email']  # Set the email
        if commit:
            user.save()  # Save the user to the database
            UserProfile.objects.create(
                user=user,
                handle=self.cleaned_data['handle']  # Create UserProfile with handle
            )
        return user

# Form for editing user profile details
class UserProfileForm(forms.ModelForm):
    """Form for updating UserProfile fields in Tipster Arena."""
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell us about yourself'}),
        max_length=160,
        required=False,
        label="Bio"
    )  # Bio field with textarea widget

    class Meta:
        model = UserProfile  # Ties the form to the UserProfile model
        fields = ['description', 'location', 'date_of_birth', 'banner', 'avatar']  # Fields to include in the form