"""Authentication, profile, and user-management views."""
from apps.core.mixins import RoleRequiredMixin
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import (
    LoginForm,
    ProfileForm,
    SelfProfileForm,
    UserCreateForm,
    UserUpdateForm,
)
from .models import CustomUser


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class LogoutView(auth_views.LogoutView):
    pass


class PasswordChangeView(auth_views.PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("accounts:password_change_done")


class PasswordChangeDoneView(auth_views.PasswordChangeDoneView):
    template_name = "accounts/password_change_done.html"


class PasswordResetView(auth_views.PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/password_reset_email.html"
    success_url = reverse_lazy("accounts:password_reset_done")


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"


class AccessDeniedView(TemplateView):
    template_name = "errors/403.html"


class ProfileView(LoginRequiredMixin, UpdateView):
    """A user manages their own profile + basic account details."""

    template_name = "accounts/profile.html"
    form_class = SelfProfileForm
    success_url = reverse_lazy("accounts:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if "profile_form" not in ctx:
            ctx["profile_form"] = ProfileForm(instance=self.request.user.profile)
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        profile_form = ProfileForm(
            request.POST, request.FILES, instance=request.user.profile
        )
        if form.is_valid() and profile_form.is_valid():
            form.save()
            profile_form.save()
            messages.success(request, "Profile updated.")
            return self.form_valid(form)
        return self.render_to_response(
            self.get_context_data(form=form, profile_form=profile_form)
        )


# -- User management (admin/owner) ---------------------------------------
class UserListView(RoleRequiredMixin, ListView):
    allowed_roles = ("ADMIN", "OWNER")
    model = CustomUser
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().order_by("username")
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(username__icontains=q)
        role = self.request.GET.get("role")
        if role:
            qs = qs.filter(role=role)
        return qs


class UserCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ("ADMIN", "OWNER")
    model = CustomUser
    form_class = UserCreateForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:user_list")

    def form_valid(self, form):
        messages.success(self.request, "User created.")
        return super().form_valid(form)


class UserUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = ("ADMIN", "OWNER")
    model = CustomUser
    form_class = UserUpdateForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:user_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.sync_primary_group()
        messages.success(self.request, "User updated.")
        return response


class UserDetailView(RoleRequiredMixin, DetailView):
    allowed_roles = ("ADMIN", "OWNER")
    model = CustomUser
    template_name = "accounts/user_detail.html"
    context_object_name = "object"
