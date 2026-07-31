from django.urls import path

from . import api_views

urlpatterns = [
    path("vision-results/", api_views.VisionResultView.as_view(), name="vision-results"),
]
