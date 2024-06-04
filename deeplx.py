from typing import Optional

import aiohttp
from fastapi import HTTPException
from starlette import status


async def translate(
        deeplx_url: str,
        text: str,
        source_lang: str = 'auto',
        target_lang: str = 'en',
        proxy_address: Optional[str] = None):

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        headers = {
            'Content-Type': 'application/json',
        }
        payload = {
            'text': text,
            'source_lang': source_lang,
            'target_lang': target_lang,
        }
        async with session.post(deeplx_url, headers=headers, json=payload, proxy=proxy_address) as res:
            status_code = res.status
            if status_code != status.HTTP_200_OK:
                raise HTTPException(status_code, detail=await res.text())

            body = await res.json()
    return body['data'], body.get('alternatives', [])
