from django.db import connection
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    checks = {}

    try:
        connection.ensure_connection()
        checks['database'] = 'ok'
    except Exception as exc:
        checks['database'] = f'error: {exc}'

    try:
        cache.set('health_check', 'ok', 5)
        checks['cache'] = 'ok' if cache.get('health_check') == 'ok' else 'miss'
    except Exception as exc:
        checks['cache'] = f'error: {exc}'

    status = 200 if all(v == 'ok' for v in checks.values()) else 503
    return Response({'status': 'ok' if status == 200 else 'degraded', 'checks': checks}, status=status)
