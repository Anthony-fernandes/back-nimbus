from rest_framework import serializers
from .models import Sprint, SprintActivityPlan

class SprintSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    lead_name = serializers.CharField(source="lead.full_name_or_username", read_only=True)

    class Meta:
        model = Sprint
        fields = "__all__"
        extra_kwargs = {"company": {"required": False, "read_only": True}}


class SprintActivityPlanSerializer(serializers.ModelSerializer):
    sprintId = serializers.UUIDField(source="sprint_id", read_only=True)
    activityId = serializers.UUIDField(source="activity_id", read_only=True)
    projectId = serializers.UUIDField(source="project_id", read_only=True)
    responsibleIds = serializers.ListField(source="responsible_ids", child=serializers.CharField(), read_only=True)
    plannedHours = serializers.DecimalField(source="planned_hours", max_digits=8, decimal_places=2, read_only=True)
    storyPoints = serializers.IntegerField(source="story_points", read_only=True)
    plannedStartDate = serializers.DateField(source="planned_start_date", read_only=True)
    plannedEndDate = serializers.DateField(source="planned_end_date", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = SprintActivityPlan
        fields = [
            "id",
            "sprint",
            "activity",
            "project",
            "responsible_ids",
            "planned_hours",
            "story_points",
            "planned_start_date",
            "planned_end_date",
            "order",
            "notes",
            "sprintId",
            "activityId",
            "projectId",
            "responsibleIds",
            "plannedHours",
            "storyPoints",
            "plannedStartDate",
            "plannedEndDate",
            "createdAt",
            "updatedAt",
        ]
        extra_kwargs = {
            "sprint": {"write_only": True},
            "activity": {"write_only": True},
            "project": {"write_only": True, "required": False, "allow_null": True},
            "responsible_ids": {"write_only": True, "required": False},
            "planned_hours": {"write_only": True},
            "story_points": {"write_only": True, "required": False, "allow_null": True},
            "planned_start_date": {"write_only": True, "required": False, "allow_null": True},
            "planned_end_date": {"write_only": True, "required": False, "allow_null": True},
        }


from apps.sprints.models import SprintRetrospective, SprintReview


class SprintRetrospectiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = SprintRetrospective
        fields = "__all__"
        extra_kwargs = {
            "company": {"required": False, "read_only": True},
            "created_by": {"required": False, "read_only": True},
        }


class SprintReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = SprintReview
        fields = "__all__"
        extra_kwargs = {
            "company": {"required": False, "read_only": True},
            "created_by": {"required": False, "read_only": True},
        }
