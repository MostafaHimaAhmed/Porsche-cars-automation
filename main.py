import sys 
from pathlib import Path 

base_dir = Path(__file__).parent

if base_dir not in sys.path:
    sys.path.insert(0, str(base_dir))

from constants import porsche_spider_name, SHEETS
from paths import spider_base_dir
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from google_apis.google_sheets_api import GoogleSheetsApi
import os 

google_client = GoogleSheetsApi.from_env()
sheets_titles = google_client.get_sheet_titles()

for sheet_name, headers in SHEETS.items():
    if sheets_titles:
        if sheet_name not in sheets_titles:
            google_client.create_blank_sheet(sheet_name)
            google_client.add_row(sheet_name=sheet_name, rows=[headers])
    else:
        google_client.create_blank_sheet(sheet_name)
        google_client.add_row(sheet_name=sheet_name, rows=[headers])



  

os.chdir(spider_base_dir)
process = CrawlerProcess(get_project_settings())
process.crawl(porsche_spider_name)
process.start()



