
porsche_spider_name = 'porsche_spider'
chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe"
profile_dir = "E:/CdpChrome"
chrome_debugging_port = 9222
tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

nago_base_url = 'https://api.nango.dev/proxy/v4/spreadsheets'
config_sheet_name = 'config'

SEARCH_SHEETS_HEADERS = [
    "vin", "model", "inner_color", "outer_color", "model_date",
    "owners_count", "price", "mileage", "dealer", "city",
    "postal_code", "street", "first_seen", "last_seen", 'url', 'window_sticker', 'status', 'date_of_gone'
]


SHEETS = {
    'options': ['vin', 'option', 'price'],
    'changes': ['vin', 'date', 'old_price', 'new_price']
}

OPTIONS_SHEET_NAME = 'options'

OPTIONS_SHEET_HEADERS = ['vin', 'option', 'price']

CHANGES_SHEET_NAME = 'changes'
CHANGES_SHEET_HEADERS = ['vin', 'date', 'old_price', 'new_price']

BASE_GOOGLE_DRIVE_FOLDERS = ['images', 'pdfs']