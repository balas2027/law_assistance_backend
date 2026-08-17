def test_get_chats(client) -> None:
    response = client.get("/api/v1/chat")
    assert response.status_code == 200
