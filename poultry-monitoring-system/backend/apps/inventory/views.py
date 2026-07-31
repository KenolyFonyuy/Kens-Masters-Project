from apps.core.mixins import AuditCreateUpdateMixin, RoleRequiredMixin, UidUrlMixin
from apps.farms.services import farms_for_user
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import InventoryItemForm, StockMovementForm
from .models import InventoryItem, StockMovement

MANAGE = ("ADMIN", "OWNER", "MANAGER")


class InventoryItemListView(LoginRequiredMixin, ListView):
    model = InventoryItem
    template_name = "inventory/item_list.html"
    context_object_name = "items"
    paginate_by = 25

    def get_queryset(self):
        allowed = farms_for_user(self.request.user)
        qs = super().get_queryset().filter(farm__in=allowed).select_related("category", "farm")
        if self.request.GET.get("low") == "1":
            qs = [i for i in qs if i.is_low_stock]
        return qs


class InventoryItemDetailView(UidUrlMixin, LoginRequiredMixin, DetailView):
    model = InventoryItem
    template_name = "inventory/item_detail.html"

    def get_queryset(self):
        return super().get_queryset().filter(farm__in=farms_for_user(self.request.user))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["movements"] = self.object.movements.all()[:50]
        return ctx


class InventoryItemCreateView(RoleRequiredMixin, AuditCreateUpdateMixin, CreateView):
    allowed_roles = MANAGE
    model = InventoryItem
    form_class = InventoryItemForm
    template_name = "inventory/item_form.html"
    success_url = reverse_lazy("inventory:item_list")


class InventoryItemUpdateView(UidUrlMixin, RoleRequiredMixin, AuditCreateUpdateMixin, UpdateView):
    allowed_roles = MANAGE
    model = InventoryItem
    form_class = InventoryItemForm
    template_name = "inventory/item_form.html"
    success_url = reverse_lazy("inventory:item_list")


class StockMovementListView(LoginRequiredMixin, ListView):
    model = StockMovement
    template_name = "inventory/movement_list.html"
    context_object_name = "movements"
    paginate_by = 30

    def get_queryset(self):
        allowed = farms_for_user(self.request.user)
        return (
            super().get_queryset().filter(item__farm__in=allowed).select_related("item")
        )


class StockMovementCreateView(RoleRequiredMixin, AuditCreateUpdateMixin, CreateView):
    allowed_roles = MANAGE
    model = StockMovement
    form_class = StockMovementForm
    template_name = "inventory/movement_form.html"
    success_url = reverse_lazy("inventory:movement_list")

    def form_valid(self, form):
        messages.success(self.request, "Stock movement recorded.")
        return super().form_valid(form)
