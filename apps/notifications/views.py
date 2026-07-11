from django.utils import timezone
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from common.viewsets import CompanyScopedModelViewSet

from .models import EmailTemplate, Notification, NotificationPreference
from .serializers import EmailTemplateSerializer, NotificationPreferenceSerializer, NotificationSerializer


class NotificationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    """Caixa de entrada interna do usuario autenticado."""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["category", "origin", "event", "is_read", "is_favorite", "is_archived"]
    search_fields = ["title", "message", "actor_name"]
    ordering_fields = "__all__"

    def get_queryset(self):
        user = self.request.user
        if not getattr(user, "pk", None):
            return Notification.objects.none()
        return Notification.objects.filter(recipient=user)

    def _set_flags(self, notification, **flags):
        update_fields = []
        for field, value in flags.items():
            setattr(notification, field, value)
            update_fields.append(field)
        update_fields.append("updated_at")
        notification.save(update_fields=update_fields)
        return notification

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        notification = self._set_flags(self.get_object(), is_read=True, read_at=timezone.now())
        return Response(self.get_serializer(notification).data)

    @action(detail=True, methods=["post"])
    def unread(self, request, pk=None):
        notification = self._set_flags(self.get_object(), is_read=False, read_at=None)
        return Response(self.get_serializer(notification).data)

    @action(detail=True, methods=["post"])
    def favorite(self, request, pk=None):
        value = bool(request.data.get("value", True))
        notification = self._set_flags(self.get_object(), is_favorite=value)
        return Response(self.get_serializer(notification).data)

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        value = bool(request.data.get("value", True))
        notification = self._set_flags(self.get_object(), is_archived=value)
        return Response(self.get_serializer(notification).data)

    @action(detail=False, methods=["post"], url_path="read-all")
    def read_all(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True, read_at=timezone.now())
        return Response({"status": "ok"})

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False, is_archived=False).count()
        return Response({"count": count})


class NotificationPreferenceView(APIView):
    """Leitura/atualizacao das preferencias do usuario autenticado."""

    permission_classes = [IsAuthenticated]

    def _get_preference(self, request):
        preference, _ = NotificationPreference.objects.get_or_create(
            user=request.user,
            defaults={"company": getattr(request.user, "company", None)},
        )
        return preference

    def get(self, request):
        return Response(NotificationPreferenceSerializer(self._get_preference(request)).data)

    def patch(self, request):
        preference = self._get_preference(request)
        serializer = NotificationPreferenceSerializer(preference, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def put(self, request):
        return self.patch(request)


class EmailTemplateViewSet(CompanyScopedModelViewSet):
    serializer_class = EmailTemplateSerializer

    def get_queryset(self):
        return EmailTemplate.objects.filter(company=self.request.user.company, deleted_at__isnull=True)

    def _ensure_can_manage(self):
        from common.access import user_has_any_permission
        from rest_framework.exceptions import PermissionDenied
        if user_has_any_permission(self.request.user, ["settings.edit"]):
            return
        raise PermissionDenied("Seu perfil nao pode alterar templates de e-mail.")

    def perform_create(self, serializer):
        self._ensure_can_manage()
        super().perform_create(serializer)

    def perform_update(self, serializer):
        self._ensure_can_manage()
        serializer.save()

    def perform_destroy(self, instance):
        self._ensure_can_manage()
        instance.delete()

    @action(detail=False, methods=["get"], url_path="available-events")
    def available_events(self, request):
        from apps.notifications.email_templates import DEFAULT_EMAIL_TEMPLATES, EVENT_LABEL
        return Response([
            {"event": k, "label": EVENT_LABEL.get(k, k), "default_subject": v["subject"], "default_body": v["body"]}
            for k, v in DEFAULT_EMAIL_TEMPLATES.items()
        ])

    @action(detail=True, methods=["post"], url_path="test")
    def send_test(self, request, pk=None):
        template = self.get_object()
        from django.core.mail import send_mail
        import logging
        logger = logging.getLogger(__name__)
        email = request.data.get("email") or request.user.email
        try:
            send_mail(
                subject=f"[Teste] {template.subject or template.event}",
                message=template.body or "(sem conteúdo)",
                html_message=template.body if template.body else None,
                from_email=None,
                recipient_list=[email],
                fail_silently=False,
            )
            return Response({"status": "sent", "to": email})
        except Exception as exc:
            logger.warning("Test email failed: %s", exc)
            return Response({"detail": str(exc)}, status=500)
