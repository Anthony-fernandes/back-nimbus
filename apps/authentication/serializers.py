from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from apps.users.serializers import UserSerializer

User = get_user_model()


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Allow login by email: if the username field looks like an email,
        # look up the actual username and substitute it before calling super().
        username_field = self.username_field  # typically "username"
        identifier = attrs.get(username_field, "")
        if "@" in identifier:
            try:
                user_obj = User.objects.get(email__iexact=identifier)
                attrs[username_field] = user_obj.username
            except User.DoesNotExist:
                pass  # let super() raise the standard invalid-credentials error

        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
