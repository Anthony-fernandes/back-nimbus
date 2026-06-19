from common.permissions import IsAdminOrManager
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
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

    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request):
        company = request.user.company
        from apps.tickets.models import Ticket
        from apps.users.models import User
        return Response({
            "total_tickets": Ticket.objects.filter(company=company, deleted_at__isnull=True).count(),
            "total_members": User.objects.filter(company=company).count(),
            "open_tickets": Ticket.objects.filter(company=company, deleted_at__isnull=True, status__in=["Aberto", "Em atendimento", "Triagem"]).count(),
        })


class IsSuperAdmin(IsAuthenticated):
    def has_permission(self, request, view):
        return bool(
            super().has_permission(request, view)
            and (request.user.is_staff or request.user.is_superuser)
        )


class SuperAdminCompanyViewSet(ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsSuperAdmin]
    filterset_fields = ["is_active"]
    search_fields = ["name", "document", "email"]
    ordering_fields = "__all__"

    @action(detail=True, methods=["post"], url_path="setup-admin")
    def setup_admin(self, request, pk=None):
        from apps.users.models import User
        company = self.get_object()
        data = request.data
        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()

        if not username or not email or not password:
            return Response(
                {"detail": "username, email e password sao obrigatorios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"detail": f"Username '{username}' ja esta em uso."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            company=company,
            role="ADMIN",
        )
        return Response(
            {
                "id": str(user.pk),
                "username": user.username,
                "email": user.email,
                "company": str(company.pk),
                "role": user.role,
            },
            status=status.HTTP_201_CREATED,
        )
