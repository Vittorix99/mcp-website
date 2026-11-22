import importlib
import json
from types import SimpleNamespace as NS

from flask import Flask, request
import pytest


def _module():
    try:
        return importlib.import_module("utils.firestore_observability")
    except ModuleNotFoundError as error:
        if error.name != "utils.firestore_observability":
            raise
        pytest.fail("Firestore operation counters not implemented")


def _doc(name="projects/p/databases/(default)/documents/c/d"):
    return NS(document=NS(name=name), found=NS(name=""), missing="")


class FakeApi:
    """Stand-in for the gapic FirestoreClient used by google-cloud-firestore."""

    def __init__(self):
        self.query_rows = []
        self.get_rows = []
        self.list_rows = []
        self.committed = []

    def run_query(self, *args, **kwargs):
        return iter(self.query_rows)

    def batch_get_documents(self, *args, **kwargs):
        return iter(self.get_rows)

    def get_document(self, *args, **kwargs):
        return NS(name="doc")

    def list_documents(self, *args, **kwargs):
        return iter(self.list_rows)

    def run_aggregation_query(self, *args, **kwargs):
        return iter([NS(result=1)])

    def commit(self, request=None, **kwargs):
        self.committed.append(request)
        return NS(write_results=[])

    def batch_write(self, request=None, **kwargs):
        return NS(write_results=[])


def _client(api=None):
    api = api or FakeApi()
    return NS(_firestore_api=api), api


def _counted(*steps):
    module = _module()
    counts, token = module.begin_counts()
    try:
        for step in steps:
            step()
    finally:
        module.end_counts(token)
    return counts


def test_query_and_batch_reads_count_documents_not_progress_markers_or_calls():
    module = _module()
    client, api = _client()
    assert module.install_firestore_counters(client) is True
    api.query_rows = [_doc(), NS(document=NS(name=""), done=True), _doc()]
    api.get_rows = [NS(found=NS(name="a"), missing=""), NS(found=NS(name=""), missing="gone"), NS(transaction=b"")]
    api.list_rows = [NS(name="a"), NS(name="b"), NS(name="c")]
    counts = _counted(
        lambda: list(client._firestore_api.run_query()),
        lambda: list(client._firestore_api.batch_get_documents()),
        lambda: client._firestore_api.get_document(),
        lambda: list(client._firestore_api.list_documents()),
    )
    assert counts == {"reads": 2 + 2 + 1 + 3, "writes": 0, "deletes": 0, "aggregations": 0}  # 2 docs, found+missing, 1 get, 3 listed


def test_aggregations_and_writes_are_counted_separately_from_reads_and_deletes():
    module = _module()
    client, api = _client()
    module.install_firestore_counters(client)
    writes = [{"update": {"name": "a"}}, {"delete": "projects/p/databases/(default)/documents/c/x"},
              NS(delete="", update=NS(name="b")), NS(delete="projects/p/databases/(default)/documents/c/y")]
    counts = _counted(
        lambda: list(client._firestore_api.run_aggregation_query()),
        lambda: client._firestore_api.commit(request={"writes": writes}),
        lambda: client._firestore_api.batch_write(request=NS(writes=writes[:2])),
        lambda: client._firestore_api.commit(request=NS(writes=[])),
    )
    assert counts == {"reads": 0, "writes": 2 + 1, "deletes": 2 + 1, "aggregations": 1}


def test_failed_commit_is_not_counted_and_the_error_still_propagates():
    module = _module()
    client, api = _client()

    def failing(request=None, **kwargs):
        raise RuntimeError("commit failed")

    api.commit = failing
    module.install_firestore_counters(client)
    counts, token = module.begin_counts()
    try:
        with pytest.raises(RuntimeError, match="commit failed"):
            client._firestore_api.commit(request={"writes": [{"update": {}}]})
    finally:
        module.end_counts(token)
    assert counts["writes"] == 0


def test_operations_outside_a_request_are_ignored_and_results_unchanged():
    module = _module()
    client, api = _client()
    module.install_firestore_counters(client)
    api.query_rows = [_doc(), _doc()]
    assert [row.document.name for row in client._firestore_api.run_query()] == [_doc().document.name] * 2
    counts, token = module.begin_counts()
    module.end_counts(token)
    assert counts == {"reads": 0, "writes": 0, "deletes": 0, "aggregations": 0}


def test_install_is_idempotent_and_never_raises_on_incompatible_clients():
    module = _module()
    client, api = _client()
    assert module.install_firestore_counters(client) is True
    first = client._firestore_api.run_query
    assert module.install_firestore_counters(client) is True
    assert client._firestore_api.run_query == first
    assert module.install_firestore_counters(object()) is False


def test_counting_errors_never_change_a_stream_result():
    module = _module()
    client, api = _client()
    module.install_firestore_counters(client)
    api.query_rows = [object(), _doc()]  # first row has no `document` attribute at all
    rows = list(client._firestore_api.run_query())
    assert len(rows) == 2


def test_real_firestore_gapic_client_exposes_every_wrapped_method():
    from google.cloud.firestore_v1.services.firestore.client import FirestoreClient
    module = _module()
    for name in module.WRAPPED_METHODS:
        assert callable(getattr(FirestoreClient, name)), name


