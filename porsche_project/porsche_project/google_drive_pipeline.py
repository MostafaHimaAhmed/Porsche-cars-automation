
from pathlib import Path
import sys
from io import BytesIO
from collections import defaultdict

from PIL import Image

base_dir = Path(__file__).resolve().parents[3]

if base_dir not in sys.path:
    sys.path.insert(0, str(base_dir))

from google_apis.google_drive import GoogleDriveClient
from constants import BASE_GOOGLE_DRIVE_FOLDERS
from utils.logger import log


class UploadToGoogleDrive:
    def __init__(self):
        self.client = GoogleDriveClient.from_env()
        self.folders = {}
        self.data = defaultdict(list)

    def open_spider(self, spider):
        # Create images and pdf inside stickers.
        for name in BASE_GOOGLE_DRIVE_FOLDERS:
            folder = self.client.get_or_create_folder(name, parent_id=self.client.folder_id)

            if folder:
                self.folders[name.lower()] = folder['id']
                log( 'Google Drive',f'Folder ready: {name}','green')

    def process_item(self, item, spider):
        body = item.body
        vin = item.vin
        search_name = item.search_name

        if not body:
            log( 'Google Drive', f'Failed to upload {vin}: empty image','red')
            return item

        if not search_name or not vin:
            log('Google Drive','Missing search_name or VIN','red')
            return item

        self.data[search_name].append({'vin': vin,'body': body})

        return item

    def close_spider(self, spider):
        images_parent_id = self.folders.get('images')
        pdf_parent_id = self.folders.get('pdfs')

        if not images_parent_id or not pdf_parent_id:
            log( 'Google Drive','Images or PDF parent folder is missing','red')
            return

        for search_name, items in self.data.items():
            # Create search_name folders in both locations.
            image_folder = self.client.get_or_create_folder(search_name,parent_id=images_parent_id)

            pdf_folder = self.client.get_or_create_folder( search_name,parent_id=pdf_parent_id)

            if not image_folder or not pdf_folder:
                log('Google Drive',f'Failed to prepare folders: {search_name}','red')
                continue

            image_folder_id = image_folder['id']
            pdf_folder_id = pdf_folder['id']

            for item in items:
                vin = item['vin']
                body = item['body']

                try:
                    # Convert image bytes to PDF bytes.
                    with Image.open(BytesIO(body)) as image:
                        image = image.convert('RGB')

                        pdf_buffer = BytesIO()
                        image.save(pdf_buffer, format='PDF')
                        pdf_body = pdf_buffer.getvalue()

                    # Upload image only if it doesn't exist.
                    image_response = self.client.get_or_create_file(
                        name=f'{vin}.png',
                        body=body,
                        parent_id=image_folder_id,
                        content_type='image/png'
                    )

                    # Upload PDF only if it doesn't exist.
                    pdf_response = self.client.get_or_create_file(
                        name=f'{vin}.pdf',
                        body=pdf_body,
                        parent_id=pdf_folder_id,
                        content_type='application/pdf'
                    )

                    if image_response and pdf_response:
                        log(
                            'Google Drive',
                            f'Files checked successfully: {vin}',
                            'green'
                        )
                    else:
                        log(
                            'Google Drive',
                            f'One or more files failed: {vin}',
                            'red'
                        )
                except Exception as exc:
                    log(
                        'Google Drive',
                        f'Failed to process {vin}: {exc}',
                        'red'
                    )
