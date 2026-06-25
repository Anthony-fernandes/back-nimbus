from rest_framework import serializers
from .models import Sprint, SprintActivityPlan, SprintParticipant, SprintRetrospective, SprintReview, SprintTicketPlan


class SprintSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project.name", read_only=True)
    lead_name = serializers.CharField(source="lead.full_name_or_username", read_only=True)
    total_capacity = serializers.SerializerMethodField(read_only=True)

    def get_total_capacity(self, obj):
        return obj.total_capacity

    class Meta:
        model = Sprint
        fields = "__all__"
        extra_kwargs = {"company": {"required": False, "read_only": True}}


class SprintActivityPlanSerializer(serializers.ModelSerializer):
    sprintId = serializers.UUIDField(source="sprint_id", read_only=True)
    activityId = serializers.UUIDField(source="activity_id", read_only=True)
    projectId = serializers.UUIDField(source="project_id", read_only=True)
    responsibleIds = serializers.ListField(source="responsible_ids", child=serializers.CharField(), read_only=True)
    userHours = serializers.DictField(source="user_hours", child=serializers.FloatField(), read_only=True)
    plannedHours = serializers.DecimalField(source="planned_hours", max_digits=8, decimal_places=2, read_only=True)
    storyPoints = serializers.IntegerField(source="story_points", read_only=True)
    plannedStartDate = serializers.DateField(source="planned_start_date", read_only=True)
    plannedEndDate = serializers.DateField(source="planned_end_date", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = SprintActivityPlan
        fields = [
            "id", "sprint", "activity", "project",
            "responsible_ids", "user_hours", "planned_hours", "story_points",
            "priority", "complexity", "planned_start_date", "planned_end_date",
            "order", "notes",
            "sprintId", "activityId", "projectId",
            "responsibleIds", "userHours", "plannedHours", "storyPoints",
            "plannedStartDate", "plannedEndDate", "createdAt", "updatedAt",
        ]
        extra_kwargs = {
            "sprint": {"write_only": True},
            "activity": {"write_only": True},
            "project": {"write_only": True, "required": False, "allow_null": True},
            "responsible_ids": {"write_only": True, "required": False},
            "user_hours": {"write_only": True, "required": False},
            "planned_hours": {"write_only": True},
            "story_points": {"write_only": True, "required": False, "allow_null": True},
            "priority": {"required": False},
            "complexity": {"required": False, "allow_null": True},
            "planned_start_date": {"write_only": True, "required": False, "allow_null": True},
            "planned_end_date": {"write_only": True, "required": False, "allow_null": True},
        }


class SprintTicketPlanSerializer(serializers.ModelSerializer):
    sprintId = serializers.UUIDField(source="sprint_id", read_only=True)
    ticketId = serializers.UUIDField(source="ticket_id", read_only=True)
    responsibleIds = serializers.ListField(source="responsible_ids", child=serializers.CharField(), read_only=True)
    userHours = serializers.DictField(source="user_hours", child=serializers.FloatField(), read_only=True)
    plannedHours = serializers.DecimalField(source="planned_hours", max_digits=8, decimal_places=2, read_only=True)
    storyPoints = serializers.IntegerField(source="story_points", read_only=True)
    plannedEndDate = serializers.DateField(source="planned_end_date", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = SprintTicketPlan
        fields = [
            "id", "sprint", "ticket",
            "responsible_ids", "user_hours", "planned_hours", "story_points",
            "priority", "complexity", "planned_end_date", "notes",
            "sprintId", "ticketId", "responsibleIds", "userHours", "plannedHours", "storyPoints",
            "plannedEndDate", "createdAt", "updatedAt",
        ]
        extra_kwargs = {
            "sprint": {"write_only": True},
            "ticket": {"write_only": True},
            "responsible_ids": {"write_only": True, "required": False},
            "user_hours": {"write_only": True, "required": False},
            "planned_hours": {"write_only": True},
            "story_points": {"write_only": True, "required": False, "allow_null": True},
            "priority": {"required": False},
            "complexity": {"required": False, "allow_null": True},
            "planned_end_date": {"write_only": True, "required": False, "allow_null": True},
        }


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


class SprintParticipantSerializer(serializers.ModelSerializer):
    sprintId = serializers.UUIDField(source="sprint_id", read_only=True)
    userId = serializers.UUIDField(source="user_id", read_only=True)
    hoursPerDay = serializers.DecimalField(source="hours_per_day", max_digits=4, decimal_places=1, read_only=True)
    workingDays = serializers.IntegerField(source="working_days", read_only=True)
    availabilityFactor = serializers.DecimalField(source="availability_factor", max_digits=5, decimal_places=2, read_only=True)
    capacity = serializers.SerializerMethodField(read_only=True)
    userName = serializers.CharField(source="user.full_name_or_username", read_only=True)

    def get_capacity(self, obj):
        return obj.capacity

    class Meta:
        model = SprintParticipant
        fields = [
            "id", "sprint", "user",
            "hours_per_day", "working_days", "availability_factor",
            "sprintId", "userId", "hoursPerDay", "workingDays", "availabilityFactor",
            "capacity", "userName", "created_at",
        ]
        extra_kwargs = {
            "sprint": {"write_only": True},
            "user": {"write_only": True},
            "hours_per_day": {"write_only": True, "required": False},
            "working_days": {"write_only": True, "required": False},
            "availability_factor": {"write_only": True, "required": False},
        }
