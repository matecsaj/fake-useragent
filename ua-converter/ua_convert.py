#!/usr/bin/env python3
# Description: Convert the user-agents.json file to JSONlines and directly remaps the keys
# Author: Melroy van den Berg
import argparse
from collections.abc import Iterable
import gzip
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TypedDict, Optional
import json
import requests
from ua_parser import parse

from fake_useragent.utils import BrowserUserAgentData, find_browser_json_path

DEFAULT_URL = (
    "https://raw.githubusercontent.com/intoli/user-agents/main/src/user-agents.json.gz"
)


class SourceItem(TypedDict):
    """The schema for the source item that the source file must (at least) follow."""

    userAgent: str
    """The user agent string."""
    weight: float
    """Sampling probability for this user agent when random sampling. Currently has no effect."""
    deviceCategory: str
    """The device type for this user agent."""
    platform: str
    """System name for the user agent."""


def download_and_extract(source_url: str) -> list[SourceItem]:
    """Download the user-agents.json file from the given URL and extract it if necessary.

    Args:
        source_url (str): The URL to the user-agents.json file.

    Returns:
        list[SourceItem]: The source file loaded as a list of `SourceItem`s. In reality, the
            returned elements have more keys than the `SourceItem` schema, but we only use the
            keys defined in the schema.
    """
    response = requests.get(source_url)
    response.raise_for_status()

    if source_url.endswith(".gz"):
        with NamedTemporaryFile("wb") as temp_file:
            temp_file.write(response.content)

            with gzip.open(temp_file.name, "rb") as intermediate:
                contents = intermediate.read()
    else:
        contents = response.content

    return json.loads(contents)


def process_item(item: SourceItem) -> Optional[BrowserUserAgentData]:
    """Process a single item and return the transformed item."""
    # Parse the user agent string
    ua_result = parse(item["userAgent"])

    if not ua_result.user_agent:
        return None

    if ua_result.user_agent:
        browser_version = ".".join(
            part
            for part in [
                ua_result.user_agent.major,
                ua_result.user_agent.minor,
                ua_result.user_agent.patch,
                ua_result.user_agent.patch_minor,
            ]
            if part is not None
        )

        browser_version_major_minor = float(
            ".".join(
                part
                for part in [
                    ua_result.user_agent.major,
                    ua_result.user_agent.minor,
                ]
                if part is not None
            )
        )
    else:
        browser_version = None
        browser_version_major_minor = 0.0

    if ua_result.os:
        os_version = ".".join(
            part
            for part in [
                ua_result.os.major,
                ua_result.os.minor,
                ua_result.os.patch,
                ua_result.os.patch_minor,
            ]
            if part is not None
        )
    else:
        os_version = None

    return {
        "useragent": item["userAgent"],
        "percent": item["weight"] * 100,
        "type": item["deviceCategory"],
        "device_brand": ua_result.device.brand if ua_result.device else None,
        "browser": ua_result.user_agent.family if ua_result.user_agent else None,
        "browser_version": browser_version,
        "version": browser_version_major_minor,
        "os": ua_result.os.family if ua_result.os else None,
        "os_version": os_version,
        "system": item["platform"],
    }


def convert_useragents_formats(
    data: Iterable[SourceItem],
) -> list[BrowserUserAgentData]:
    new_data: list[BrowserUserAgentData] = []
    # Process data in parallel
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(process_item, item) for item in data}

        for future in as_completed(futures):
            try:
                result = future.result()
                if result is not None:
                    new_data.append(result)
            except Exception as exc:
                print(f"Generated an exception: {exc}")
                raise
    return new_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert Intoli's user agent data to our JSONL format."
    )

    input_group = parser.add_argument_group(
        "Input source", "Define where to get the source data from."
    )
    exclusive_group = input_group.add_mutually_exclusive_group(required=True)
    exclusive_group.add_argument(
        "-i",
        "--input",
        help="Input JSON file path (default: %(const)s)",
        nargs="?",
        const=Path("user-agents.json"),
        type=Path,
    )
    exclusive_group.add_argument(
        "-d",
        "--download",
        help=(
            "Download source file from URL. Supports gzipped and non-gzipped files "
            "(default: %(const)s)"
        ),
        nargs="?",
        const=DEFAULT_URL,
        type=str,
    )

    parser.add_argument(
        "-o",
        "--output",
        help="Output JSONL file. Default overwirtes current package file (default: %(default)s)",
        default=find_browser_json_path(),
        type=Path,
    )

    parser.add_argument(
        "-l",
        "--parse-limit",
        help="How many of the fetched user agent lines to parse (default: %(default)s)",
        default=None,
        type=lambda limit: None if limit is None else int(limit),
    )

    args = parser.parse_args()

    if args.download:
        print(f"Downloading data from {args.download}")
        data = download_and_extract(args.download)
    else:
        print(f"Reading data from {args.input}")
        with open(args.input, "r") as f:
            data = json.load(f)

    if args.parse_limit:
        print(f"Parsing only the first {args.parse_limit} items")
        data = data[: args.parse_limit]

    print("Processing data...")
    jsonl_converted = convert_useragents_formats(data)

    print(f"Writing data to {args.output}")
    with open(args.output, "w") as f:
        for item in jsonl_converted:
            f.write(json.dumps(item) + "\n")
    print("Done!")
