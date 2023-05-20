from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from scraper.spiders.yit import YitSkFlatsForSale
from tests.scraper.spiders import make_fake_json_response

if TYPE_CHECKING:
    from typing import Any

    from shared.models import Apartment
    from tests.scraper.spiders import FakeYitApiResponse


class TestYitSkFlatsForSale:
    spider = YitSkFlatsForSale()

    def test_start_requests(self) -> None:
        [request] = self.spider.start_requests()
        assert request.url == self.spider.API_URL
        assert request.method == "POST"
        assert request.callback == self.spider.continue_requests
        assert json.loads(request.body)["StartPage"] == 0
        assert json.loads(request.body)["PageSize"] == self.spider.PER_PAGE

    @pytest.mark.parametrize(
        # NOTE: expected_extra_requests is calculated with PER_PAGE=10
        "total_hits,expected_extra_requests",
        ((0, 0), (1, 0), (10, 0), (11, 1), (100, 9), (319, 31)),
    )
    def test_continue_requests_extra_requests_made(
        self, total_hits: int, expected_extra_requests: int
    ) -> None:
        """Tests how many additional requests to API will spider make."""
        fake_body: FakeYitApiResponse = {"TotalHits": total_hits, "Hits": []}
        iterator = self.spider.continue_requests(make_fake_json_response(fake_body))
        requests = tuple(iterator)

        assert len(requests) == expected_extra_requests
        for index, request in enumerate(requests, start=1):
            assert request.url == self.spider.API_URL
            assert request.method == "POST"
            assert request.callback == self.spider.process_listing
            assert json.loads(request.body)["StartPage"] == index
            assert json.loads(request.body)["PageSize"] == self.spider.PER_PAGE

    def test_continue_requests(self) -> None:
        fake_body: FakeYitApiResponse = {
            "TotalHits": 15,
            "Hits": [
                {
                    "Fields": {
                        "ProductItemForSale": True,
                        "ProductItemForRent": False,
                        "_Url": f"/foo{i}",
                    },
                }
                for i in range(self.spider.PER_PAGE)
            ],
        }
        iterator = self.spider.continue_requests(make_fake_json_response(fake_body))
        *photo_requests, extra_api_request = tuple(iterator)

        assert len(photo_requests) == self.spider.PER_PAGE
        for index, request in enumerate(photo_requests):
            assert request.method == "GET"
            assert request.url.endswith(str(index))

        assert extra_api_request.method == "POST"
        assert extra_api_request.url == self.spider.API_URL

    def test_process_listing_empty(self) -> None:
        response = make_fake_json_response({"Hits": []})
        assert tuple(self.spider.process_listing(response)) == ()

    def test_process_listing_single_hit(
        self, yit_apartment_from_server: dict[str, Any]
    ) -> None:
        response = make_fake_json_response({"Hits": [yit_apartment_from_server]})
        aux_requests = tuple(self.spider.process_listing(response))
        assert len(aux_requests) == 1
        [photo_request] = aux_requests
        assert photo_request.url == (
            "https://www.yit.sk" + yit_apartment_from_server["Fields"]["_Url"]
        )

    def test_yield_item(
        self, yit_apartment_from_server: dict[str, Any], yit_apartment: Apartment
    ) -> None:
        expected = yit_apartment
        apartments = tuple(
            self.spider.yield_item(None, yit_apartment_from_server["Fields"])
        )
        assert len(apartments) == 1

        [result] = apartments
        assert result.dict(exclude={"id"}) == expected.dict(exclude={"id"})

        result.id, expected.id = None, None
        assert result == expected
