from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import TYPE_CHECKING

import scrapy
import scrapy.exceptions
import scrapy.http

from scraper.pages.yit import YitSkJsonApartmentPage

if TYPE_CHECKING:
    from typing import Any, Iterator

    from scrapy.http import JsonRequest, Request, TextResponse

    from shared.models import Apartment


class YitSkFlatsForSale(scrapy.Spider):
    name = "yit.sk"
    allowed_domains = ("yit.sk",)

    API_URL = "https://www.yit.sk/api/v1/productsearch/apartments"
    PER_PAGE = 10
    BODY = json.loads(
        (Path(__file__).parent / "resources" / "yit.request_body.json").read_text()
    )

    def start_requests(self) -> Iterator[JsonRequest]:
        # Infinite loop to be stopped from .process_listing() by raising CloseSpider
        # Not the best approach, but it gets the job done.
        # More clean/sophisticated version would be to get the amount of existing ads
        # right at the start of start_requests and then use `for page_index in range(max_page)`
        yield from (
            scrapy.http.JsonRequest(
                url=self.API_URL,
                data=self.BODY | {"StartPage": page_index, "PageSize": self.PER_PAGE},
                method="POST",
                callback=self.process_listing,
            )
            for page_index in itertools.count()
        )

    def process_listing(self, response: TextResponse) -> Iterator[Request]:
        """
        Yield up to self.PER_PAGE items from single response.
        For each item additionally make a request to its html page to get all photos links.
        """

        data = response.json()
        if data["IsMoreAvailable"] is False:
            raise scrapy.exceptions.CloseSpider("Nothing more to scrape!")

        for apartment in data.get("Hits") or ():
            for_sale = apartment["Fields"]["ProductItemForSale"]
            for_rent = apartment["Fields"]["ProductItemForRent"]
            if not for_sale or for_rent:
                self.logger.warning(
                    "Ignoring. This spider only cares about selling apartments!"
                )
                continue

            apartment_html_url = "https://www.yit.sk" + apartment["Fields"]["_Url"]
            yield scrapy.Request(
                apartment_html_url,  # for photos
                callback=self.yield_item,
                cb_kwargs={"json_data": apartment["Fields"]},
            )

    def yield_item(
        self, response: TextResponse, json_data: dict[str, Any]
    ) -> Iterator[Apartment]:
        """Delegate parsing/cleaning part to web-poet pattern implementation."""
        yield YitSkJsonApartmentPage(response=response, data=json_data).to_item()
