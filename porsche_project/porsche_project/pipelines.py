from pathlib import Path
import sys
from typing import Any, Coroutine, Literal

from scrapy.http import Request, Response
from scrapy.pipelines.media import MediaPipeline, FileInfo
from twisted.python.failure import Failure

base_dir = Path(__file__).resolve().parents[2]
if base_dir not in sys.path:
    sys.path.insert(0, str(base_dir))

from utils.logger import log 
from google_apis.google_sheets_api import GoogleSheetsApi
from itemadapter import ItemAdapter
from scrapy.pipelines.files import  FilesPipeline
from scrapy.exceptions import DropItem
import scrapy 
from collections import defaultdict
from constants import SEARCH_SHEETS_HEADERS, CHANGES_SHEET_NAME, OPTIONS_SHEET_NAME, OPTIONS_SHEET_HEADERS
from datetime import date 
from porsche_project.spider_utils.sticker_analyzer import analyze_sticker

from dotenv import load_dotenv
from paths import dotenv_path
import os 
from google import genai


load_dotenv(dotenv_path=dotenv_path)
google_api_key = os.environ['GOOGLE_API_KEY']

gemini = genai.Client(api_key=google_api_key)

vin_index = SEARCH_SHEETS_HEADERS.index('vin')
price_index = SEARCH_SHEETS_HEADERS.index('price')
first_seen_index = SEARCH_SHEETS_HEADERS.index('first_seen')
last_seen_index = SEARCH_SHEETS_HEADERS.index('last_seen')
status_index = SEARCH_SHEETS_HEADERS.index('status')
date_of_gone_index = SEARCH_SHEETS_HEADERS.index('date_of_gone')


OPTIONS_VIN_INDEX = OPTIONS_SHEET_HEADERS.index("vin")
OPTIONS_OPTION_INDEX = OPTIONS_SHEET_HEADERS.index("option")
OPTIONS_PRICE_INDEX = OPTIONS_SHEET_HEADERS.index("price")


def normalize_price(value):
    if value is None or str(value).strip() == "":
        return None

    clean = "".join(ch for ch in str(value) if ch.isdigit() or ch == ".")
    try:
        return float(clean) if clean else None
    except ValueError:
        return None


class UploadStickerOptions:

    def __init__(self):
        self.google = GoogleSheetsApi.from_env()
        self.options = []
        self.old_options = set()
        self.processed_items = 0
        self.skipped_items = 0
        self.errors = 0

        log("OPTIONS", "Pipeline initialized", "cyan")

    def process_item(self, item, spider):
        body = item.body
        vin = item.vin


        if not body:
            self.skipped_items += 1
            log("OPTIONS", f"SKIP | VIN={vin} | No options found", "yellow")
            return item

        options = {}
        total_options = None 
        try:

            data = analyze_sticker(gemini, body)
            if data:
                options = data['options']
                total_options = data['total']
   
        
                # Supports either a dict or a list of (option, price) pairs
                option_items = (options.items() if isinstance(options, dict) else options)

                item_rows = []

                for option, price in option_items:
                    item_rows.append((vin, option, normalize_price(price)))

                if total_options is not None:
                    item_rows.append((vin,"total_options",normalize_price(total_options),))

                self.options.extend(item_rows)
                self.processed_items += 1

                log("OPTIONS", f"PARSED | VIN={vin} | " f"Options={len(item_rows)} | "f"Total={total_options}","green")
                return item
            
            log('analyze options', f'data for [{vin}] is emtpy, {data} ', 'red')
            return item

        except Exception as exc:
            self.errors += 1
            log("OPTIONS", f"PARSE ERROR | VIN={vin} | " f"{type(exc).__name__}: {exc}", "red")
            return item
        
        


    def close_spider(self, spider):
        log("OPTIONS", "Upload process started", "bold cyan")

        try:
            log("OPTIONS", f"Fetching existing rows from '{OPTIONS_SHEET_NAME}'", "blue", )

            old_data = self.google.get_rows(OPTIONS_SHEET_NAME) or []

            if not old_data:
                log( "OPTIONS", "Sheet is empty or has no rows", "yellow" )

                if self.options:
                    rows = [
                        OPTIONS_SHEET_HEADERS,
                        *[ list(row) for row in dict.fromkeys(self.options) ],
                    ]

                    self.google.add_row( OPTIONS_SHEET_NAME, rows)
                    log("OPTIONS", f"INITIAL UPLOAD | Rows={len(rows) - 1}", "green",)

                else:
                    log("OPTIONS", "Nothing to upload", "yellow", )

                return

            # Skip header
            for row in old_data[1:]:
                try:
                    if len(row) <= max(
                        OPTIONS_VIN_INDEX,
                        OPTIONS_OPTION_INDEX,
                        OPTIONS_PRICE_INDEX,
                    ):
                        log(
                            "OPTIONS",
                            f"INVALID ROW | {row}",
                            "yellow",
                        )
                        continue

                    vin = row[OPTIONS_VIN_INDEX]
                    option = row[OPTIONS_OPTION_INDEX]
                    price = normalize_price(
                        row[OPTIONS_PRICE_INDEX]
                    )

                    self.old_options.add((vin, option, price))

                except (IndexError, TypeError) as exc:
                    log(
                        "OPTIONS",
                        f"ROW ERROR | {exc}",
                        "yellow",
                    )

            log(
                "OPTIONS",
                f"EXISTING DATA | Rows={len(old_data) - 1} | "
                f"Unique={len(self.old_options)}",
                "blue",
            )

            # Deduplicate incoming data and exclude existing rows
            unique_new = list(dict.fromkeys(self.options))

            data_to_upload = [
                list(row)
                for row in unique_new
                if row not in self.old_options
            ]

            duplicates = len(self.options) - len(unique_new)
            already_exists = len(unique_new) - len(data_to_upload)

            log(
                "OPTIONS",
                f"COMPARE | Collected={len(self.options)} | "
                f"Duplicates={duplicates} | "
                f"Already exists={already_exists} | "
                f"New={len(data_to_upload)}",
                "cyan",
            )

            if not data_to_upload:
                log(
                    "OPTIONS",
                    "NO CHANGES | Google Sheets is already up to date",
                    "yellow",
                )
                return

            log(
                "OPTIONS",
                f"UPLOADING | Rows={len(data_to_upload)} "
                f"| Sheet={OPTIONS_SHEET_NAME}",
                "bold blue",
            )

            self.google.add_row(
                OPTIONS_SHEET_NAME,
                data_to_upload,
            )

            log(
                "OPTIONS",
                f"UPLOAD COMPLETE | Rows={len(data_to_upload)}",
                "bold green",
            )

        except Exception as exc:
            self.errors += 1

            log(
                "OPTIONS",
                f"UPLOAD FAILED | {type(exc).__name__}: {exc}",
                "bold red",
            )

        finally:
            log(
                "OPTIONS",
                f"SUMMARY | Items processed={self.processed_items} | "
                f"Items skipped={self.skipped_items} | "
                f"Collected rows={len(self.options)} | "
                f"Errors={self.errors}",
                "bold magenta",
            )

            log("OPTIONS", "Pipeline closed", "bold cyan")


