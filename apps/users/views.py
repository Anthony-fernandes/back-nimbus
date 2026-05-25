from common.permissions import IsAdminOrManagerOrReadOnly
from common.viewsets import CompanyScopedModelViewSet
from .models import User
from .serializers import UserSerializer

class UserViewSet(CompanyScopedModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    filterset_fields = ["role","company","is_active"]
    search_fields = ["first_name","last_name","email","username","job_title","specialty"]
    ordering_fields = "__all__"
