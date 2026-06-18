import secrets as _secrets
from django.core.cache import cache
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from apps.users.serializers import UserSerializer
from common.throttles import LoginRateThrottle
from .serializers import LoginSerializer


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
