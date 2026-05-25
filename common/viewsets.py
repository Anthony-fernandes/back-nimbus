from rest_framework.viewsets import ModelViewSet


class CompanyScopedModelViewSet(ModelViewSet):
    company_field_name = "company"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        company = getattr(user, "company", None)
        company_field_name = getattr(self, "company_field_name", "company")

        if not company or not company_field_name:
            return queryset.none()

        return queryset.filter(**{company_field_name: company})

    def perform_create(self, serializer):
        company_field_name = getattr(self, "company_field_name", "company")
        company = getattr(self.request.user, "company", None)

        if company_field_name and company and not serializer.validated_data.get(company_field_name):
            serializer.save(**{company_field_name: company})
            return

        serializer.save()
