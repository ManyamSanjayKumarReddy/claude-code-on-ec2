def test_metrics_endpoint_exposes_prometheus_data(client):
    client.get("/health")

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "http_requests_total" in response.text
    assert '/health' in response.text
