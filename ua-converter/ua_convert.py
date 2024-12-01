#!/usr/bin/env python3
# Description: Convert the user-agents.json file to JSONlines and directly remaps the keys
# Author: Melroy van den Berg
import json
from ua_parser import parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from fake_useragent.utils import find_browser_json_path
from pathlib import Path


def process_item(item):
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
        "browser_version_major_minor": browser_version_major_minor,
        "os": ua_result.os.family if ua_result.os else None,
        "os_version": os_version,
        "platform": item["platform"],
    }


def convert_useragents_file_format(source: Path, destination: Path) -> None:
    """Convert the `source` file in Intoli's format to a JSONL file in our format in `destination`.

    Args:
        source (Path): The path to the file with updated user agent data. We use Intoli's
            [user-agents](https://github.com/intoli/user-agents) library, so this file must comply
            with their format.
        destination (Path): Where to output the JSONL converted to our format.
    """
    print(f"Reading data from {source}.")
    with open(source, "r") as f:
        data = json.load(f)

    new_data = []
    # Process data in parallel
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(process_item, item) for item in data}
        print("Processing data...")
        for future in as_completed(futures):
            try:
                result = future.result()
                if result is not None:
                    new_data.append(result)
            except Exception as exc:
                print(f"Generated an exception: {exc}")
                raise

    print(f"Writing data to {destination}")
    with open(destination, "w") as f:
        for item in new_data:
            f.write(json.dumps(item) + "\n")

    print("Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert Intoli's user agent data to our JSONL format.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-i",
        "--input",
        help="Input JSON file.",
        default=Path("user-agents.json"),
        type=Path,
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output JSONL file.",
        default=find_browser_json_path(),
        type=Path,
    )
    args = parser.parse_args()

    convert_useragents_file_format(args.input, args.output)
