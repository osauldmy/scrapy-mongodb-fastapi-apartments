from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import scrapy
from scrapy.pipelines.images import ImagesPipeline

if TYPE_CHECKING:
    from typing import Any, Iterator

    from scrapy import Request
    from scrapy.pipelines.media import MediaPipeline

    from shared.models import Apartment


# NOTE: if twisted downloading & botocore uploading are slow,
# rewrite this pipeline(s) without using FilesPipeline/ImagesPipeline,
# so downloading is done by aiohttp/httpx and saving to MinIO by aiobotocore
class SaveToMinioApartmentPhotos(ImagesPipeline):
    def get_media_requests(
        self, item: Apartment, _: MediaPipeline.SpiderInfo
    ) -> Iterator[Request]:
        photos = item.photos.copy()
        item.photos.clear()
        for url in photos:
            yield scrapy.Request(url)

    def file_path(self, request: Request, item: Apartment, *_: Any, **__: Any) -> str:
        img_filename = Path(urlparse(request.url).path).name
        return f"{str(item.id)}/{img_filename}"
