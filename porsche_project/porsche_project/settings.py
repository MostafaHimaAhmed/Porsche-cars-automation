from pathlib import Path 
import sys 

base_dir = Path(__file__).resolve().parents[2]
if base_dir not in sys.path:
    sys.path.insert(0, str(base_dir))

from paths import window_sticker_images_dir
BOT_NAME = "porsche_project"

SPIDER_MODULES = ["porsche_project.spiders"]
NEWSPIDER_MODULE = "porsche_project.spiders"

ADDONS = {}
LOG_LEVEL = 'INFO'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "porsche_project (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False 

# Concurrency and throttling settings
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1
PLAYWRIGHT_MAX_PAGES_PER_CONTEXT = 1


PLAYWRIGHT_BROWSER_TYPE = 'chromium'
DOWNLOAD_HANDLERS = {
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    # "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

PLAYWRIGHT_CDP_URL = "http://localhost:9222"

PLAYWRIGHT_CDP_KWARGS = {
    "timeout": 60 * 1000
}

PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 60 * 1000 

import playwright.async_api
from typing import Dict 
from fake_useragent import UserAgent
ua = UserAgent(browsers=['Chrome', 'Edge', 'Firefox'], os=['Windows'])

async def custom_headers(
    *,
    browser_type_name: str,
    playwright_request: playwright.async_api.Request,
    scrapy_request_data: dict,
) -> Dict[str, str]:
    headers = await playwright_request.all_headers()
    scrapy_headers = scrapy_request_data["headers"].to_unicode_dict()
    headers["Cookie"] = scrapy_headers.get("Cookie")
    headers['User-Agent'] = ua.random
    return headers

PLAYWRIGHT_PROCESS_REQUEST_HEADERS = custom_headers

# FEEDS = {
#     'output.json': {
#         'format': 'json',
#         'encoding': 'utf-8'
#     }
# }

FILES_STORE = str(window_sticker_images_dir)
# PLAYWRIGHT_PROCESS_REQUEST_HEADERS = None

#SPIDER_MIDDLEWARES = {
#    "porsche_project.middlewares.PorscheProjectSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    "porsche_project.middlewares.PorscheProjectDownloaderMiddleware": 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   "porsche_project.pipelines.DropDuplicatesPipeline": 300,
   "porsche_project.pipelines.WindowStickerDownloadPipeline": 400,
   "porsche_project.pipelines.UploadDataToGoogleSheets": 500,
   "porsche_project.pipelines.UploadStickerOptions": 600,
   "porsche_project.pipelines.ConvertWindowStickerToPDF": 700,
   'porsche_project.google_drive_pipeline.UploadToGoogleDrive': 800
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"
