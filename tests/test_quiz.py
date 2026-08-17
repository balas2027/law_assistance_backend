def test_get_quizzes(client) -> None:
    response = client.get("/api/v1/quiz")
    assert response.status_code == 200
