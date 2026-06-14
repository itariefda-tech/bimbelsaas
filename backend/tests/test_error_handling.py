def test_unknown_route_uses_standard_error_response(client):
    response = client.get("/api/v1/unknown")

    assert response.status_code == 404
    assert response.json["success"] is False
    assert response.json["error"]["code"] == "not_found"
    assert response.json["request_id"]

