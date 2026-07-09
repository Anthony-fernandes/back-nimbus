import secrets as _secrets
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import OpenApiResponse, extend_schema
from apps.users.serializers import UserSerializer
from common.throttles import LoginRateThrottle
from .serializers import LoginSerializer

User = get_user_model()


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    throttle_classes = [LoginRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user

        if getattr(user, 'mfa_enabled', False):
            mfa_token = _secrets.token_urlsafe(32)
            cache.set(f"mfa_login:{mfa_token}", str(user.id), 300)
            return Response({"mfa_required": True, "mfa_token": mfa_token})

        return Response(serializer.validated_data)

@extend_schema(tags=["auth"])
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Dados do usuário logado",
        description="Retorna o perfil do usuário autenticado (identificado pelo token JWT).",
        responses=UserSerializer,
    )
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    @extend_schema(
        summary="Atualizar meu perfil",
        description="Atualiza campos do próprio perfil: first_name, last_name, email, "
        "phone, job_title e theme_config.",
        request=UserSerializer,
        responses=UserSerializer,
    )
    def patch(self, request):
        allowed = {"first_name", "last_name", "email", "phone", "job_title", "theme_config"}
        data = {k: v for k, v in request.data.items() if k in allowed}
        user = request.user
        for field, value in data.items():
            setattr(user, field, value)
        user.save(update_fields=list(data.keys()))
        return Response(UserSerializer(user).data)

@extend_schema(
    tags=["auth"],
    summary="Alterar senha",
    description="Troca a senha do usuário logado; exige old_password e new_password.",
    request={"application/json": {"type": "object", "properties": {
        "old_password": {"type": "string"}, "new_password": {"type": "string"}}}},
    responses=OpenApiResponse(description="Senha alterada."),
)
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        if not old_password or not new_password:
            return Response({"error": "old_password and new_password are required."}, status=400)
        user = request.user
        if not user.check_password(old_password):
            return Response({"error": "Senha atual incorreta."}, status=400)
        user.set_password(new_password)
        user.save()
        return Response({"success": True})


class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from django.conf import settings as django_settings
        from django.core.mail import send_mail

        email = request.data.get("email")
        if not email:
            return Response({"error": "email is required."}, status=400)

        safe_response = Response({"detail": "Se o e-mail existir, as instruções foram enviadas."})

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return safe_response

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        frontend_url = getattr(django_settings, "FRONTEND_URL", "http://localhost:5173")
        reset_url = f"{frontend_url}/reset-password?uid={uid}&token={token}"

        try:
            send_mail(
                subject="Redefinição de senha",
                message=(
                    f"Olá {user.first_name or user.email},\n\n"
                    f"Clique no link abaixo para redefinir sua senha:\n{reset_url}\n\n"
                    "Se você não solicitou isso, ignore este e-mail."
                ),
                from_email=django_settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception:
            pass

        return safe_response


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        uid = request.data.get("uid")
        token = request.data.get("token")
        new_password = request.data.get("new_password")
        if not uid or not token or not new_password:
            return Response({"error": "uid, token and new_password are required."}, status=400)
        try:
            pk = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=pk)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Link inválido."}, status=400)
        if not default_token_generator.check_token(user, token):
            return Response({"error": "Token inválido ou expirado."}, status=400)
        user.set_password(new_password)
        user.save()
        return Response({"success": True})


@extend_schema(
    tags=["auth"],
    summary="Encerrar sessão (logout)",
    description="Invalida o refresh token informado (blacklist).",
    request={"application/json": {"type": "object", "properties": {"refresh": {"type": "string"}}}},
    responses=OpenApiResponse(description="Sessão encerrada."),
)
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        refresh = request.data.get("refresh")
        if refresh:
            try:
                RefreshToken(refresh).blacklist()
            except Exception:
                pass
        return Response({"success": True})
