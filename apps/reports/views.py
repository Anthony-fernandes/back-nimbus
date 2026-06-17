import csv
import io
from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class ReportsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        report_type = request.query_params.get("type", "tickets")
        company = request.user.company
        date_from_str = request.query_params.get("date_from")
        date_to_str = request.query_params.get("date_to")
        export = request.query_params.get("export", "")

        now = timezone.now()
        date_from = now - timedelta(days=30)
        date_to = now

        if date_from_str:
            try:
                from django.utils.dateparse import parse_date
                d = parse_date(date_from_str)
                if d:
                    date_from = timezone.make_aware(timezone.datetime.combine(d, timezone.datetime.min.time()))
            except Exception:
                pass
        if date_to_str:
            try:
                from django.utils.dateparse import parse_date
                d = parse_date(date_to_str)
                if d:
                    date_to = timezone.make_aware(timezone.datetime.combine(d, timezone.datetime.max.time()))
            except Exception:
                pass

        if report_type == "tickets":
            return self._tickets_report(request, company, date_from, date_to, export)
        if report_type == "sla":
            return self._sla_report(request, company, date_from, date_to, export)
        if report_type == "ratings":
            return self._ratings_report(request, company, date_from, date_to, export)
        if report_type == "activities":
            return self._activities_report(request, company, date_from, date_to, export)

        return Response({"detail": "Tipo de relatório inválido."}, status=400)

    def _tickets_report(self, request, company, date_from, date_to, export):
        from apps.tickets.models import Ticket
        qs = Ticket.objects.filter(company=company, created_at__gte=date_from, created_at__lte=date_to, deleted_at__isnull=True)

        by_status = list(qs.values("status").annotate(count=Count("id")).order_by("-count"))
        by_priority = list(qs.values("priority").annotate(count=Count("id")).order_by("-count"))
        by_category = list(qs.values("category").annotate(count=Count("id")).order_by("-count")[:10])
        by_technician = list(
            qs.exclude(responsible_technician__isnull=True)
            .values("responsible_technician__name", "responsible_technician_id")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        total = qs.count()
        finished = qs.filter(status__in=["Finalizado", "Cancelado"]).count()

        data = {
            "total": total,
            "finished": finished,
            "open": total - finished,
            "by_status": by_status,
            "by_priority": by_priority,
            "by_category": by_category,
            "by_technician": by_technician,
        }

        if export == "csv":
            rows = list(qs.values("code", "title", "status", "priority", "category", "created_at", "finished_at", "sla_due_at", "rating"))
            return self._csv_response(rows, "relatorio_chamados.csv")

        return Response(data)

    def _sla_report(self, request, company, date_from, date_to, export):
        from apps.tickets.models import Ticket
        qs = Ticket.objects.filter(company=company, created_at__gte=date_from, created_at__lte=date_to, deleted_at__isnull=True, sla_due_at__isnull=False)

        now = timezone.now()
        total = qs.count()
        breached = qs.filter(sla_due_at__lt=now).exclude(status__in=["Finalizado", "Cancelado"]).count()
        breached_finished = qs.filter(
            Q(finished_at__isnull=False) & Q(finished_at__gt=models_sla_due_at())
        ).count()

        # Tickets with SLA info for listing
        tickets = list(
            qs.order_by("sla_due_at").values(
                "id", "code", "title", "status", "priority", "sla_due_at", "finished_at",
                "responsible_technician__name"
            )[:100]
        )
        for t in tickets:
            due = t["sla_due_at"]
            fin = t.get("finished_at")
            if fin and due:
                t["sla_breached"] = fin > due
            elif due:
                t["sla_breached"] = now > due
            else:
                t["sla_breached"] = False

        data = {
            "total": total,
            "breached_open": breached,
            "on_time_rate": round((1 - breached / total) * 100, 1) if total else 100,
            "tickets": tickets,
        }

        if export == "csv":
            return self._csv_response(tickets, "relatorio_sla.csv")

        return Response(data)

    def _ratings_report(self, request, company, date_from, date_to, export):
        from apps.tickets.models import Ticket
        qs = Ticket.objects.filter(
            company=company, rated_at__gte=date_from, rated_at__lte=date_to,
            deleted_at__isnull=True, rating__isnull=False
        )
        avg = qs.aggregate(avg=Avg("rating"))["avg"]
        by_score = list(qs.values("rating").annotate(count=Count("id")).order_by("rating"))
        tickets = list(qs.values("code", "title", "rating", "rating_comment", "rated_at", "responsible_technician__name")[:100])
        data = {"total_rated": qs.count(), "average": round(avg or 0, 2), "by_score": by_score, "tickets": tickets}

        if export == "csv":
            return self._csv_response(tickets, "relatorio_avaliacoes.csv")

        return Response(data)

    def _activities_report(self, request, company, date_from, date_to, export):
        from apps.activities.models import Activity
        qs = Activity.objects.filter(company=company, created_at__gte=date_from, created_at__lte=date_to, deleted_at__isnull=True)
        by_status = list(qs.values("status").annotate(count=Count("id")).order_by("-count"))
        by_project = list(qs.values("project__name").annotate(count=Count("id")).order_by("-count")[:10])
        total_hours = qs.aggregate(h=Count("id"))["h"]
        data = {"total": qs.count(), "by_status": by_status, "by_project": by_project}

        if export == "csv":
            rows = list(qs.values("title", "status", "project__name", "assignee__name", "created_at", "due_date")[:500])
            return self._csv_response(rows, "relatorio_atividades.csv")

        return Response(data)

    def _csv_response(self, rows: list[dict], filename: str) -> HttpResponse:
        if not rows:
            response = HttpResponse("Sem dados", content_type="text/csv")
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
        response = HttpResponse(output.getvalue(), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


def models_sla_due_at():
    """Helper to reference field in Q filter."""
    from django.db.models import F
    return F("sla_due_at")


class SLAPolicyViewSet:
    pass  # defined in sla_views.py
