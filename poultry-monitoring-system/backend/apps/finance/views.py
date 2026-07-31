"""Finance views — restricted to roles permitted to see financial data."""
from apps.core.mixins import AuditCreateUpdateMixin, RoleRequiredMixin, UidUrlMixin
from apps.farms.services import farms_for_user
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import ExpenseForm, PaymentForm, SaleForm
from .models import Expense, Payment, Sale

# Workers must not access financial records.
FINANCE_ROLES = ("ADMIN", "OWNER", "MANAGER")


class ExpenseListView(RoleRequiredMixin, ListView):
    allowed_roles = FINANCE_ROLES
    model = Expense
    template_name = "finance/expense_list.html"
    context_object_name = "expenses"
    paginate_by = 25

    def get_queryset(self):
        allowed = farms_for_user(self.request.user)
        qs = super().get_queryset().filter(farm__in=allowed).select_related("farm", "batch")
        cat = self.request.GET.get("category")
        if cat:
            qs = qs.filter(category=cat)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = Expense.Category.choices
        return ctx


class ExpenseCreateView(RoleRequiredMixin, AuditCreateUpdateMixin, CreateView):
    allowed_roles = FINANCE_ROLES
    model = Expense
    form_class = ExpenseForm
    template_name = "finance/record_form.html"
    success_url = reverse_lazy("finance:expense_list")
    extra_context = {"object_label": "Expense"}


class ExpenseUpdateView(UidUrlMixin, RoleRequiredMixin, AuditCreateUpdateMixin, UpdateView):
    allowed_roles = FINANCE_ROLES
    model = Expense
    form_class = ExpenseForm
    template_name = "finance/record_form.html"
    success_url = reverse_lazy("finance:expense_list")
    extra_context = {"object_label": "Expense"}


class SaleListView(RoleRequiredMixin, ListView):
    allowed_roles = FINANCE_ROLES
    model = Sale
    template_name = "finance/sale_list.html"
    context_object_name = "sales"
    paginate_by = 25

    def get_queryset(self):
        allowed = farms_for_user(self.request.user)
        return super().get_queryset().filter(farm__in=allowed).select_related("batch", "customer")


class SaleDetailView(UidUrlMixin, RoleRequiredMixin, DetailView):
    allowed_roles = FINANCE_ROLES
    model = Sale
    template_name = "finance/sale_detail.html"

    def get_queryset(self):
        return super().get_queryset().filter(farm__in=farms_for_user(self.request.user))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["payments"] = self.object.payments.all()
        return ctx


class SaleCreateView(RoleRequiredMixin, AuditCreateUpdateMixin, CreateView):
    allowed_roles = FINANCE_ROLES
    model = Sale
    form_class = SaleForm
    template_name = "finance/record_form.html"
    success_url = reverse_lazy("finance:sale_list")
    extra_context = {"object_label": "Sale"}

    def form_valid(self, form):
        messages.success(self.request, "Sale recorded.")
        return super().form_valid(form)


class SaleUpdateView(UidUrlMixin, RoleRequiredMixin, AuditCreateUpdateMixin, UpdateView):
    allowed_roles = FINANCE_ROLES
    model = Sale
    form_class = SaleForm
    template_name = "finance/record_form.html"
    success_url = reverse_lazy("finance:sale_list")
    extra_context = {"object_label": "Sale"}


class PaymentCreateView(RoleRequiredMixin, AuditCreateUpdateMixin, CreateView):
    allowed_roles = FINANCE_ROLES
    model = Payment
    form_class = PaymentForm
    template_name = "finance/record_form.html"
    success_url = reverse_lazy("finance:sale_list")
    extra_context = {"object_label": "Payment"}
