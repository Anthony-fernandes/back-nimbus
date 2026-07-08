from django.urls import path

from .backlog_views import backlog_list, backlog_metrics

urlpatterns = [
    path("", backlog_list, name="backlog-list"),
    path("metrics/", backlog_metrics, name="backlog-metrics"),
]
