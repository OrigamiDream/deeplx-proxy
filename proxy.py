import math
import random
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ProxyInfo:
    address: str
    is_working: bool
    score: int

    def add_success(self):
        self.score = max(-50, min(50, self.score + 1))
        if self.is_working:
            return
        self.is_working = True

    def add_failure(self):
        self.score = max(-50, min(50, self.score - 1))


def _create_proxy_info_from_proxy(proxy: str) -> ProxyInfo:
    return ProxyInfo(proxy, is_working=False, score=0)


class ProxyHandler:
    def __init__(self, proxies: List[str]):
        self._proxies = [
            _create_proxy_info_from_proxy(proxy) for proxy in proxies
        ]
        self._init = True

    def is_service_available(self):
        return self._init

    def set_service_available(self):
        self._init = True

    def proxies(self) -> List[ProxyInfo]:
        return self._proxies

    def _recalibrate(self):
        self._proxies.sort(key=lambda p: p.score, reverse=True)

    def choose(self, k: int = 5) -> List[ProxyInfo]:
        self._recalibrate()

        if not self._proxies:
            return []
        return self._proxies[0:min(len(self._proxies), k)]

    def choose_one(self, k: int = 5) -> Optional[ProxyInfo]:
        self._recalibrate()
        proxies = self.choose(k)
        min_score = min(proxy.score for proxy in proxies)
        total_score = sum(proxy.score - min_score for proxy in proxies)
        if total_score:
            populations = []
            for proxy in proxies:
                prob = ((proxy.score - min_score) / max(total_score, 1)) * 1000
                populations += [proxy] * max(5, int(math.ceil(prob)))
        else:
            populations = proxies
        return random.choice(populations)

    def severe(self, proxy: ProxyInfo):
        if proxy.is_working or proxy not in self._proxies:
            return
        self._proxies.remove(proxy)
