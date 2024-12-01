"""General utils for the fake_useragent package."""

import json
import sys
from typing import TypedDict, Union

# We need files() from Python 3.10 or higher
if sys.version_info >= (3, 10):
    import importlib.resources as ilr
else:
    import importlib_resources as ilr

from pathlib import Path

from fake_useragent.errors import FakeUserAgentError
from fake_useragent.log import logger


class BrowserUserAgentData(TypedDict):
    """The schema for the browser user agent data that the `browsers.json` file must follow."""

    useragent: str
    """The user agent string."""
    percent: float
    """Sampling probability for this user agent when random sampling. Currently has no effect."""
    type: str
    """The device type for this user agent."""
    system: str
    """System name for the user agent."""
    browser: str
    """Browser name for the user agent."""
    version: float
    """Version of the browser."""
    os: str
    """OS name for the user agent."""


def find_browser_json_path() -> Path:
    """Find the path to the browsers.json file.

    Returns:
        Path: Path to the browsers.json file.

    Raises:
        FakeUserAgentError: If unable to find the file.
    """
    try:
        file_path = ilr.files("fake_useragent.data").joinpath("browsers.json")
        return Path(str(file_path))
    except Exception as exc:
        logger.warning(
            "Unable to find local data/json file using importlib-resources. Try pkg-resource.",
            exc_info=exc,
        )
        try:
            from pkg_resources import resource_filename

            return Path(resource_filename("fake_useragent", "data/browsers.json"))
        except Exception as exc2:
            logger.warning(
                "Could not find local data/json file using pkg-resource.",
                exc_info=exc2,
            )
            raise FakeUserAgentError("Could not locate browsers.json file") from exc2


def load() -> list[BrowserUserAgentData]:
    """Load the included `browser.json` file into memory.

    Raises:
        FakeUserAgentError: If unable to load or parse the data.

    Returns:
        list[BrowserUserAgentData]: The list of browser user agent data.
    """
    data = []
    try:
        json_path = find_browser_json_path()
        json_lines = json_path.read_text()
        for line in json_lines.splitlines():
            data.append(json.loads(line))
    except Exception as exc:
        raise FakeUserAgentError("Failed to load or parse browsers.json") from exc

    if not data:
        raise FakeUserAgentError("Data list is empty", data)

    if not isinstance(data, list):
        raise FakeUserAgentError("Data is not a list", data)
    return data
