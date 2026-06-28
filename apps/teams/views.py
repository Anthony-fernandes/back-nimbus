from rest_framework.permissions import IsAuthenticated

from common.viewsets import CompanyScopedModelViewSet
from .models import Team, TeamMember
from .serializers import TeamSerializer, TeamMemberSerializer


class TeamViewSet(CompanyScopedModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["company", "status", "leader"]
    search_fields = ["name", "description"]
    ordering_fields = "__all__"


class TeamMemberViewSet(CompanyScopedModelViewSet):
    queryset = TeamMember.objects.all()
    serializer_class = TeamMemberSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["company", "team", "user"]
    search_fields = ["role"]
    ordering_fields = "__all__"

    def perform_create(self, serializer):
        team = serializer.validated_data.get("team")
        company = getattr(self.request.user, "company", None)
        kwargs = {}
        if company:
            kwargs["company"] = company
        if not kwargs.get("company") and team:
            kwargs["company"] = team.company
        serializer.save(**kwargs)
