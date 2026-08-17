def test_login(client) -> None:
    response = client.post("/api/v1/auth/login")
    assert response.status_code == 200
    assert response.json() == {"message": "Login successful"}
