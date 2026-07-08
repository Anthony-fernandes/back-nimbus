from django.urls import path

from .workitem_views import available_actions

urlpatterns = [
    path("<str:item_type>/<uuid:pk>/available-actions/", available_actions, name="workitem-available-actions"),
]