class WindowStickerDownloadPipeline(FilesPipeline):

    def get_media_requests(self, item: Any, info: MediaPipeline.SpiderInfo) -> list[Request]:
            adapter = ItemAdapter(item)
            headers = adapter.get('headers') or {}
            return [
                scrapy.Request(url, headers=headers)
                for url in (adapter.get('file_urls') or [])
            ]

    def file_path(self, request: Request, response: Response | None = None, info: MediaPipeline.SpiderInfo | None = None, *, item: Any = None) -> str:
        adapter = ItemAdapter(item) if item is not None else ItemAdapter({})
        vin = adapter.get('vin') or "unkown_vin"
        search_name = adapter.get('search_name') or 'unkwon_search_name'
        clean_search_name = search_name.lower().replace(' ', "_")
        return f'{clean_search_name}/{vin}.png'

    def item_completed(self, results: list[tuple[Literal[True], FileInfo] | tuple[Literal[False], Failure]], item: Any, info: MediaPipeline.SpiderInfo) -> Any:
        adapter = ItemAdapter(item=item)
        downloaded = False
        for success, result in results:
            if isinstance(result, Failure):
                log('Sticker Window falied', result.getErrorMessage(), 'red')
            else:
                log('Sticker Window success', f'{result['status']} | {result["path"]}', 'green')
                downloaded = True 
                adapter['sticker_path'] = result.get('path', '')

        adapter['sticker_downloaded'] = downloaded

        return item
    

class DropDuplicatesPipeline:
    def __init__(self) -> None:
        self.vins_seen = set()

    def process_item(self, item, spider):
        vin = item.vin
        if vin in self.vins_seen:
            raise DropItem(f"Duplicate VIN: {vin}")
        
        self.vins_seen.add(vin)
        return item 


def get_cell(row, index):
    return row[index] if len(row) > index else None

def col_letter(index):
    """0 -> A, 1 -> B, ... 25 -> Z, 26 -> AA"""
    letters = ""
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def cell_range(sheet_name, row_number, start_col, end_col):
    """مثال: 'My Sheet'!A5:O5 (اسم الشيت لازم يتحط بين apostrophes)"""
    safe = sheet_name.replace("'", "''")
    return f"'{safe}'!{col_letter(start_col)}{row_number}:{col_letter(end_col)}{row_number}"


