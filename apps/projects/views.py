from common.viewsets import CompanyScopedModelViewSet
from .models import Project
from .serializers import ProjectSerializer

class ProjectViewSet(CompanyScopedModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    filterset_fields = ["company","client","status","owner"]
    search_fields = ["name","description","client__name"]
    ordering_fields = "__all__"
