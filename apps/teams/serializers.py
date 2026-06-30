from rest_framework import serializers
from .models import Team, TeamMember


class TeamMemberSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = TeamMember
        fields = ["id", "team", "user", "user_name", "user_email", "role", "default_hours_per_day", "default_capacity", "created_at"]
        read_only_fields = ["id", "user_name", "user_email", "created_at"]
        extra_kwargs = {
            "team": {"required": False},
        }


class TeamSerializer(serializers.ModelSerializer):
    leader_name = serializers.CharField(source="leader.get_full_name", read_only=True)
    member_count = serializers.SerializerMethodField()
    members = TeamMemberSerializer(many=True, read_only=True)

    class Meta:
        model = Team
        fields = ["id", "name", "description", "leader", "leader_name", "status", "color", "icon", "default_capacity", "settings", "tipo", "parent", "clients", "member_count", "members", "created_at", "updated_at"]
        read_only_fields = ["id", "leader_name", "member_count", "members", "created_at", "updated_at"]
        extra_kwargs = {"company": {"required": False, "read_only": True}}

    def get_member_count(self, obj):
        return obj.members.count()
