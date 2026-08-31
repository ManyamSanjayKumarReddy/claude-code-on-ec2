import structlog


def test_request_gets_an_id_header(client):
    response = client.get("/health")

    assert "X-Request-ID" in response.headers


def test_request_emits_a_structured_log(client):
    with structlog.testing.capture_logs() as captured:
        response = client.get("/health")

    request_id = response.headers["X-Request-ID"]
    [entry] = [e for e in captured if e["event"] == "request_finished"]

    assert entry["request_id"] == request_id
    assert entry["method"] == "GET"
    assert entry["path"] == "/health"
    assert entry["status_code"] == 200
    assert "duration_ms" in entry
