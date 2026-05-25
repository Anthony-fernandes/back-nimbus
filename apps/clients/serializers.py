from rest_framework import serializers
from .models import Client

class ClientSerializer(serializers.ModelSerializer):
    tickets = serializers.SerializerMethodField()
    projects = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = "__all__"
        extra_kwargs = {"company": {"required": False, "read_only": True}}

    def get_tickets(self, obj):
        return obj.tickets.count()

    def get_projects(self, obj):
        return obj.projects.count()
