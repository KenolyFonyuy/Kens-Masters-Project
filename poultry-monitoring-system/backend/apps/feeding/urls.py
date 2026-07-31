from django.urls import path

from . import views

app_name = "feeding"

urlpatterns = [
    path("", views.FeedUsageListView.as_view(), name="usage_list"),
    path("add/", views.FeedUsageCreateView.as_view(), name="usage_create"),
    path("types/", views.FeedTypeListView.as_view(), name="feedtype_list"),
    path("types/add/", views.FeedTypeCreateView.as_view(), name="feedtype_create"),
    path("types/<uuid:uid>/edit/", views.FeedTypeUpdateView.as_view(), name="feedtype_update"),
]
