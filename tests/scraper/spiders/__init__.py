from __future__ import annotations

import json
from typing import TYPE_CHECKING

from scrapy.http import TextResponse

if TYPE_CHECKING:
    from typing import Any


def make_fake_json_response(data: dict[str, Any], url: str = "") -> TextResponse:
    return TextResponse(url=url, body=json.dumps(data), encoding="utf-8")