class UploadDataToGoogleSheets:

    def __init__(self) -> None:
        self.google = GoogleSheetsApi.from_env()
        

    def open_spider(self, spider):
        self.items = defaultdict(list)
        self.indexs = {}
        

    def process_item(self, item, spider):
        search_name = item.search_name
        vin = item.vin; url=item.url; model=item.model; inner_color=item.inner_color
        outer_color = item.outer_color; model_date = item.model_date; owners_count = item.owners_count; price = item.price
        mileage = item.mileage; dealer = item.dealer; city=item.city; postal_code = item.postal_code; street = item.street
        sticker_downloaded= item.sticker_downloaded; first_seen = item.first_seen; last_seen = item.last_seen

        self.items[search_name].append([
            vin, model, inner_color, outer_color, model_date, owners_count, price, mileage, dealer, city, postal_code,
            street, first_seen, last_seen, url, sticker_downloaded
        ])

        return item

    def close_spider(self, spider):
        today = date.today().isoformat()
        changes_rows = []

        for sheet_name, scraped_rows in self.items.items():
            rows_to_append = []
            updates = []

            sheet_rows = self.google.get_rows(sheet_name=sheet_name)

            # if all rows are empty ...
            if not sheet_rows:
                log(sheet_name, f"empty sheet, adding all {len(scraped_rows)} cars", 'green')
                self.google.add_row(sheet_name=sheet_name, rows=[SEARCH_SHEETS_HEADERS])
                self.google.add_row(sheet_name, scraped_rows)
                continue


            _, *old_rows = sheet_rows
            old_vins = {
                get_cell(row, vin_index): (index, row)   # +2 لأن صف 1 = header
                for index, row in enumerate(old_rows, start=2)
                if row and get_cell(row, vin_index)
            }
            new_vins = set()

            for new_row in scraped_rows:
                vin = new_row[vin_index]
                new_vins.add(vin)

                # New Car
                if vin not in old_vins:
                    log(sheet_name, f"NEW car: {vin}", "green")
                    rows_to_append.append(new_row)
                    continue

                # if the car is existing get the row number and the row itself (old row)
                row_number, old_row = old_vins[vin]

                # keeping first seen and update last_seen
                new_row[first_seen_index] = get_cell(old_row, first_seen_index) or today
                new_row[last_seen_index] = today


                # Price changed
                old_price = normalize_price(get_cell(old_row, price_index))
                new_price = normalize_price(get_cell(new_row, price_index))

                if new_price != old_price:
                    log(sheet_name, f"PRICE CHANGED: {vin} | {old_price} -> {new_price}", "yellow")
                    changes_rows.append([ vin, today, old_price, new_price])
                else:
                    log(sheet_name, f"no change: {vin}")


                updates.append({
                    'range': cell_range(sheet_name, row_number, 0, len(SEARCH_SHEETS_HEADERS)-1),
                    'values': [new_row]
                })

                if get_cell(old_row, status_index) == 'gone':
                    log(sheet_name, f"BACK again: {vin}", "cyan")
                    updates.append(
                        {
                            "range": cell_range(sheet_name, row_number, status_index, date_of_gone_index),
                            'values': [['','']]
                        }
                    )

            if scraped_rows:
                for vin in old_vins.keys() - new_vins:
                    row_number, old_row = old_vins[vin]
                    if get_cell(old_row, status_index) == "gone":
                        continue  # اتسجلت قبل كده، متكررش التاريخ
                    log(sheet_name, f"GONE (sold/removed): {vin}", "red")
                    updates.append({
                        "range": cell_range(sheet_name, row_number, status_index, date_of_gone_index),
                        "values": [["gone", today]],
                    })
            else:
                log(sheet_name, "WARNING: no results scraped, skipping 'gone' check")

            if rows_to_append:
                self.google.add_row(sheet_name, rows_to_append)
            if updates:
                self.google.batch_update_values(updates)

        if changes_rows:
            self.google.add_row(CHANGES_SHEET_NAME, changes_rows)


from io import BytesIO
import img2pdf
from paths import window_sticker_pdfs_dir
class ConvertWindowStickerToPDF:

    def process_item(self, item, spider):
        image_bytes = item.body
        vin = item.vin
        search_name = item.search_name 
        if not image_bytes:
            log('ConvertWindowStickerPipeline', 'body is empty', 'red')
            return item 

        folder_path = Path(window_sticker_pdfs_dir / search_name)
        folder_path.mkdir(exist_ok=True, parents=True)
        pdf_file_path = f"{folder_path}/{vin}.pdf"
        pdf_bytes = img2pdf.convert(BytesIO(image_bytes))
        if pdf_bytes:
            with open(pdf_file_path, 'wb') as f:
                f.write(pdf_bytes)
                log("ConvertWindowStickerToPdf", f'process goes successfuly with {pdf_file_path}', 'green')

        return item 


        


            

           

            


