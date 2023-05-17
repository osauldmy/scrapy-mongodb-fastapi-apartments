#!/usr/bin/env python3
from pathlib import Path
from urllib.request import urlretrieve

from diagrams import Cluster, Diagram
from diagrams.aws.storage import S3
from diagrams.custom import Custom
from diagrams.onprem.database import MongoDB
from diagrams.programming.framework import FastAPI

scrapy_icon = "/tmp/scrapylogo.png"
if not Path(scrapy_icon).exists():
    scrapy_icon_url = "https://scrapy.org/img/scrapylogo.png"
    urlretrieve(scrapy_icon_url, scrapy_icon)

with Diagram(
    "Architecture diagram", direction="LR", show=False, filename="architecture_alt"
):
    scrapy = Custom("", scrapy_icon)

    with Cluster("Persistence"):
        with Cluster("MinIO"):
            photos = S3("real estate photos")
            snapshots = S3("JSON snapshots")
            logs = S3("scraper logs")

            scrapy >> [logs, photos, snapshots]

        mongo = MongoDB("MongoDB")
        scrapy >> mongo
    mongo >> FastAPI("FastAPI") >> mongo
