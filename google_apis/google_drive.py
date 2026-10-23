
import requests 
import sys 
from pathlib import Path 
from rich import print as pprint 

base_dir = Path(__file__).resolve().parents[1]
if base_dir not in sys.path:
    sys.path.insert(0, str(base_dir))

from dotenv import load_dotenv
from paths import dotenv_path
import os 
from utils.logger import log

load_dotenv(dotenv_path=dotenv_path)

class GoogleDriveClient:
    BASE_URL = 'https://api.nango.dev/proxy/drive/v3/files'
    def __init__(self, folder_id, connection_id, integeration_id, api_key) -> None:
        self.folder_id = folder_id 
        self.session = requests.Session()
        self.headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Provider-Config-Key": integeration_id,
                    "Connection-Id": connection_id,
                    'Accept': 'application/json'
                }
        self.session.headers.update(
            self.headers
        )

    @classmethod
    def from_env(cls):
        return cls(
            connection_id = os.environ['GOOGLE_DRIVE_CONNECTION_ID'],
            integeration_id = os.environ['GOOGLE_DRIVE_INTEGERATION_ID'],
            api_key = os.environ['GOOGLE_DRIVE_API_KEY'],
            folder_id = os.environ['GOOGLE_DRIVE_FOLDER_ID']
        )

    def _request(self, method, path="", **kwargs):
        response = self.session.request(method=method, url=f'{self.BASE_URL}{path}', **kwargs)

        try:
            response.raise_for_status()
        except Exception as e:
            log('google drive', f'An error at: {e} | response: {response.text}', 'red')
            return
        return response.json()
            
    
    def create_folder(self, name, parent_id=None):
        body = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id or self.folder_id]
        }

        return self._request('POST', json=body)


    def get_drive_files(self, folder_id=None):
        folder_id = folder_id or self.folder_id

        params = {
            'q': f"'{folder_id}' in parents and trashed = false",
            'fields': 'files(id,name,mimeType),nextPageToken'
        }

        return self._request('GET', params=params)


    def get_or_create_folder(self, name, parent_id):
        response = self.get_drive_files(folder_id=parent_id)

        if response is None:
            return

        for file in response.get('files', []):
            if (
                file.get('mimeType') == 'application/vnd.google-apps.folder'
                and file['name'].lower() == name.lower()
            ):
                return file

        response = self._request(
            'POST',
            json={
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
        )

        if response:
            return response


    def upload_file(
        self,
        name,
        body,
        parent_id,
        content_type='image/png'
    ):
        # Create the file metadata first.
        response = self._request(
            'POST',
            json={
                'name': name,
                'mimeType': content_type,
                'parents': [parent_id]
            }
        )

        if not response:
            return

        file_id = response['id']

        # Upload the actual file content to the created file.
        url = (
            'https://api.nango.dev/proxy/upload/drive/v3/files/'
            f'{file_id}'
        )

        try:
            upload_response = self.session.patch(
                url,
                params={'uploadType': 'media'},
                data=body,
                headers={'Content-Type': content_type}
            )
            upload_response.raise_for_status()
            return upload_response.json()

        except requests.RequestException as exc:
            log(
                'Google Drive',
                f'Failed to upload {name}: {exc}',
                'red'
            )
            return

    def get_or_create_file(self,name,body,parent_id,content_type):
        response = self.get_drive_files(folder_id=parent_id)

        if response is None:
            return

        for file in response.get('files', []):
            if (
                file.get('name', '').lower() == name.lower()
                and file.get('mimeType') != 'application/vnd.google-apps.folder'
            ):
                log(
                    'Google Drive',
                    f'File already exists: {name}',
                    'cyan'
                )
                return file

        return self.upload_file(
            name=name,
            body=body,
            parent_id=parent_id,
            content_type=content_type
        )
