from django.urls import path

from . import views

app_name = "vision"

urlpatterns = [
    path("", views.VisionResultListView.as_view(), name="result_list"),
    path("<uuid:uid>/", views.VisionResultDetailView.as_view(), name="result_detail"),
    path("<uuid:uid>/review/", views.VisionReviewView.as_view(), name="result_review"),
]
