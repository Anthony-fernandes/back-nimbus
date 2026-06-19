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

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        allowed = {"first_name", "last_name", "email", "phone", "job_title"}
        data = {k: v for k, v in request.data.items() if k in allowed}
        user = request.user
        for field, value in data.items():
            setattr(user, field, value)
        user.save(update_fields=list(data.keys()))
        return Response(UserSerializer(user).data)

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
        email = request.data.get("email")
        if not email:
            return Response({"error": "email is required."}, status=400)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Do not reveal whether user exists
            return Response({"detail": "Se o e-mail existir, as instruções foram enviadas."})
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        return Response({"uid": uid, "token": token})


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
