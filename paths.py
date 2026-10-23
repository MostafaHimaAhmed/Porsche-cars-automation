from pathlib import Path 


base_dir = Path(__file__).parent 
spider_base_dir = base_dir / 'porsche_project' / 'porsche_project'
dotenv_path = base_dir / '.env'

session_folder_dir = base_dir / 'session'
session_folder_dir.mkdir(parents=True, exist_ok=True)

session_file_dir = session_folder_dir / 'session.json'

window_sticker_base_dir = base_dir / 'stickers'
window_sticker_base_dir.mkdir(exist_ok=True, parents=True)

window_sticker_images_dir = window_sticker_base_dir / 'images'
window_sticker_images_dir.mkdir(parents=True, exist_ok=True)

window_sticker_pdfs_dir =  window_sticker_base_dir/ 'pdfs'
window_sticker_pdfs_dir.mkdir(exist_ok=True, parents=True)

options_file = window_sticker_base_dir / 'options.json'
