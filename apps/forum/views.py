from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from common.access import normalize_user_role, user_has_any_permission
from common.viewsets import CompanyScopedModelViewSet
from .models import ForumCategory, ForumTopic, ForumReply
from .serializers import ForumCategorySerializer, ForumTopicSerializer, ForumReplySerializer


def _can_moderate_forum(user) -> bool:
    return user_has_any_permission(user, ["communication.moderate", "settings.edit"]) or \
        normalize_user_role(getattr(user, "role", None)) == "ADMIN"


class ForumCategoryViewSet(CompanyScopedModelViewSet):
    queryset = ForumCategory.objects.all()
    serializer_class = ForumCategorySerializer
    permission_classes = [IsAuthenticated]
    ordering_fields = "__all__"

    def _ensure_can_manage(self):
        if _can_moderate_forum(self.request.user):
            return
        raise PermissionDenied("Seu perfil nao pode alterar categorias do forum.")

    def perform_create(self, serializer):
        self._ensure_can_manage()
        super().perform_create(serializer)

    def perform_update(self, serializer):
        self._ensure_can_manage()
        serializer.save()

    def perform_destroy(self, instance):
        self._ensure_can_manage()
        instance.delete()


class ForumTopicViewSet(CompanyScopedModelViewSet):
    queryset = ForumTopic.objects.all()
    serializer_class = ForumTopicSerializer
    permission_classes = [IsAuthenticated]
    ordering_fields = "__all__"

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(title__icontains=search) | Q(content__icontains=search)
            )
        return qs

    def perform_create(self, serializer):
        serializer.save(
            company=self.request.user.company,
            author=self.request.user,
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views += 1
        instance.save(update_fields=["views", "updated_at"])
        serializer = self.get_serializer(instance)
        from rest_framework.response import Response
        return Response(serializer.data)


class ForumReplyViewSet(CompanyScopedModelViewSet):
    queryset = ForumReply.objects.all()
    serializer_class = ForumReplySerializer
    permission_classes = [IsAuthenticated]
    company_field_name = "topic__company"
    ordering_fields = "__all__"

    def get_queryset(self):
        user = self.request.user
        company = getattr(user, "company", None)
        if not company:
            return self.queryset.none()
        qs = self.queryset.filter(topic__company=company)
        topic_id = self.request.query_params.get("topic")
        if topic_id:
            qs = qs.filter(topic=topic_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
