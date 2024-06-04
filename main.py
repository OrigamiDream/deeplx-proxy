import asyncio
import logging
import os.path
from typing import List, Optional

import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from pydantic_settings import BaseSettings

import deeplx
from proxy import ProxyHandler, ProxyInfo


class Settings(BaseSettings):
    proxy_file: str

    class Config:
        env_file = '.env'


class TranslateRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str
    max_retry: int = -1
    num_proxies: int = 5
    deeplx_url: str = 'https://api.deeplx.org/translate'


class TranslateResponse(BaseModel):
    data: str
    alternatives: List[str]
    source_lang: str
    target_lang: str


logging.basicConfig(level=logging.INFO)

settings = Settings()

if not os.path.exists(settings.proxy_file):
    raise ValueError('Proxy file is not specified. Specify a TXT file with a list of proxy addresses.')

with open(settings.proxy_file, 'r') as f:
    proxies = f.read().splitlines()
    proxies = [p.strip() for p in proxies if len(p) > 0 and not p.strip().startswith('#')]
    proxies = list(set(proxies))
    logging.info("Total {} proxies have been registered.".format(len(proxies)))
proxy_handler = ProxyHandler(proxies)

app = FastAPI()


@app.get('/')
async def main():
    return {'data': 'This is DeepLX service with dynamic proxy balancing.'}


async def _attempt_via_proxy(request: TranslateRequest, override_proxy: Optional[ProxyInfo] = None):
    max_retry = request.max_retry
    run_forever = max_retry == -1

    retval = None
    while max_retry > 0 or run_forever:
        if not run_forever:
            max_retry -= 1

        if override_proxy is None:
            proxy = proxy_handler.choose_one(request.num_proxies)
        else:
            proxy = override_proxy

        try:
            retval = await deeplx.translate(
                request.deeplx_url,
                request.text,
                request.source_lang,
                request.target_lang,
                proxy_address=proxy.address
            )
            logging.info("Proxy {} is working.".format(proxy.address))
            proxy.add_success()
            break

        # when the proxy is not accessible.
        except (aiohttp.ClientHttpProxyError,
                aiohttp.ClientProxyConnectionError,
                aiohttp.ClientOSError,
                aiohttp.ClientResponseError) as e:
            logging.warning("Proxy {} is not accessible for error {}: {}."
                            .format(proxy.address, e.__class__.__name__, str(e)))
            proxy_handler.severe(proxy)
            continue

        # when the proxy temporarily failed to access.
        except (aiohttp.ClientPayloadError,
                aiohttp.ClientConnectorError,
                asyncio.TimeoutError,
                aiohttp.ServerDisconnectedError) as e:
            logging.warning("Proxy {} is temporarily disabled for error {}: {}."
                            .format(proxy.address, e.__class__.__name__, str(e)))
            proxy.add_failure()
            continue

        # other exception happens during requests
        except BaseException as e:
            logging.warning("Proxy {} is temporarily disabled for error.".format(proxy.address))
            logging.exception(e)
            proxy.add_failure()
            continue
    return retval


@app.post('/translate', response_model=TranslateResponse)
async def translate(request: TranslateRequest):
    retval = await _attempt_via_proxy(request)

    if retval is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Failed to get translation from DeepL service')

    text, alternatives = retval
    return TranslateResponse(
        code="200",
        data=text,
        alternatives=alternatives,
        source_lang=request.source_lang,
        target_lang=request.target_lang,
    )


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=1189)
