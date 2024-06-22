from typing import Dict, List, Optional

import requests
import os
import urllib.parse
import multiprocessing
import traceback
import time

from cps import logger
from cps.services.Metadata import MetaRecord, MetaSourceInfo, Metadata


log = logger.create()


BGM_ACCESS_TOKEN = os.getenv("BGM_ACCESS_TOKEN")
META_PROVIDER_BGM_THREAD_POOL = os.getenv("META_PROVIDER_BGM_THREAD_POOL", 8)
META_PROVIDER_BGM_TAG_LOWEST_USER_CNT = os.getenv("META_PROVIDER_BGM_TAG_LOWEST_USER_CNT", 5)
META_PROVIDER_BGM_TAG_MAX_CNT = os.getenv("META_PROVIDER_BGM_TAG_MAX_CNT", 10)

characters_to_clean = ["\u200e"]


def clean_string(s: str) -> str:
    for c in characters_to_clean:
        s = s.replace(c, "")
    return s


class Bangumi(Metadata):
    __name__ = "Bangumi"
    __id__ = "bangumi"
    DESCRIPTION = "Bangumi"
    META_URL = "https://bgm.tv/"
    BOOK_URL = "https://bgm.tv/subject/"

    def search(
        self, query: str, generic_cover: str = "", locale: str = "en"
    ) -> Optional[List[MetaRecord]]:
        val = list()
        if self.active:
            try:
                results = requests.get(f"https://api.bgm.tv/search/subject/{urllib.parse.quote(query)}?type=1&responseGroup=small&max_results=10")
                results.raise_for_status()
            except Exception as e:
                log.warning(e)
                return []

            queue = []

            try:
                results = results.json()
            except Exception as e:
                log.warning(e)
                log.warning("Bangumi: failed to parse search results (possibly no match, try to change query)")
                return []

            for result in results["list"]:
                queue.append(result["id"])


            with multiprocessing.Pool(META_PROVIDER_BGM_THREAD_POOL) as pool:
                ret = pool.map(self._query_subject, queue)
                val.extend([i for i in ret if i is not None])

            # get children to form a new queue
            with multiprocessing.Pool(META_PROVIDER_BGM_THREAD_POOL) as pool:
                ret = pool.map(self._get_children, queue)
                queue = [i for i in ret if i is not None]
                queue = [item for sublist in queue for item in sublist]

            # then query them again
            with multiprocessing.Pool(META_PROVIDER_BGM_THREAD_POOL) as pool:
                ret = pool.map(self._query_subject, queue)
                val.extend([i for i in ret if i is not None])

        return val


    def _request_headers(self):
        headers = {
            'accept': 'application/json',
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }
        if BGM_ACCESS_TOKEN is not None:
            headers['Authorization'] = f'Bearer {BGM_ACCESS_TOKEN}'
        return headers


    def _query_subject(self, subject_id: int) -> Optional[MetaRecord]:
        try:
            response = requests.get(f'https://api.bgm.tv/v0/subjects/{subject_id}', headers=self._request_headers())
            response.raise_for_status()
        except Exception as e:
            log.warning(e)
            return None

        data = response.json()

        try:
            record = MetaRecord(
                id=subject_id,
                title=self._parse_title(data),
                authors=self._parse_author(data),
                url=f'https://bgm.tv/subject/{subject_id}',
                source=MetaSourceInfo(
                    id=self.__id__,
                    description=f"{self.__name__} {self._parse_source_platform(data)}",
                    link=self.META_URL
                ),
                cover=self._parse_cover(data),
                description=self._parse_description(data),
                series=self._parse_series(data),
                series_index=self._parse_series_index(data),
                identifiers=self._parse_identifiers(data),
                publisher=self._parse_publisher(data),
                publishedDate=self._parse_published_date(data),
                rating=self._parse_rating(data),
                languages=self._parse_languages(data),
                tags=self._parse_tags(data)
            )
        except Exception as e:
            log.warning(e)
            log.warning(traceback.format_exc())
            return None

        return record



    def _get_children(self, subject_id: int) -> List[int]:
        try:
            response = requests.get(f'https://api.bgm.tv/v0/subjects/{subject_id}/subjects', headers=self._request_headers())
            response.raise_for_status()
        except Exception as e:
            log.warning(e)
            return None

        data = response.json()
        ret_ids = []
        
        try:
            ret_ids = [
                item["id"] for item in data if item["type"] == 1
            ]
        except Exception as e:
            log.warning(e)
            log.warning(traceback.format_exc())

        return ret_ids


    def _parse_title(self, data):
        if data["name_cn"] == "":
            return data["name"]
        return data["name_cn"]


    def _parse_item_from_keys(self, data, keys, only_one=True):
        """
        keys is a list of keys to match in the infobox.
        the higher the key is in the list, the higher the priority.
        """
        matched = {}
        for item in data:
            if item["key"] in keys:
                value = item["value"]
                if isinstance(value, list):
                    matched[item["key"]] = [clean_string(i["v"]) for i in value]
                else:
                    matched[item["key"]] = clean_string(item["value"])

        ret = []
        for key in keys:
            if key in matched:
                if only_one:
                    if isinstance(matched[key], list):
                        return matched[key][0]
                    return matched[key]
                else:
                    if isinstance(matched[key], list):
                        ret.extend(matched[key])
                    else:
                        ret.append(matched[key])
        if only_one:
            return None
        return ret


    def _parse_source_platform(self, data):
        platform = data["platform"]
        if 'series' in data and data['series']:
            platform += "系列"
        return platform


    def _parse_author(self, data):
        return self._parse_item_from_keys(data["infobox"], ["作者", "作画", "插图", "插画"], only_one=False)


    def _parse_cover(self, data):
        return clean_string(data["images"]["large"])


    def _parse_description(self, data):
        return clean_string(data["summary"])


    def _parse_series(self, data):
        return None


    def _parse_series_index(self, data):
        return None


    def _parse_identifiers(self, data):
        identifiers = {
            "bangumi": data["id"],
        }
        isbn = self._parse_item_from_keys(data["infobox"], ["ISBN"], only_one=True)
        if isbn is not None:
            identifiers["isbn"] = isbn
        return identifiers


    def _parse_publisher(self, data):
        return self._parse_item_from_keys(data["infobox"], ["文库", "出版社"], only_one=True)


    def _parse_published_date(self, data):
        timestr = self._parse_item_from_keys(data["infobox"], ["发售日", "开始"], only_one=True)
        if timestr is None:
            return None

        def get_formated_date(t):
            return time.strftime("%Y-%m-%d", t)
        
        timestr = timestr.replace(' ', '') \
            .replace('\n', '') \
            .replace('\t', '') \
            .replace('\r', '')
        if timestr == "": return None

        try:
            ts = time.strptime(timestr, "%Y-%m-%d")
            return get_formated_date(ts)
        except: pass
        try:
            ts = time.strptime(timestr, "%Y/%m/%d")
            return get_formated_date(ts)
        except: pass
        try:
            ts = time.strptime(timestr, "%Y年%m月%d日")
            return get_formated_date(ts)
        except: pass
        log.warning(f"Failed to parse date: {timestr}")
        return None


    def _parse_rating(self, data):
        return round(data["rating"]["score"] / 2)


    def _parse_languages(self, data):
        return None


    def _parse_tags(self, data):
        ret = []
        for tag in data["tags"]:
            if tag["count"] >= META_PROVIDER_BGM_TAG_LOWEST_USER_CNT:
                ret.append(clean_string(tag["name"]))
        ret = ret[:META_PROVIDER_BGM_TAG_MAX_CNT]
        return ret


# testing
if __name__ == "__main__":
    bgm = Bangumi()
    queries = ["义妹生活", "地下30mの蜜月を…"]
    
    for query in queries:
        print(f"Searching for {query}")
        results = bgm.search(query)
        for result in results:
            print(result)
        print("====================================")
