def test_health_endpoint_reports_ok(api_client):
    response = api_client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

