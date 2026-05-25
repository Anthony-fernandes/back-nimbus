from common.permissions import IsAdminOrManagerOrReadOnly
from common.viewsets import CompanyScopedModelViewSet
from .models import Activity, ActivityTag, ActivityTimeEntry
from .serializers import ActivitySerializer, ActivityTagSerializer, ActivityTimeEntrySerializer

class ActivityViewSet(CompanyScopedModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    filterset_fields = ["company","type","status","priority","assignee","project","sprint","ticket"]
    search_fields = ["title","description","project__name","ticket__code"]
    ordering_fields = "__all__"


class ActivityTagViewSet(CompanyScopedModelViewSet):
    queryset = ActivityTag.objects.all()
    serializer_class = ActivityTagSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    filterset_fields = ["active"]
    search_fields = ["name", "description"]
    ordering_fields = "__all__"


class ActivityTimeEntryViewSet(CompanyScopedModelViewSet):
    queryset = ActivityTimeEntry.objects.all()
    serializer_class = ActivityTimeEntrySerializer
    filterset_fields = ["activity", "sprint", "project", "collaborator"]
    search_fields = ["collaborator_name", "work_description"]
    ordering_fields = "__all__"
