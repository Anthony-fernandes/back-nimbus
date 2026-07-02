import csv
import io
import logging
from datetime import timedelta, date as date_type

from django.db.models import Avg, Count, F, Q

logger = logging.getLogger(__name__)
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
            except Exception as exc:
                logger.warning("Invalid date_from param %r: %s", date_from_str, exc)
        if date_to_str:
            try:
                from django.utils.dateparse import parse_date
                d = parse_date(date_to_str)
                if d:
                    date_to = timezone.make_aware(timezone.datetime.combine(d, timezone.datetime.max.time()))
            except Exception as exc:
                logger.warning("Invalid date_to param %r: %s", date_to_str, exc)

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
            .values("responsible_technician__username", "responsible_technician__first_name", "responsible_technician__last_name", "responsible_technician_id")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        # Normalise technician display name for the frontend key it expects
        for row in by_technician:
            fn = row.pop("responsible_technician__first_name", "") or ""
            ln = row.pop("responsible_technician__last_name", "") or ""
            un = row.pop("responsible_technician__username", "") or ""
            row["responsible_technician__name"] = (f"{fn} {ln}".strip()) or un

        total = qs.count()
        finished = qs.filter(status__in=["Finalizado", "Cancelado"]).count()

        # Weekly breakdown — group by ISO week
        from django.db.models.functions import TruncWeek
        weekly_raw = (
            qs.annotate(week=TruncWeek("created_at"))
            .values("week")
            .annotate(total=Count("id"))
            .order_by("week")
        )
        weekly_finished_raw = (
            qs.filter(status__in=["Finalizado", "Cancelado"])
            .annotate(week=TruncWeek("created_at"))
            .values("week")
            .annotate(total=Count("id"))
            .order_by("week")
        )
        finished_by_week = {r["week"]: r["total"] for r in weekly_finished_raw}
        by_date = [
            {
                "semana": r["week"].strftime("Sem %d/%m") if r["week"] else "",
                "Abertos": r["total"],
                "Finalizados": finished_by_week.get(r["week"], 0),
            }
            for r in weekly_raw
        ]

        # Average resolution time (hours) for finished tickets
        finished_qs = qs.filter(status__in=["Finalizado", "Cancelado"], finished_at__isnull=False)
        avg_res = finished_qs.aggregate(avg=Avg(F("finished_at") - F("created_at")))["avg"]
        avg_resolution_hours = round(avg_res.total_seconds() / 3600, 1) if avg_res else None

        # SLA met rate
        sla_qs = qs.filter(sla_due_at__isnull=False)
        sla_total = sla_qs.count()
        sla_met = sla_qs.filter(
            Q(finished_at__isnull=False, finished_at__lte=F("sla_due_at")) |
            Q(finished_at__isnull=True, sla_due_at__gte=timezone.now())
        ).count()
        sla_met_rate = round(sla_met / sla_total * 100, 1) if sla_total else None

        reopened_count = qs.filter(reopen_count__gt=0).count()
        reopen_rate = round(reopened_count / total * 100, 1) if total else 0
        avg_reopens_agg = qs.filter(reopen_count__gt=0).aggregate(avg=Avg("reopen_count"))["avg"]
        avg_reopens = round(float(avg_reopens_agg), 2) if avg_reopens_agg else 0

        avg_csat_agg = qs.filter(rating__isnull=False).aggregate(avg=Avg("rating"))["avg"]
        avg_csat = round(float(avg_csat_agg), 2) if avg_csat_agg else None

        data = {
            "total": total,
            "finished": finished,
            "open": total - finished,
            "avg_resolution_time_hours": avg_resolution_hours,
            "sla_met_rate": sla_met_rate,
            "reopen_count": reopened_count,
            "reopen_rate": reopen_rate,
            "avg_reopens": avg_reopens,
            "avg_csat": avg_csat,
            "by_status": by_status,
            "by_priority": by_priority,
            "by_category": by_category,
            "by_technician": by_technician,
            "by_date": by_date,
        }

        rows = list(qs.values("code", "title", "status", "priority", "category", "created_at", "finished_at", "sla_due_at", "rating"))
        if export == "csv":
            return self._csv_response(rows, "relatorio_chamados.csv")
        if export == "excel":
            return self._excel_response(rows, "relatorio_chamados.xlsx")

        return Response(data)

    def _sla_report(self, request, company, date_from, date_to, export):
        from apps.tickets.models import Ticket
        qs = Ticket.objects.filter(company=company, created_at__gte=date_from, created_at__lte=date_to, deleted_at__isnull=True, sla_due_at__isnull=False)

        now = timezone.now()
        total = qs.count()
        breached = qs.filter(sla_due_at__lt=now).exclude(status__in=["Finalizado", "Cancelado"]).count()
        breached_finished = qs.filter(
            Q(finished_at__isnull=False) & Q(finished_at__gt=F("sla_due_at"))
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
        if export == "excel":
            return self._excel_response(tickets, "relatorio_sla.xlsx")

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
        if export == "excel":
            return self._excel_response(tickets, "relatorio_avaliacoes.xlsx")

        return Response(data)

    def _activities_report(self, request, company, date_from, date_to, export):
        from apps.activities.models import Activity
        qs = Activity.objects.filter(company=company, created_at__gte=date_from, created_at__lte=date_to, deleted_at__isnull=True)
        by_status = list(qs.values("status").annotate(count=Count("id")).order_by("-count"))
        by_project = list(qs.values("project__name").annotate(count=Count("id")).order_by("-count")[:10])
        total_hours = qs.aggregate(h=Count("id"))["h"]
        data = {"total": qs.count(), "by_status": by_status, "by_project": by_project}

        rows = list(qs.values("title", "status", "project__name", "assignee__first_name", "assignee__last_name", "created_at", "due_at")[:500])
        if export == "csv":
            return self._csv_response(rows, "relatorio_atividades.csv")
        if export == "excel":
            return self._excel_response(rows, "relatorio_atividades.xlsx")

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

    def _excel_response(self, rows: list[dict], filename: str) -> HttpResponse:
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment
        except ImportError:
            return HttpResponse("openpyxl não instalado.", status=500)

        if not rows:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.append(["Sem dados"])
        else:
            wb = openpyxl.Workbook()
            ws = wb.active
            headers = list(rows[0].keys())
            ws.append(headers)
            # Style header row
            for cell in ws[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor="1E293B")
                cell.alignment = Alignment(horizontal="center")
            for row in rows:
                ws.append([str(v) if v is not None else "" for v in row.values()])
            # Auto-fit columns
            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 40)

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
