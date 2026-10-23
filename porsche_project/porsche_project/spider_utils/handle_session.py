
from pathlib import Path 
import sys 

base_dir = Path(__file__).resolve().parents[3]
if base_dir not in sys.path:
    sys.path.insert(0, str(base_dir))

from paths import session_file_dir
from utils.logger import log
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from typing import Any

async def accept_cookies_once(page: Page) -> None:
    
    try:
        await page.locator("uc-p-button.accept").get_by_role("button", name="Accept All").click(timeout=30_000)
        log('accept cookies', f'Cookie banner accepted, session saved to: {session_file_dir}', 'green')
    except PlaywrightTimeoutError:
        log('accept cookies', "Cookie banner not found, continuing without it", 'yellow')
        


def context_kwargs(use_session=True):
    kwargs: dict[str, Any] = {'viewport': {'width': 1920, 'height': 1000}, 'ignore_https_errors': True}
    if use_session and session_file_dir.exists():
        kwargs['storage_state'] = str(session_file_dir)
    return kwargs 