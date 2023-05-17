from __future__ import annotations

from beanie import Document

from shared.models import Apartment
from shared.settings import Settings


class ApartmentBeanie(Document, Apartment):  # type: ignore[misc]
    class Settings:
        name = Settings().MONGO_COLLECTION
        use_state_management = True
