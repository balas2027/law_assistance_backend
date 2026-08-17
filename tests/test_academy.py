def test_get_courses(client) -> None:
    response = client.get("/api/v1/academy")
    assert response.status_code == 200
