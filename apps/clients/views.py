from common.viewsets import CompanyScopedModelViewSet
from .models import Client
from .serializers import ClientSerializer

class ClientViewSet(CompanyScopedModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    filterset_fields = ["company","status","plan","health"]
    search_fields = ["name","email","phone","sector","contact_name"]
    ordering_fields = "__all__"
