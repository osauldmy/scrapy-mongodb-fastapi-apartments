from fastapi.testclient import TestClient

from api import app

client = TestClient(app)


def test_index() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == "It works!"


# TODO: test api with running mongo or mongomock
# https://github.com/mongomock/mongomock
# https://github.com/michaelkryukov/mongomock_motor
