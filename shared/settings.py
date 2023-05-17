from pydantic import AnyHttpUrl, BaseSettings, MongoDsn


class Settings(BaseSettings):
    class Config:
        env_file = ".env"

    MONGO_URL: MongoDsn
    MONGO_DATABASE: str
    MONGO_COLLECTION: str

    MINIO_URL: AnyHttpUrl
    MINIO_LOGIN: str
    MINIO_PASSWORD: str
    MINIO_BUCKET: str
