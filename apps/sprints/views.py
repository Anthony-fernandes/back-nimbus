from common.viewsets import CompanyScopedModelViewSet
from .models import Sprint, SprintActivityPlan
from .serializers import SprintSerializer, SprintActivityPlanSerializer

class SprintViewSet(CompanyScopedModelViewSet):
    queryset = Sprint.objects.all()
    serializer_class = SprintSerializer
    filterset_fields = ["company","project","status","lead"]
    search_fields = ["name","goal","project__name"]
    ordering_fields = "__all__"


class SprintActivityPlanViewSet(CompanyScopedModelViewSet):
    queryset = SprintActivityPlan.objects.all()
    serializer_class = SprintActivityPlanSerializer
    filterset_fields = ["sprint", "activity", "project"]
    search_fields = ["notes"]
    ordering_fields = "__all__"
