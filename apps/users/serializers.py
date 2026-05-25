from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "name",
            "role",
            "job_title",
            "specialty",
            "phone",
            "total_hours",
            "used_hours",
            "hourly_cost",
            "technical_group",
            "permissions_json",
            "company",
            "password",
            "is_active",
        ]
        read_only_fields = ["id","name"]
        extra_kwargs = {"company": {"required": False}}

    def get_name(self, obj):
        return obj.full_name_or_username

    def create(self, validated_data):
        password = validated_data.pop("password", None) or "123456"
        user = User(**validated_data)
        if not user.username:
            user.username = user.email
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for k,v in validated_data.items():
            setattr(instance,k,v)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
