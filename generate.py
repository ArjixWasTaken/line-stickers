from typing import Literal, TypedDict
from bs4 import BeautifulSoup
from session import SessionWithUrlBase

import os
import json
import requests

requests.Session = SessionWithUrlBase
session = requests.Session("https://store.line.me")

soup = BeautifulSoup(session.get("/stickershop/home/general/en").text, "html.parser")
official_categories: dict[str, int] = dict(
    [
        [x.text.strip(), int(x["href"].split("=")[1])]
        for x in soup.select('[href*="?category="]')
    ]
)

soup = BeautifulSoup(session.get("/stickershop/home/user/en").text, "html.parser")
creator_categories: dict[str, int] = dict(
    [
        [x.text.strip(), int(x["href"].split("=")[1])]
        for x in soup.select('[href*="top_creators"][href*="?"]')
    ]
)


class StickerPack(TypedDict):
    title: str
    id: int


def get_sticker_packs(
    category_id: int, kind: Literal["top", "top_creators"] = "top"
) -> list[StickerPack]:
    next_page = "1"
    sticker_packs = []

    while 1:
        soup = BeautifulSoup(
            session.get(
                f"/stickershop/showcase/{kind}/en",
                params={"category": category_id, "page": next_page},
            ).text,
            "html.parser",
        )
        sticker_packs.extend(
            (
                {
                    "title": " ".join(x.select_one("p").text.split()),
                    "id": int(
                        x.select_one("a")["href"].split("product/")[1].split("/")[0]
                    ),
                    "img": x.select_one("img")["src"],
                }
                for x in soup.select('[class$="List"] > [class$="Ul"] > [class$="Li"]')
            )
        )

        anchor = soup.select_one('nav[class$="Pagination"] > a[class$="Next"][href]')
        if not anchor:
            break

        next_page = str(anchor["href"].split("&page=")[1])

    return sticker_packs


def get_pack(pack_id: int):
    soup = BeautifulSoup(session.get(f"/stickershop/product/{pack_id}/en").text)
    stickers = soup.select(
        '[class$="StickerList"] > [class*="StickerPreviewItem"][data-preview]'
    )

    return {
        "title": soup.select_one('[class$="Sticker"] [class$="Head"] > [class$="Ttl"]'),
        "about": soup.select_one('[class$="Sticker"] p[class$="Txt"]'),
        "stickers": [json.loads(x["data-preview"]) for x in stickers],
    }


if not os.path.exists("data"):
    os.mkdir("data")

os.chdir("data")

official_sticker_packs = {}

count = 0
n = len(official_categories.keys())

for name, category_id in official_categories.items():
    count += 1
    print(f"Getting official sticker packs ({str(count).zfill(2)}/{n}) - {name}")
    official_sticker_packs[category_id] = {
        "title": name,
        "id": category_id,
        "packs": get_sticker_packs(category_id, "top"),
    }

with open("official_sticker_packs.json", "w") as f:
    json.dump(official_sticker_packs, f)

creator_sticker_packs = {}

count = 0
n = len(creator_categories.keys())

for name, category_id in creator_categories.items():
    count += 1
    print(f"Getting creator stickers packs ({str(count).zfill(2)}/{n}) - {name}")
    creator_sticker_packs[category_id] = {
        "title": name,
        "id": category_id,
        "packs": get_sticker_packs(category_id, "top_creators"),
    }

with open("creator_sticker_packs.json", "w") as f:
    json.dump(creator_sticker_packs, f)
