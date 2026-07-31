"""CRUD views for farms, pens, breeds, suppliers and customers."""
from apps.core.mixins import AuditCreateUpdateMixin, RoleRequiredMixin, UidUrlMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import BreedForm, CustomerForm, FarmForm, PenForm, SupplierForm
from .models import Breed, Customer, Farm, Pen, Supplier
from .services import farms_for_user

MANAGE = ("ADMIN", "OWNER", "MANAGER")


class FarmListView(LoginRequiredMixin, ListView):
    model = Farm
    template_name = "farms/farm_list.html"
    context_object_name = "farms"
    paginate_by = 20

    def get_queryset(self):
        qs = farms_for_user(self.request.user).distinct()
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(name__icontains=q)
        return qs


class FarmDetailView(UidUrlMixin, LoginRequiredMixin, DetailView):
    model = Farm
    template_name = "farms/farm_detail.html"

    def get_queryset(self):
        return farms_for_user(self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["pens"] = self.object.pens.all()
        ctx["batches"] = self.object.batches.all()[:10]
        return ctx


class FarmCreateView(RoleRequiredMixin, AuditCreateUpdateMixin, CreateView):
    allowed_roles = ("ADMIN", "OWNER")
    model = Farm
    form_class = FarmForm
    template_name = "farms/farm_form.html"
    success_url = reverse_lazy("farms:farm_list")


class FarmUpdateView(UidUrlMixin, RoleRequiredMixin, AuditCreateUpdateMixin, UpdateView):
    allowed_roles = ("ADMIN", "OWNER")
    model = Farm
    form_class = FarmForm
    template_name = "farms/farm_form.html"
    success_url = reverse_lazy("farms:farm_list")


class PenListView(LoginRequiredMixin, ListView):
    model = Pen
    template_name = "farms/pen_list.html"
    context_object_name = "pens"
    paginate_by = 25

    def get_queryset(self):
        allowed = farms_for_user(self.request.user)
        qs = Pen.objects.filter(farm__in=allowed).select_related("farm")
        farm = self.request.GET.get("farm")
        if farm:
            qs = qs.filter(farm__uid=farm)
        return qs


class PenDetailView(UidUrlMixin, LoginRequiredMixin, DetailView):
    model = Pen
    template_name = "farms/pen_detail.html"

    def get_queryset(self):
        return Pen.objects.filter(farm__in=farms_for_user(self.request.user))


class PenCreateView(RoleRequiredMixin, AuditCreateUpdateMixin, CreateView):
    allowed_roles = MANAGE
    model = Pen
    form_class = PenForm
    template_name = "farms/pen_form.html"
    success_url = reverse_lazy("farms:pen_list")


class PenUpdateView(UidUrlMixin, RoleRequiredMixin, AuditCreateUpdateMixin, UpdateView):
    allowed_roles = MANAGE
    model = Pen
    form_class = PenForm
    template_name = "farms/pen_form.html"
    success_url = reverse_lazy("farms:pen_list")


# -- Simple reference CRUD (breeds / suppliers / customers) ---------------
class _RefList(RoleRequiredMixin, ListView):
    allowed_roles = MANAGE
    paginate_by = 25


class BreedListView(_RefList):
    model = Breed
    template_name = "farms/breed_list.html"
    context_object_name = "breeds"


class BreedCreateView(RoleRequiredMixin, AuditCreateUpdateMixin, CreateView):
    allowed_roles = MANAGE
    model = Breed
    form_class = BreedForm
    template_name = "farms/simple_form.html"
    success_url = reverse_lazy("farms:breed_list")
    extra_context = {"object_label": "Breed"}


class BreedUpdateView(UidUrlMixin, RoleRequiredMixin, AuditCreateUpdateMixin, UpdateView):
    allowed_roles = MANAGE
    model = Breed
    form_class = BreedForm
    template_name = "farms/simple_form.html"
    success_url = reverse_lazy("farms:breed_list")
    extra_context = {"object_label": "Breed"}


class SupplierListView(_RefList):
    model = Supplier
    template_name = "farms/supplier_list.html"
    context_object_name = "suppliers"


class SupplierCreateView(RoleRequiredMixin, AuditCreateUpdateMixin, CreateView):
    allowed_roles = MANAGE
    model = Supplier
    form_class = SupplierForm
    template_name = "farms/simple_form.html"
    success_url = reverse_lazy("farms:supplier_list")
    extra_context = {"object_label": "Supplier"}


class SupplierUpdateView(UidUrlMixin, RoleRequiredMixin, AuditCreateUpdateMixin, UpdateView):
    allowed_roles = MANAGE
    model = Supplier
    form_class = SupplierForm
    template_name = "farms/simple_form.html"
    success_url = reverse_lazy("farms:supplier_list")
    extra_context = {"object_label": "Supplier"}


class CustomerListView(_RefList):
    model = Customer
    template_name = "farms/customer_list.html"
    context_object_name = "customers"


class CustomerCreateView(RoleRequiredMixin, AuditCreateUpdateMixin, CreateView):
    allowed_roles = MANAGE
    model = Customer
    form_class = CustomerForm
    template_name = "farms/simple_form.html"
    success_url = reverse_lazy("farms:customer_list")
    extra_context = {"object_label": "Customer"}


class CustomerUpdateView(UidUrlMixin, RoleRequiredMixin, AuditCreateUpdateMixin, UpdateView):
    allowed_roles = MANAGE
    model = Customer
    form_class = CustomerForm
    template_name = "farms/simple_form.html"
    success_url = reverse_lazy("farms:customer_list")
    extra_context = {"object_label": "Customer"}
