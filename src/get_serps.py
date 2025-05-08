# coding: utf-8
import re
import json
import asyncio
import argparse
from typing import Awaitable, Callable, Generic, Sequence, TypeVar

import pickle
from time import perf_counter
from loguru import logger
from tqdm import tqdm

from httpx import AsyncClient, AsyncHTTPTransport, Limits


ENDPOINT = "http://api.prod.lan/api/magic/search/internal"

T = TypeVar('T')
R = TypeVar('R')
KT = TypeVar("KT")
VT = TypeVar("VT")


class Mapper(Generic[T, R]):
    def __init__(
        self,
        func: Callable[[T], Awaitable[R | None]],
        /,
        max_rps: int,
        max_workers: int | None = None,
        tag: str | None = None,
        backup_path: str | None = None,
        backup_size: int | None = None
    ) -> None:
        self._func = func
        self._max_rps = max_rps
        self._max_workers = max_workers or max_rps
        self._tag = tag or self._func.__name__.strip("_")
        self._queue = asyncio.Queue[T](maxsize=self._max_rps)
        self._backup_path = backup_path
        self._backup_size = backup_size
        self._pbar: tqdm
        self._n_omitted: int
        self._n_errors: int
        self._backup: bool

    async def do(self, items: Sequence[T]) -> list[R]:
        self._pbar = tqdm(total=len(items), desc=self._tag)
        self._n_omitted = self._n_errors = 0
        self._backup = not (self._backup_path is None or self._backup_size is None)
        result: list[R] = []

        with self._pbar:
            consumers = [
                asyncio.create_task(
                    self._process_items(store_to=result),
                    name=f"bm_{self._tag}_consumer_{i}",
                )
                for i in range(self._max_workers)
            ]

            await self._schedule_for_processing(items)
            await self._queue.join()

            for consumer in consumers:
                consumer.cancel()
            await asyncio.gather(*consumers, return_exceptions=True)

        return result

    async def _schedule_for_processing(self, items: Sequence[T]) -> None:
        chunk: list[T] = []
        for x in items:
            chunk.append(x)
            if len(chunk) >= self._max_rps:
                await self._schedule_and_wait(chunk)
                chunk = []
        if chunk:
            await self._schedule_and_wait(chunk)

    async def _process_items(self, *, store_to: list[R]) -> None:
        while True:
            item = await self._queue.get()
            try:
                result = await self._func(item)
            except Exception as exc:
                self._n_errors += 1
                logger.debug(
                    "An exception '{}' occured inside of the '{}' mapper: {}",
                    type(exc).__qualname__,
                    self._tag,
                    exc,
                )
            else:
                if result is None:
                    self._n_omitted += 1
                else:
                    store_to.append(result)
                    if store_to and self._backup and len(store_to) % self._backup_size == 0:
                        with open(self._backup_path, "wb") as fout:
                            pickle.dump(store_to, fout)

            self._queue.task_done()
            self._pbar.update(1)
            self._pbar.set_postfix(
                n_errors=self._n_errors,
                n_omitted=self._n_omitted,
            )

    async def _schedule_and_wait(self, chunk: list[T], /) -> None:
        start = perf_counter()
        for item in chunk:
            await self._queue.put(item)
        elapsed_time = perf_counter() - start

        if idle_time := max(0, 1 - elapsed_time):
            await asyncio.sleep(idle_time)


def get_search_api() -> AsyncClient:
    transport = AsyncHTTPTransport(retries=3)
    limits = Limits(
        max_connections=5,
        max_keepalive_connections=5
    )
    search_api = AsyncClient(
        base_url=ENDPOINT,
        transport=transport,
        limits=limits,
        params={
            "region_id": 50,
            "offset": 0,
            "age_more_18": 1,
            "sendStats": "false"
        },
    )
    return search_api

search_api = get_search_api()

async def process_query(q) -> dict:
    try:
        resp = await search_api.post(
            "search/search_plain",
            params={"q": q, "limit": 10}
        )
        return (q, resp.json())
    except Exception:
        return None


def read_queries(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
        
    result = []
    for key in data:
        item = data[key]
        result.append(item['query'])
        
    return result

def save_result(data, file_path):
    result = {}
    with open(file_path, 'w') as f:
        for i, item in enumerate(data):
            result[i] = {
                "query": item[0],
                "search_response": item[1]
            }
        json.dump(result, f)


def main(args):
    queries = read_queries(args.output_path)
    search_results = asyncio.run(Mapper(
        process_query,
        max_rps=1,
        max_workers=10,
    ).do(queries))
    save_result(search_results, args.output_path)

if __name__ == "__main__":
    logger.info("Start searching")
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_path', type=str)
    args = parser.parse_args()

    main(args)
