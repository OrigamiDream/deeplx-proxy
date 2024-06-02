import json
import random
import time
from typing import Optional

import aiohttp
from fastapi import HTTPException
from starlette import status

BASE_URL = 'https://www2.deepl.com/jsonrpc'
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "*/*",
    "x-app-os-name": "iOS",
    "x-app-os-version": "16.3.0",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "x-app-device": "iPhone13,2",
    "User-Agent": "DeepL-iOS/2.9.1 iOS 16.3.0 (iPhone13,2)",
    "x-app-build": "510265",
    "x-app-version": "2.9.1",
    "Connection": "keep-alive",
}


def num_i_letters(text: str) -> int:
    return text.count('i')


def generate_random_number() -> int:
    random.seed(time.time())
    return random.randint(8300000, 8399998)


def timestamp(i_count: int) -> int:
    ts = int(time.time() * 1000)
    if i_count == 0:
        return ts
    i_count += 1
    return ts - ts % i_count + i_count


async def translate(
        text: str,
        source_lang: str = 'auto',
        target_lang: str = 'en',
        num_alternatives: int = 3,
        proxy_address: Optional[str] = None):
    i_count = num_i_letters(text)
    id = generate_random_number()

    num_alternatives = max(min(3, num_alternatives), 0)

    form_data = {
        'jsonrpc': '2.0',
        'method': 'LMT_handle_texts',
        'id': id,
        'params': {
            'texts': [{'text': text, 'requestAlternatives': num_alternatives}],
            'splitting': 'newlines',
            'lang': {
                'source_lang_user_selected': source_lang,
                'target_lang': target_lang,
            },
            'timestamp': timestamp(i_count),
            'commonJobParams': {
                'wasSpoken': False,
                'transcribe_as': '',
            },
        },
    }
    form_data_string = json.dumps(form_data, ensure_ascii=False)
    if (id + 5) % 29 == 0 or (id + 3) % 13 == 0:
        form_data_string = form_data_string.replace('"method":"', '"method" : "', -1)
    else:
        form_data_string = form_data_string.replace('"method":"', '"method": "', -1)

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        async with session.post(BASE_URL, data=form_data_string, headers=HEADERS, proxy=proxy_address) as res:
            status_code = res.status
            if status_code != status.HTTP_200_OK:
                raise HTTPException(status_code, detail=await res.text())

            body = await res.json()
    result = body['result']['texts'][0]

    alternatives = [d['text'] for d in result['alternatives']]
    return result['text'], alternatives
