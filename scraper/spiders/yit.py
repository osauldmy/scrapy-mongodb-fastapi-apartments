from __future__ import annotations

import json
import math
from pathlib import Path
from typing import TYPE_CHECKING

import scrapy
from scrapy.http import JsonRequest, Request

from scraper.pages.yit import YitSkJsonApartmentPage

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any, Callable

    from scrapy.http import Response, TextResponse

    from shared.models import Apartment


class YitSkFlatsForSale(scrapy.Spider):
    name = "yit.sk"
    allowed_domains = ("yit.sk",)

    API_URL = "https://www.yit.sk/api/v1/productsearch/apartments"
    PER_PAGE = 10
    BODY = json.loads(
        (Path(__file__).parent / "resources" / "yit.request_body.json").read_text()
    )

    @classmethod
    def _api_request(
        cls, page: int, callback: Callable[[Response], Any]
    ) -> JsonRequest:
        return JsonRequest(
            url=cls.API_URL,
            data=cls.BODY | {"StartPage": page, "PageSize": cls.PER_PAGE},
            method="POST",
            callback=callback,
        )

    def start_requests(self) -> tuple[Request]:
        """
        Make first request to API to determine how many apartments/pages are there
        and delegate the response to next method where additional request are made.
        """
        return (self._api_request(page=0, callback=self.continue_requests),)

    def continue_requests(self, response: TextResponse) -> Iterator[Request]:
        """
        Use json data from `.start_requests()`, pass them to `.process_listing()`.
        Calculate how many pages with content are there, so it's not infinite loop
        or `itertools.count()` which should be interrupted with `raise CloseSpider`
        (which doesn't really work as I'd expect) and make the rest of requests.
        """
        yield from self.process_listing(response)
        last_page_plus_one = math.ceil(response.json()["TotalHits"] / self.PER_PAGE)
        yield from (
            self._api_request(page=page, callback=self.process_listing)
            for page in range(1, last_page_plus_one)
        )

    def process_listing(self, response: TextResponse) -> Iterator[Request]:
        """
        Yield up to self.PER_PAGE items from single response.
        For each item additionally make a request to its html page to get all photos links.
        """
        data = response.json()

        for apartment in data.get("Hits") or ():
            for_sale = apartment["Fields"]["ProductItemForSale"]
            for_rent = apartment["Fields"]["ProductItemForRent"]
            if not for_sale or for_rent:
                self.logger.warning(
                    "Ignoring. This spider only cares about selling apartments!"
                )
                continue

            apartment_html_url = "https://www.yit.sk" + apartment["Fields"]["_Url"]
            yield Request(
                apartment_html_url,  # for photos
                callback=self.yield_item,
                cb_kwargs={"json_data": apartment["Fields"]},
            )

    def yield_item(
        self, response: TextResponse, json_data: dict[str, Any]
    ) -> Iterator[Apartment]:
        """Delegate parsing/cleaning part to web-poet pattern implementation."""
        yield YitSkJsonApartmentPage(response=response, data=json_data).to_item()
