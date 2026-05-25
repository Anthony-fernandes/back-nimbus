from rest_framework import serializers
from .models import Activity, ActivityTag, ActivityTimeEntry

class ActivitySerializer(serializers.ModelSerializer):
    assignee_name = serializers.CharField(source="assignee.full_name_or_username", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    sprint_name = serializers.CharField(source="sprint.name", read_only=True)
    ticket_code = serializers.CharField(source="ticket.code", read_only=True)

    class Meta:
        model = Activity
        fields = "__all__"
        extra_kwargs = {"company": {"required": False, "read_only": True}}


class ActivityTagSerializer(serializers.ModelSerializer):
    usage_count = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = ActivityTag
        fields = [
            "id",
            "name",
            "color",
            "description",
            "active",
            "usage_count",
            "createdAt",
            "updatedAt",
        ]

    def get_usage_count(self, obj):
        return sum(
            1
            for activity in Activity.objects.filter(company=obj.company).only("tags")
            if obj.name in (activity.tags or [])
        )


class ActivityTimeEntrySerializer(serializers.ModelSerializer):
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)
    activityId = serializers.UUIDField(source="activity_id", read_only=True)
    sprintId = serializers.UUIDField(source="sprint_id", read_only=True)
    projectId = serializers.UUIDField(source="project_id", read_only=True)
    collaboratorId = serializers.UUIDField(source="collaborator_id", read_only=True)
    collaboratorName = serializers.CharField(source="collaborator_name", read_only=True)
    workDescription = serializers.CharField(source="work_description", read_only=True)
    generatedCostId = serializers.CharField(source="generated_cost_id", read_only=True)

    class Meta:
        model = ActivityTimeEntry
        fields = [
            "id",
            "activity",
            "sprint",
            "project",
            "collaborator",
            "collaborator_name",
            "date",
            "hours",
            "work_description",
            "generated_cost_id",
            "activityId",
            "sprintId",
            "projectId",
            "collaboratorId",
            "collaboratorName",
            "workDescription",
            "generatedCostId",
            "createdAt",
            "updatedAt",
        ]
        extra_kwargs = {
            "activity": {"write_only": True},
            "sprint": {"write_only": True, "required": False, "allow_null": True},
            "project": {"write_only": True, "required": False, "allow_null": True},
            "collaborator": {"write_only": True, "required": False, "allow_null": True},
            "collaborator_name": {"write_only": True, "required": False},
            "work_description": {"write_only": True, "required": False},
            "generated_cost_id": {"write_only": True, "required": False},
        }
