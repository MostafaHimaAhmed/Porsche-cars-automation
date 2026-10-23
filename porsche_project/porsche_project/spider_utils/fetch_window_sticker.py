
from pathlib import Path 
import sys 

base_dir = Path(__file__).resolve().parents[3]
if base_dir not in sys.path:
    sys.path.insert(0, str(base_dir))

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from utils.logger import log 
from typing import Any 
from porsche_project.spider_utils.sticker_analyzer import analyze_sticker
import os 
from dotenv import load_dotenv
from google import genai
from paths import dotenv_path
from rich import print 


async def open_sticker_window(page: Page, vin, max_retries: int = 3) -> dict[str, Any] | None:
        await page.wait_for_load_state('domcontentloaded')
        selector = 'button[data-testid="monroney-label-link"]'
        try:
            for attempt in range(1, max_retries + 1):
                button = page.locator(selector)

                # أول محاولة بس: لو الزرار مظهرش خلال 10 ثواني يبقى مفيش Sticker
                try:
                    await button.wait_for(state="visible", timeout=20_000)
                except PlaywrightTimeoutError:
                    if attempt == 1:
                        log('open sticker window', f'car [{vin}] has no Sticker Window', 'yellow')
                        return None
                    
                    # في المحاولات اللي بعدها الزرار كان موجود، فغيابه معناه إن الصفحة لسه بتحمّل
                    log('open sticker window', f'[{vin}] button missing on attempt {attempt}', 'yellow')
                    await page.reload()
                    continue

                try:
                    async with page.expect_response(
                        lambda r: 'monroneydownloadbucket' in r.url,
                        timeout=40_000,
                    ) as response_info:
                        await button.click()
                    response = await response_info.value
                    body = await response.body()

                    return {
                        'file_urls': [response.url],
                        'headers': await response.request.all_headers(),
                        'body': body

                    }

                except PlaywrightTimeoutError:
                    log('open sticker window', f'[{vin}] attempt {attempt}/{max_retries} timed out', 'yellow')
                    if attempt < max_retries:
                        await page.reload()

            log('fetching window sticker', f'After {max_retries} tries, failed to open Window sticker for [{vin}]', 'red')
            return {}

        except Exception as e:
            log('open sticker window', f'[{vin}] {e}', 'red')
            return {}
