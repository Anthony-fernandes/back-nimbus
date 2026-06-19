from django.db.models import Q
from rest_framework.permissions import IsAuthenticated

from common.viewsets import CompanyScopedModelViewSet
from .models import ForumCategory, ForumTopic, ForumReply
from .serializers import ForumCategorySerializer, ForumTopicSerializer, ForumReplySerializer


class ForumCategoryViewSet(CompanyScopedModelViewSet):
    queryset = ForumCategory.objects.all()
    serializer_class = ForumCategorySerializer
    permission_classes = [IsAuthenticated]
    ordering_fields = "__all__"


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
