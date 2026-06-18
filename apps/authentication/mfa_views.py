import logging
import pyotp
from django.conf import settings
from django.core.cache import cache
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)

MFA_TOKEN_TTL = 300  # 5 minutes


def _mfa_cache_key(mfa_token: str) -> str:
    return f"mfa_login:{mfa_token}"


class MFASetupView(APIView):
    """GET: generate TOTP secret and QR URL for setup."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        secret = pyotp.random_base32()
        # Store temporarily in cache until confirmed
        cache.set(f"mfa_setup:{request.user.id}", secret, 600)

        app_name = getattr(settings, 'MFA_APP_NAME', 'Stratos Suite')
        totp = pyotp.TOTP(secret)
        qr_url = totp.provisioning_uri(
            name=request.user.email or request.user.username,
            issuer_name=app_name,
        )
        return Response({"secret": secret, "qr_url": qr_url})


class MFASetupConfirmView(APIView):
    """POST {totp_code}: verify and save MFA secret."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = str(request.data.get("totp_code", "")).strip()
        secret = cache.get(f"mfa_setup:{request.user.id}")

        if not secret:
            return Response(
                {"detail": "Sessão de configuração expirada. Inicie o processo novamente."},
                status=400,
            )

        totp = pyotp.TOTP(secret)
        if not totp.verify(code, valid_window=1):
            return Response(
                {"detail": "Código inválido. Verifique o aplicativo autenticador."},
                status=400,
            )

        user = request.user
        user.mfa_secret = secret
        user.mfa_enabled = True
        user.save(update_fields=["mfa_secret", "mfa_enabled", "updated_at"])
        cache.delete(f"mfa_setup:{request.user.id}")

        logger.info("MFA enabled for user %s", user.id)
        return Response({"detail": "Autenticação em dois fatores ativada com sucesso."})


class MFADisableView(APIView):
    """POST {totp_code}: disable MFA after verification."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if not user.mfa_enabled:
            return Response({"detail": "MFA não está ativo."}, status=400)

        code = str(request.data.get("totp_code", "")).strip()
        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(code, valid_window=1):
            return Response({"detail": "Código inválido."}, status=400)

        user.mfa_enabled = False
        user.mfa_secret = ""
        user.save(update_fields=["mfa_enabled", "mfa_secret", "updated_at"])

        logger.info("MFA disabled for user %s", user.id)
        return Response({"detail": "Autenticação em dois fatores desativada."})


class MFAVerifyLoginView(APIView):
    """POST {mfa_token, totp_code}: complete login after MFA challenge."""
    permission_classes = [AllowAny]

    def post(self, request):
        mfa_token = str(request.data.get("mfa_token", "")).strip()
        code = str(request.data.get("totp_code", "")).strip()

        if not mfa_token or not code:
            return Response({"detail": "Token e código são obrigatórios."}, status=400)

        user_id = cache.get(_mfa_cache_key(mfa_token))
        if not user_id:
            return Response(
                {"detail": "Token expirado ou inválido. Faça login novamente."},
                status=400,
            )

        from apps.users.models import User
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "Usuário não encontrado."}, status=400)

        if not user.mfa_enabled or not user.mfa_secret:
            return Response({"detail": "MFA não configurado."}, status=400)

        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(code, valid_window=1):
            return Response({"detail": "Código inválido ou expirado."}, status=400)

        cache.delete(_mfa_cache_key(mfa_token))

        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })


class MFAStatusView(APIView):
    """GET: check if MFA is enabled for current user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"mfa_enabled": request.user.mfa_enabled})
