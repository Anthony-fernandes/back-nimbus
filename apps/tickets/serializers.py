from rest_framework import serializers
from .models import Ticket, TicketCategory, TicketWorkflowStatus

class TicketSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    technician_names = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = "__all__"
        extra_kwargs = {"company": {"required": False, "read_only": True}}

    def get_technician_names(self, obj):
        return [u.full_name_or_username for u in obj.technicians.all()]


class TicketCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketCategory
        fields = "__all__"
        extra_kwargs = {"company": {"required": False, "read_only": True}}


class TicketWorkflowStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketWorkflowStatus
        fields = "__all__"
        extra_kwargs = {"company": {"required": False, "read_only": True}}
