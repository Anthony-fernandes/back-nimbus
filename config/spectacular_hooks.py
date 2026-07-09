"""Hooks de pré-processamento do schema OpenAPI (drf-spectacular)."""


def exclude_v1_duplicates(endpoints):
    """Remove as rotas duplicadas sob /api/v1/ — o frontend usa /api/.

    O projeto monta os mesmos viewsets em /api/ e /api/v1/ (compat.), o que
    duplicaria cada endpoint na documentação. Mantemos só a família /api/.
    """
    return [
        (path, path_regex, method, callback)
        for (path, path_regex, method, callback) in endpoints
        if not path.startswith("/api/v1/")
    ]
