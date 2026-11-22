"""Per-request Firestore operation counts: numbers only, never ids, paths or data.

The Firestore client funnels every operation through a small set of gapic methods, so counting
there covers repositories, services and helpers without touching them. Counts approximate the
billable operation categories; a query that returns no document is still billed one read by
Firestore and is not modelled here. Known limits: operations outside an HTTP request, in threads
that do not copy the context (e.g. BulkWriter) and after the request ended are not counted;
`execute_pipeline`, `partition_query`, `list_collection_ids` and the async client are not wrapped;
`batch_write` and aggregation queries are counted when the call is made/returns, even if parts fail.
"""
from contextvars import ContextVar

_counts = ContextVar("firestore_operation_counts", default=None)
KINDS = ("reads", "writes", "deletes", "aggregations")
WRAPPED_METHODS = ("run_query", "batch_get_documents", "get_document", "list_documents",
                   "run_aggregation_query", "commit", "batch_write")


def begin_counts():
    counts = dict.fromkeys(KINDS, 0)
    return counts, _counts.set(counts)


def end_counts(token):
    _counts.reset(token)


def _add(kind, amount=1):
    try:
        counts = _counts.get()
        if counts is not None and amount:
            counts[kind] += amount
    except Exception:
        pass  # Observability must never change an application result.


def _named(row, attribute):
    value = getattr(row, attribute, None)
    return bool(getattr(value, "name", "") or (value if isinstance(value, str) else ""))


class _Counted:
    """Iterator proxy that counts items as they are consumed and keeps the stream API."""

    def __init__(self, stream, count):
        self._stream = stream
        self._count = count
        self._items = iter(stream)

    def __iter__(self):
        return self

    def __next__(self):
        item = next(self._items)
        try:
            self._count(item)
        except Exception:
            pass
        return item

    def __getattr__(self, name):
        return getattr(self._stream, name)


def _is_delete(write):
    value = write.get("delete") if isinstance(write, dict) else getattr(write, "delete", "")
    return bool(value)


def _count_writes(args, kwargs):
    request = kwargs.get("request", args[0] if args else None)
    writes = kwargs.get("writes")
    if writes is None and request is not None:
        writes = request.get("writes") if isinstance(request, dict) else getattr(request, "writes", None)
    for write in writes or ():
        _add("deletes" if _is_delete(write) else "writes")


def _wrap(name, method):
    if name == "run_query":
        return lambda *a, **k: _Counted(method(*a, **k), lambda r: _add("reads") if _named(r, "document") else None)
    if name == "batch_get_documents":
        return lambda *a, **k: _Counted(method(*a, **k), lambda r: _add("reads") if (
            _named(r, "found") or _named(r, "missing")) else None)
    if name == "list_documents":
        return lambda *a, **k: _Counted(method(*a, **k), lambda _: _add("reads"))

    def wrapper(*args, **kwargs):
        result = method(*args, **kwargs)
        try:
            if name == "get_document":
                _add("reads")
            elif name == "run_aggregation_query":
                _add("aggregations")
            else:
                _count_writes(args, kwargs)  # commit / batch_write, only after success
        except Exception:
            pass
        return result

    return wrapper


def install_firestore_counters(client):
    """Wrap the client's gapic methods once. Returns False if the client is not compatible."""
    try:
        api = client._firestore_api
        if getattr(api, "_mcp_operation_counters", False):
            return True
        for name in WRAPPED_METHODS:
            setattr(api, name, _wrap(name, getattr(api, name)))
        api._mcp_operation_counters = True
        return True
    except Exception:
        return False
