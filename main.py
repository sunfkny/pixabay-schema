import datetime
import pathlib
import shelve
from argparse import ArgumentParser
from typing import Literal

import bs4
import pandas as pd
from curl_cffi import requests
from pydantic import BaseModel, Field, TypeAdapter
from tenacity import retry, stop_after_attempt, wait_fixed

session = requests.Session()


class ThingModel(BaseModel):
    context_: Literal["http://schema.org"] = Field(alias="@context")
    type_: str = Field(alias="@type")
    model_config = {"extra": "allow"}


class ImageObjectModel(BaseModel):
    context_: Literal["http://schema.org"] = Field(alias="@context")
    type_: Literal["ImageObject"] = Field(alias="@type")
    datePublished: datetime.datetime
    model_config = {"extra": "allow"}


SchemaModel = ImageObjectModel | ThingModel
SchemaModelAdapter = TypeAdapter[SchemaModel](SchemaModel)


def get_published_date_from_response(response: str):
    soup = bs4.BeautifulSoup(response, "html.parser")
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        schema_model = SchemaModelAdapter.validate_json(script.get_text())
        if isinstance(schema_model, ImageObjectModel):
            return schema_model.datePublished

    raise ValueError("No datePublished found")


def is_pixabay_url(url) -> bool:
    if not url:
        return False
    if not isinstance(url, str):
        return False
    return url.startswith("https://pixabay.com/photos/")


PIXABAY_CACHE_SHELVE = "pixabay_cache.shelve.sqlite3"


@retry(stop=stop_after_attempt(10), wait=wait_fixed(1))
def get_published_date_from_url(url: str):
    if not is_pixabay_url(url):
        return None
    with shelve.open(PIXABAY_CACHE_SHELVE) as cache:
        published_date: datetime.datetime | None = cache.get(url)
        if published_date:
            return published_date.astimezone().replace(tzinfo=None)

    print(f"Getting published date from {url}")

    try:
        r = session.get(url, impersonate="chrome")
    except requests.exceptions.RequestException as e:
        if e.code == 23:
            raise KeyboardInterrupt
        raise

    r.raise_for_status()
    response = r.text
    published_date = get_published_date_from_response(response)
    print(f"Published Date: {published_date}")

    with shelve.open(PIXABAY_CACHE_SHELVE) as cache:
        cache[url] = published_date

    return published_date.astimezone().replace(tzinfo=None)


class Args(BaseModel):
    input_file: pathlib.Path
    output_file: pathlib.Path
    link_col: str
    published_date_col: str


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "-i",
        "--input_file",
        type=pathlib.Path,
        help="输入文件",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output_file",
        type=pathlib.Path,
        help="保存路径",
        required=True,
    )
    parser.add_argument(
        "--link_col",
        help="链接字段名",
        type=str,
        default="link",
    )
    parser.add_argument(
        "--published_date_col",
        help="发布日期字段名",
        type=str,
        default="published_date",
    )

    args = parser.parse_args()
    args = Args.model_validate(args, from_attributes=True)

    df = pd.read_excel(args.input_file)
    if args.link_col not in df.columns:
        raise ValueError(f"{args.link_col!r}列不存在")

    # df[args.published_date_col] = df[args.link_col].apply(get_published_date_from_url)
    links = df[args.link_col].to_list()
    for index, link in enumerate(links):
        print(f"progress: {index + 1}/{len(links)}")
        df.at[index, args.published_date_col] = get_published_date_from_url(link)
    df.to_excel(args.output_file, index=False)


if __name__ == "__main__":
    main()
