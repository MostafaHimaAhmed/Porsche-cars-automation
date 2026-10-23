
from pathlib import Path 
import sys 

base_dir = Path(__file__).resolve().parents[1]
if base_dir not in sys.path:
    sys.path.insert(0, str(base_dir))

from constants import nago_base_url 
from paths import dotenv_path
import requests
import os 
from urllib.parse import quote
from utils.logger import log
from dotenv import load_dotenv

load_dotenv(dotenv_path=dotenv_path)

class GoogleSheetsApi:
    
    def __init__(self, sheet_id, connection_id, integration_id, api_key) -> None:
        self.base_url = f'{nago_base_url}/{sheet_id}'
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Provider-Config-Key": integration_id,
                'Connection-Id': connection_id,
                'Authorization': f'Bearer {api_key}'
            }
        )

    @classmethod
    def from_env(cls):
        return cls(
            sheet_id = os.environ['SHEET_ID'],
            connection_id = os.environ['NAGO_CONNECTION_ID'],
            integration_id = os.environ['NAGO_INTERGRATOIN_ID'],
            api_key = os.environ['NAGO_API_KEY']
        )


    def _request(self, method, path='', **kwargs):
        response = self.session.request(method=method, url=f"{self.base_url}{path}", timeout=40, **kwargs)

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            log('Google Sheets', f'Error: {e} | response {response.text}') 
            return
        return response.json()

    def get_rows(self, sheet_name):
        rows = self._request('GET', f'/values/{quote(sheet_name)}') 
        if rows:
            return rows.get('values', [])
        return []

    def create_blank_sheet(self, sheet_name):
        """
            it returns the new sheet id
        """
        body = {'requests': [{'addSheet': {'properties': {'title': sheet_name}}}]}
        sheet_id = self._request('POST', ':batchUpdate', json=body)
        log('Sheets', f'✎ Creating sheet "{sheet_name}"...', 'green')
        return sheet_id

    def get_sheet_titles(self):
        response = self._request("GET")
        if response:
            return [title['properties']['title'] for title in response.get('sheets', [])]

    def add_row(self, sheet_name, rows: list[list], ):
        params = {'valueInputOption': "USER_ENTERED"}
        body={'values':rows}
        self._request('POST', f"/values/{quote(sheet_name)}:append", params=params, json=body)
        log('Sheets', f'✓ {len(rows)} row(s) appended → {sheet_name}\n', 'green')

    def batch_update_values(self,data: list[dict],value_input_option: str = "USER_ENTERED",chunk_size: int = 500,) -> int:
        """"
        Update many cells in a few requests. Returns how many cells were updated.
        data = [{"range": "'My Sheet'!C3", "values": [[75000]]}, ...]
        """
        updated = 0
        for start in range(0, len(data), chunk_size):
            chunk = data[start:start + chunk_size]
            result = self._request(
                "POST",
                "/values:batchUpdate",
                json={"valueInputOption": value_input_option, "data": chunk},
            )
            updated += (result or {}).get("totalUpdatedCells", 0)
        return updated


