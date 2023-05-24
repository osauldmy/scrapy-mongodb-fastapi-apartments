from __future__ import annotations

import datetime
import os
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from beanie import PydanticObjectId
from fastapi.testclient import TestClient

from api import app
from shared.models import Apartment, Source

if TYPE_CHECKING:
    from collections.abc import Iterator
    from contextlib import AbstractContextManager

    from shared.settings import Settings
    from tests.conftest import MotorClientClass, PyMongoClient


@pytest.fixture
def patch_motor_client(
    motor_client_class: MotorClientClass,
    pymongo_client: PyMongoClient,
    test_settings: Settings,
) -> Iterator[AbstractContextManager[MotorClientClass]]:
    with patch.dict(os.environ, {"MONGO_DATABASE": test_settings.MONGO_DATABASE}):
        yield patch("api.AsyncIOMotorClient", motor_client_class)
    pymongo_client.drop_database(test_settings.MONGO_DATABASE)


@pytest.fixture
def client(patch_motor_client: AbstractContextManager[None]) -> Iterator[TestClient]:
    with patch_motor_client:
        # if it's `yield TestClient(app)`, then lifespan is not called,
        # so init_beanie() is not awaited and api will fail on attempt
        # of communicating with db
        with TestClient(app) as _client:
            yield _client


class TestAPI:
    def test_get_id_wrong_type(self, client: TestClient) -> None:
        response = client.get("/apartments/abc")
        assert response.status_code == 422

    def test_get_not_existing_apartment(
        self, client: TestClient, random_objectid: PydanticObjectId
    ) -> None:
        response = client.get(f"/apartments/{random_objectid}")
        assert response.status_code == 404
        assert response.json() == {"detail": "Not Found"}

    def test_delete_not_existing_apartment(
        self, client: TestClient, random_objectid: PydanticObjectId
    ) -> None:
        response = client.delete(f"/apartments/{random_objectid}")
        assert response.status_code == 404
        assert response.json() == {"detail": "Not Found"}

    def test_list_apartments_empty_db(self, client: TestClient) -> None:
        response = client.get("/apartments")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_one(self, client: TestClient, yit_apartment: Apartment) -> None:
        response = client.post("/apartments", content=yit_apartment.json())
        assert response.status_code == 200
        assert response.json() == str(yit_apartment.id)

        expected = yit_apartment
        expected.source = Source.API  # API rewrites source to "api"

        list_response = client.get("/apartments")  # by listing all
        get_response = client.get(f"/apartments/{yit_apartment.id}")  # by getting one
        assert list_response.status_code == get_response.status_code == 200

        [in_db], by_id = list_response.json(), get_response.json()
        assert Apartment.parse_obj(in_db) == Apartment.parse_obj(by_id) == expected

    def test_create_one_without_id_check_timestamp(
        self, client: TestClient, yit_apartment: Apartment
    ) -> None:
        del yit_apartment.id
        past = datetime.datetime.utcnow() - datetime.timedelta(seconds=10)
        response = client.post("/apartments", content=yit_apartment.json())
        future = datetime.datetime.utcnow() + datetime.timedelta(seconds=10)
        assert response.status_code == 200

        id = response.json()
        timestamp = PydanticObjectId(id).generation_time.replace(tzinfo=None)
        assert past <= timestamp <= future
