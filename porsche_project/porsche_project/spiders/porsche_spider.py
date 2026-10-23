from pathlib import Path 
import sys 

base_dir = Path(__file__).parents[3]
if base_dir not in sys.path:
    sys.path.insert(0, str(base_dir))

import scrapy
from scrapy.crawler import Crawler 
from typing import Any, Self
from scrapy import signals
from constants import chrome_path, profile_dir, chrome_debugging_port
from utils.logger import log 
from utils.cdp_chrome_launcher import CdpChromeLauncher
from google_apis.active_searches import load_active_searches
from scrapy.http import Response
from playwright.async_api import Page 
from scrapy_playwright.page import PageMethod
from porsche_project.spider_utils.handle_session import accept_cookies_once, context_kwargs
from porsche_project.spider_utils.parser import extract_car_object, parse_car_obj
from porsche_project.spider_utils.fetch_window_sticker import open_sticker_window
from porsche_project.items import PorscheProjectItem
from datetime import date
import os 
from paths import session_file_dir

class PorscheSpiderSpider(scrapy.Spider):
    name = "porsche_spider"
    chrome: CdpChromeLauncher


    def __init__(self, name: str | None = None, **kwargs: Any):
        super().__init__(name, **kwargs)
        self.searches = load_active_searches()
        self.page_number = 0
        self.cars_profile_number = 0

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider.chrome = CdpChromeLauncher(chrome_path=chrome_path, profile_dir=profile_dir, port=chrome_debugging_port)
        crawler.signals.connect(spider.open_spider, signal=signals.spider_opened)
        return spider

    def open_spider(self, spider):
        if not self.searches :
            log('open spider', 'searches are empty closing spider ....', 'red') 
            self.crawler.engine.close_spider(self, 'Searches are empty noting to do.')
            return
        
        log('Open Spider', 'spider has started', 'blue')
        self.chrome.start_chrome()
        input('are you ready ? ')

    def closed(self, spider):
    
        log('close_spider', 'spider has closed', 'blue')
        self.chrome.stop_chrome()

    async def start(self):
        for search in self.searches:
            url = search['url']
            search_name = search['search_name']

            yield scrapy.Request(
                url=url, callback=self.parse_urls,
                meta= {
                    'playwright': True,
                    'search_name': search_name,
                    'playwright_page_methods': [PageMethod("wait_for_load_state", 'domcontentloaded', timeout=60 * 1000),
                                                 PageMethod("wait_for_timeout", timeout=60 * 1000)]
                }
            )
    
    
    def parse_urls(self, response: Response):
        search_name = response.meta['search_name']

        urls = response.xpath(
            '//article[@data-testid="searchlistitem-card"]/div/a/@href'
        ).getall()

        if not urls:
            log('parse urls', f'urls is empty | {urls}', 'red')

        next_page = response.xpath(
            '//a[normalize-space()="Next Page"]/@href'
        ).get()

        for url in urls:
            yield response.follow(
                url=url,
                callback=self.parse_cars,
                meta={
                    'search_name': search_name,
                    'playwright': True,
                    'playwright_include_page': True,
                }
            )

        if next_page:
            yield response.follow(
                url=next_page,
                callback=self.parse_urls,
                meta={
                    'search_name': search_name,
                    'playwright': True,
                }
            )

        
    async def parse_cars(self, response: Response):


        page: Page = response.meta['playwright_page']
        search_name = response.meta['search_name']
        try:
            try:
                await accept_cookies_once(page=page)
            except Exception as e:
                log('parse_cars', f'accept_cookies failed: {e}', 'yellow')

            data = response.xpath('//main/script[@type="application/ld+json"]/text()').get()
            if not data:
                log('parse_cars', 'data is empty', 'yellow')
                return

            try:
                car_obj = extract_car_object(data=data)
            except Exception as e:
                log('parse_cars', f'extract_car_object failed: {e}', 'red')
                return

            if not car_obj:
                log('parse_cars', 'car_obj is empty', 'red')
                return

            car_item = parse_car_obj(obj=car_obj)

            sticker = {}
            vin = car_item.get('vin')
            if vin:
                try:
                    sticker = await open_sticker_window(page=page, vin=vin) or {}
                except Exception as e:
                    log('parse_cars', f'open_sticker_window failed: {e}', 'red')

            today = date.today().isoformat()
            yield PorscheProjectItem(**car_item, **sticker, search_name=search_name, first_seen=today, last_seen=today)

        except Exception as e:
            log('parse_cars', f'Unexpected error: {e}', 'red')
        finally:
            try:
                await page.close()
            except Exception as e:
                log('parse_cars', f'Error closing page: {e}', 'yellow')
