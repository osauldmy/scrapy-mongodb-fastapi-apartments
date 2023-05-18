import datetime

from pydantic.json import pydantic_encoder

from shared.settings import Settings

PROJECT_NAME = BOT_NAME = "scraper"
SPIDER_MODULES = [f"{PROJECT_NAME}.spiders"]
# https://docs.scrapy.org/en/latest/topics/commands.html#custom-project-commands
COMMANDS_MODULE = f"{PROJECT_NAME}.commands"

USER_AGENT = (
    "scraper/0.0.1 https://github.com/osauldmy/scrapy-mongodb-fastapi-apartments"
)
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
COOKIES_ENABLED = False
TELNETCONSOLE_ENABLED = False
ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 16
AUTOTHROTTLE_ENABLED = True

LOG_LEVEL = "INFO"
LOG_SHORT_NAMES = True

DOTENV_SETTINGS = Settings()

FILES_STORE = f"s3://{DOTENV_SETTINGS.MINIO_BUCKET}/"
IMAGES_STORE = f"s3://{DOTENV_SETTINGS.MINIO_BUCKET}/photos/"

AWS_ACCESS_KEY_ID = DOTENV_SETTINGS.MINIO_LOGIN
AWS_SECRET_ACCESS_KEY = DOTENV_SETTINGS.MINIO_PASSWORD
AWS_ENDPOINT_URL = DOTENV_SETTINGS.MINIO_URL
AWS_USE_SSL, AWS_VERIFY = True, True

ITEM_PIPELINES: dict[str, int] = {
    # f"{PROJECT_NAME}.pipelines.debug.PrettyPrintPydantic": 0,
    "scrapy.pipelines.files.FilesPipeline": 1,  # NOTE: required by FEEDS below
    f"{PROJECT_NAME}.pipelines.mongo.SaveToMongoWithDuplicatesCheck": 600,
    f"{PROJECT_NAME}.pipelines.minio.SaveToMinioApartmentPhotos": 700,
}

today_str = datetime.date.strftime(datetime.date.today(), "%d.%m.%Y")
FEEDS = {
    f"{FILES_STORE}/apartments/%(name)s.{today_str}.json": {
        "format": "json",
        "encoding": "utf-8",
        "indent": 2,
        "store_empty": True,
        "item_export_kwargs": {
            "default": pydantic_encoder,  # fixes json.dumps(pydantic_model)
            "ensure_ascii": False,
        },
    }
}
