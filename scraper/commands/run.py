from __future__ import annotations

from typing import TYPE_CHECKING

import scrapy.commands

if TYPE_CHECKING:
    from argparse import Namespace
    from typing import Any


class Command(scrapy.commands.ScrapyCommand):
    """
    https://docs.scrapy.org/en/latest/topics/commands.html#custom-project-commands

    Custom scrapy CLI command/kind of script starting execution of all available spiders.
    Something to implement because scrapy lacks (intentionally?) this functionality.
    Name of the command defines filename where `Command` implementation is located.
    Examples (standard CLI commands): https://github.com/scrapy/scrapy/tree/master/scrapy/commands

    Usage: scrapy run

    Other options to implement this pattern:
        Sequential crawling from shell.
        `for spider in $(scrapy list); do scrapy crawl $spider; done`

        or `scrapy list | xargs -n 1 scrapy crawl`

        Parallel execution from shell.
        `scrapy list| xargs -P 0 -n 1 scrapy crawl`

        More: https://stackoverflow.com/questions/15564844/locally-run-all-of-the-spiders-in-scrapy
    """

    requires_project = True

    def short_desc(self) -> str:
        return "Run all spiders [custom command]"

    def run(self, _: Any, opts: Namespace) -> None:
        for spider_name in self.crawler_process.spider_loader.list():
            self.crawler_process.crawl(spider_name, **vars(opts))
        self.crawler_process.start()
        # TODO(logs to minio): create temp file, send it as param to .crawl() to redirect logs,
        # then maybe print it and upload to S3/Minio
