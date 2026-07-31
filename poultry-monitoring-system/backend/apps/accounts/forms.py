from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserChangeForm,
    UserCreationForm,
)

from .models import CustomUser, UserProfile


class StyledFormMixin:
    """Apply Bootstrap form-control classes without per-field boilerplate."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            css = "form-check-input" if isinstance(
                widget, (forms.CheckboxInput,)
            ) else "form-select" if isinstance(
                widget, (forms.Select, forms.SelectMultiple)
            ) else "form-control"
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing} {css}".strip()


class LoginForm(StyledFormMixin, AuthenticationForm):
    pass


class UserCreateForm(StyledFormMixin, UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("username", "first_name", "last_name", "email", "role", "phone")


class UserUpdateForm(StyledFormMixin, UserChangeForm):
    password = None

    class Meta:
        model = CustomUser
        fields = (
            "username", "first_name", "last_name", "email", "role", "phone",
            "is_active", "assigned_farms",
        )


class ProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ("job_title", "bio", "avatar", "timezone")


class SelfProfileForm(StyledFormMixin, forms.ModelForm):
    """A user editing their own basic details (cannot change their role)."""

    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "email", "phone")
