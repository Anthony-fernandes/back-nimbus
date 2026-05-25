from rest_framework import serializers
from .models import Project
from apps.clients.models import Client
from apps.users.models import User

class ProjectSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name", read_only=True)
    owner_name = serializers.CharField(source="owner.full_name_or_username", read_only=True)
    team_names = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = "__all__"
        extra_kwargs = {"company": {"required": False}}

    def get_team_names(self, obj):
        return [u.full_name_or_username for u in obj.team.all()]
