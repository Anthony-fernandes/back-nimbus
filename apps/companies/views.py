from common.permissions import IsAdminOrManager
from rest_framework.viewsets import ModelViewSet
from .models import Company
from .serializers import CompanySerializer

class CompanyViewSet(ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAdminOrManager]
    filterset_fields = ["is_active"]
    search_fields = ["name","document","email"]
    ordering_fields = "__all__"

    def get_queryset(self):
        company = getattr(self.request.user, "company", None)
        if not company:
            return Company.objects.none()
        return Company.objects.filter(id=company.id)