def _app(handler):
    import utils.http_observability as http
    app = Flask("firestore-counts")
    observed = http.observe_http_request(handler)
    app.add_url_rule("/x", view_func=lambda: observed(request), methods=["GET"])
    return app


def test_http_completion_record_carries_numeric_counts_per_request_only(capfd):
    module = _module()
    client, api = _client()
    module.install_firestore_counters(client)
    api.query_rows = [_doc(), _doc(), _doc()]

    def handler(_request):
        if _request.args.get("work"):
            list(client._firestore_api.run_query())
            client._firestore_api.commit(request={"writes": [{"delete": "x"}, {"update": {}}]})
        return "ok"

    app = _app(handler)
    with app.test_client() as http:
        http.get("/x?work=1")
        busy = json.loads(capfd.readouterr().out.splitlines()[-1])
        http.get("/x")
        idle = json.loads(capfd.readouterr().out.splitlines()[-1])
    assert (busy["firestore_reads"], busy["firestore_writes"], busy["firestore_deletes"],
            busy["firestore_aggregations"]) == (3, 1, 1, 0)
    assert (idle["firestore_reads"], idle["firestore_writes"], idle["firestore_deletes"],
            idle["firestore_aggregations"]) == (0, 0, 0, 0)
    assert all(isinstance(busy[key], int) for key in busy if key.startswith("firestore_"))


def test_counts_are_recorded_when_the_handler_raises(capfd):
    module = _module()
    client, api = _client()
    module.install_firestore_counters(client)
    api.query_rows = [_doc()]

    def handler(_request):
        list(client._firestore_api.run_query())
        raise RuntimeError("boom")

    app = _app(handler)
    app.config["PROPAGATE_EXCEPTIONS"] = False
    with app.test_client() as http:
        http.get("/x")
    record = json.loads(capfd.readouterr().out.splitlines()[0])
    assert record["status_code"] == 500 and record["firestore_reads"] == 1


def test_real_sdk_client_is_wrapped_and_a_real_query_is_counted_through_it(monkeypatch):
    # The unit conftest forbids Client._firestore_api (network guard). This guard test needs the
    # real lazy property to detect SDK renames; building the gapic client itself is offline and
    # the query response is faked below, so no connection is ever opened.
    monkeypatch.undo()
    from google.auth.credentials import AnonymousCredentials
    from google.cloud import firestore
    from google.cloud.firestore_v1.types import Document, RunQueryResponse
    module = _module()
    client = firestore.Client(project="demo-mcp-test", credentials=AnonymousCredentials())
    api = client._firestore_api
    name = "projects/demo-mcp-test/databases/(default)/documents/c/"
    api.run_query = lambda *a, **k: iter([RunQueryResponse(document=Document(name=name + "a")),
                                          RunQueryResponse(done=True),
                                          RunQueryResponse(document=Document(name=name + "b"))])
    assert module.install_firestore_counters(client) is True
    assert api._mcp_operation_counters is True
    counts = _counted(lambda: list(client.collection("c").stream()))
    assert counts["reads"] == 2


def test_proxy_forwards_stream_attributes_and_propagates_midstream_errors_unchanged():
    module = _module()
    client, api = _client()

    class Stream:
        cancelled = False

        def __iter__(self):
            yield _doc()
            raise ConnectionError("stream broke")

        def cancel(self):
            Stream.cancelled = True

    api.run_query = lambda *a, **k: Stream()
    module.install_firestore_counters(client)
    stream = client._firestore_api.run_query()
    stream.cancel()
    assert Stream.cancelled is True
    counts, token = module.begin_counts()
    try:
        with pytest.raises(ConnectionError, match="stream broke"):
            list(stream)
    finally:
        module.end_counts(token)
    assert counts["reads"] == 1


def test_streams_consumed_after_the_request_or_in_another_thread_count_nothing_and_do_not_raise():
    import threading
    module = _module()
    client, api = _client()
    module.install_firestore_counters(client)
    api.query_rows = [_doc(), _doc()]
    counts, token = module.begin_counts()
    stream = client._firestore_api.run_query()
    module.end_counts(token)
    assert len(list(stream)) == 2
    assert counts["reads"] == 0
    api.query_rows = [_doc()]
    counts, token = module.begin_counts()
    try:
        worker = threading.Thread(target=lambda: list(client._firestore_api.run_query()))
        worker.start()
        worker.join()
    finally:
        module.end_counts(token)
    assert counts["reads"] == 0


def test_nested_scopes_are_isolated_and_restore_the_outer_counts():
    module = _module()
    client, api = _client()
    module.install_firestore_counters(client)
    api.query_rows = [_doc()]
    outer, outer_token = module.begin_counts()
    list(client._firestore_api.run_query())
    inner, inner_token = module.begin_counts()
    list(client._firestore_api.run_query())
    module.end_counts(inner_token)
    list(client._firestore_api.run_query())
    module.end_counts(outer_token)
    assert (outer["reads"], inner["reads"]) == (2, 1)


def test_transform_only_writes_count_as_writes():
    module = _module()
    client, api = _client()
    module.install_firestore_counters(client)
    counts = _counted(lambda: client._firestore_api.commit(
        request={"writes": [{"transform": {"document": "d"}}, {"update": {}, "update_transforms": [1]}]}))
    assert (counts["writes"], counts["deletes"]) == (2, 0)
