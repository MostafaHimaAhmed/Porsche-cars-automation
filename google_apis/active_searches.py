
from pathlib import Path 
import sys 

base_dir = Path(__file__).resolve().parents[1]
if base_dir not in sys.path:
    sys.path.insert(0, str(base_dir))


from google_apis.google_sheets_api import GoogleSheetsApi
from constants import config_sheet_name
from utils.logger import log 
from constants import SEARCH_SHEETS_HEADERS


client = GoogleSheetsApi.from_env()
sheets = client.get_sheet_titles()


def load_active_searches():
    searches = []

    response = client.get_rows(config_sheet_name)
    if not response:
        log('Load active searches', f'{config_sheet_name} is empty', 'yellow')
        return []

    if len(response) == 1: # That means there is just headers
        log('load active searches', f'{config_sheet_name} has just headers', 'yellow')
        return []
    
    header, *rows = response
    search_name_index = header.index('search_name')
    is_active_index = header.index('is_active')
    url_index = header.index('url')

    for row in rows:
        try:
            is_active = row[is_active_index]
            if not is_active.lower() == 'true':
                continue

            search_name = row[search_name_index]
            url = row[url_index]

            # Create a new sheet if it does not exist and its header
            if search_name not in sheets:
                client.create_blank_sheet(search_name)
                client.add_row(search_name, [SEARCH_SHEETS_HEADERS])
            else:
                log('Sheet', f'{search_name} sheet is already existing', 'blue')
                
            
            searches.append({'search_name': search_name, 'url': url})
        except Exception as e:
            log('load active searches', f'Error at: {e}', 'red')

    log('searches', f'Found {len(searches)} active searches in {config_sheet_name}', 'blue')
    return searches
