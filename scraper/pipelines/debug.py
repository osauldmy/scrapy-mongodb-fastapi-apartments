from __future__ import annotations

import pprint
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scrapy import Spider

    from shared.models import Apartment


class PrettyPrintPydantic:
    def process_item(self, item: Apartment, _: Spider) -> Apartment:
        pprint.pprint(item.dict(exclude_unset=True, exclude_none=True))
        return item
