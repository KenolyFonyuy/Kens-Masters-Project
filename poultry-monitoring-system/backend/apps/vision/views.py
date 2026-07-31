"""Vision-result browsing and the human prediction-review workflow."""
from apps.core.mixins import RoleRequiredMixin, UidUrlMixin
from apps.farms.services import farms_for_user
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import DetailView, ListView, View

from .class_mapping import known_classes
from .models import VisionResult

REVIEW_ROLES = ("ADMIN", "OWNER", "MANAGER", "VET")


class VisionResultListView(LoginRequiredMixin, ListView):
    model = VisionResult
    template_name = "vision/result_list.html"
    context_object_name = "results"
    paginate_by = 30

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .filter(farm__in=farms_for_user(self.request.user))
            .select_related("farm", "pen", "device")
        )
        status = self.request.GET.get("review_status")
        if status:
            qs = qs.filter(review_status=status)
        predicted = self.request.GET.get("predicted_class")
        if predicted:
            qs = qs.filter(predicted_class=predicted)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["review_statuses"] = VisionResult.ReviewStatus.choices
        ctx["classes"] = known_classes()
        return ctx


class VisionResultDetailView(UidUrlMixin, LoginRequiredMixin, DetailView):
    model = VisionResult
    slug_field = "result_uuid"
    slug_url_kwarg = "uid"
    template_name = "vision/result_detail.html"

    def get_queryset(self):
        return super().get_queryset().filter(farm__in=farms_for_user(self.request.user))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["classes"] = known_classes()
        ctx["review_statuses"] = VisionResult.ReviewStatus.choices
        ctx["can_review"] = (
            self.request.user.has_any_role(REVIEW_ROLES) or self.request.user.is_superuser
        )
        return ctx


class VisionReviewView(RoleRequiredMixin, View):
    """Record a human review WITHOUT overwriting the original machine output."""

    allowed_roles = REVIEW_ROLES

    def post(self, request, uid):
        result = get_object_or_404(
            VisionResult.objects.filter(farm__in=farms_for_user(request.user)),
            result_uuid=uid,
        )
        decision = request.POST.get("decision")
        notes = request.POST.get("review_notes", "")
        corrected = request.POST.get("corrected_class", "")

        mapping = {
            "accept": VisionResult.ReviewStatus.ACCEPTED,
            "correct": VisionResult.ReviewStatus.CORRECTED,
            "uncertain": VisionResult.ReviewStatus.UNCERTAIN,
            "false": VisionResult.ReviewStatus.FALSE,
            "escalate": VisionResult.ReviewStatus.ESCALATED,
        }
        new_status = mapping.get(decision)
        if not new_status:
            messages.error(request, "Unknown review decision.")
            return redirect("vision:result_detail", uid=uid)

        # Original predicted_class/confidence/detections are never modified.
        result.review_status = new_status
        result.review_notes = notes
        result.reviewed_by = request.user
        result.reviewed_at = timezone.now()
        if new_status == VisionResult.ReviewStatus.CORRECTED and corrected:
            result.corrected_class = corrected
        result.save(
            update_fields=[
                "review_status", "review_notes", "reviewed_by",
                "reviewed_at", "corrected_class",
            ]
        )

        # Optionally create a linked health observation when escalating.
        if decision == "escalate" and result.batch_id:
            from apps.health.models import HealthObservation

            HealthObservation.objects.create(
                batch=result.batch,
                pen=result.pen,
                title=f"Escalated vision alert: {result.effective_class}",
                symptoms=notes,
                severity=HealthObservation.Severity.MODERATE,
                vision_result=result,
            )
            messages.info(request, "A health observation was created from this case.")

        messages.success(request, "Review recorded. Original prediction preserved.")
        return redirect("vision:result_detail", uid=uid)
