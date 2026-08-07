from django.urls import path

from . import views

urlpatterns = [
    path("predict/", views.predict_view, name="predict"),
    path("history/", views.history_list_view, name="history-list"),
    path("history/<uuid:scan_id>/", views.history_detail_view, name="history-detail"),
    path("health/", views.health_view, name="health"),
]
