from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tickets.models import Ticket
from apps.knowledge.models import KnowledgeArticle
from apps.projects.models import Project

# Fórum e Dúvidas moram em apps.communication (as apps forum/doubts eram duplicatas mortas).
try:
    from apps.communication.models import ForumTopic
    _has_forum = True
except ImportError:
    _has_forum = False

try:
    from apps.communication.models import DoubtsQuestion
    _has_doubts = True
except ImportError:
    _has_doubts = False


class GlobalSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "").strip()

        if len(query) < 2:
            return Response({"results": [], "query": query})

        company = request.user.company
        results = []

        # Tickets
        tickets = Ticket.objects.filter(
            company=company,
            deleted_at__isnull=True,
        ).filter(
            Q(title__icontains=query) | Q(description__icontains=query) | Q(code__icontains=query)
        )[:10]

        for t in tickets:
            results.append({
                "type": "ticket",
                "id": t.id,
                "title": t.title,
                "subtitle": t.code,
                "url": f"/tickets/{t.id}",
                "status": t.status,
            })

        # KnowledgeArticle
        articles = KnowledgeArticle.objects.filter(
            company=company,
            deleted_at__isnull=True,
            status="PUBLISHED",
        ).filter(
            Q(title__icontains=query) | Q(content__icontains=query) | Q(summary__icontains=query)
        )[:8]

        for a in articles:
            results.append({
                "type": "knowledge",
                "id": a.id,
                "title": a.title,
                "subtitle": a.category.name if a.category else "Base de Conhecimento",
                "url": f"/knowledge/{a.id}",
                "status": None,
            })

        # ForumTopic
        if _has_forum:
            topics = ForumTopic.objects.filter(
                company=company,
                deleted_at__isnull=True,
            ).filter(
                Q(title__icontains=query) | Q(content__icontains=query)
            )[:6]

            for t in topics:
                results.append({
                    "type": "forum",
                    "id": t.id,
                    "title": t.title,
                    "subtitle": "Fórum",
                    "url": f"/forum/{t.id}",
                    "status": None,
                })

        # DoubtsQuestion
        if _has_doubts:
            questions = DoubtsQuestion.objects.filter(
                company=company,
                deleted_at__isnull=True,
            ).filter(
                Q(title__icontains=query) | Q(content__icontains=query)
            )[:6]

            for q_obj in questions:
                results.append({
                    "type": "doubt",
                    "id": q_obj.id,
                    "title": q_obj.title,
                    "subtitle": "Central de Dúvidas",
                    "url": f"/doubts/{q_obj.id}",
                    "status": None,
                })

        # Project
        projects = Project.objects.filter(
            company=company,
            deleted_at__isnull=True,
        ).filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )[:5]

        for p in projects:
            results.append({
                "type": "project",
                "id": p.id,
                "title": p.name,
                "subtitle": "Projeto",
                "url": f"/projects/{p.id}",
                "status": None,
            })

        return Response({"results": results, "query": query})
