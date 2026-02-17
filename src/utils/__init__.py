from .BuildConfig import BuildConfig
from typing import Optional, Union
import requests
import gzip
import json
import asyncio
import base64
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def _get_download_url_sync(
    api_url: str,
    package_id: str,
    package_version: Optional[Union[int, str]] = None
) -> str:
    if isinstance(package_version, str):
        version_text = package_version.strip()
        if version_text.isdigit():
            package_version = version_text
        elif "." in version_text:
            package_version = version_string_to_int(version_text)
        else:
            package_version = version_text
    elif package_version is None:
        package_version = "latest"

    data = {
        "package_id": package_id,
        "package_version": str(package_version)
    }

    gzip_data = gzip.compress(json.dumps(data).encode("utf-8"))
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": f"AndroidToolBox Installer {BuildConfig.PKGUTILS_VERSION_STR}",
        "Accept-Encoding": "gzip",
        "Content-Encoding": "gzip",
        "Connection": "close",
    }
    gzip_headers = {
        "Base-Request-Header": base64.b64encode(gzip.compress(json.dumps(headers).encode("utf-8"))).decode("utf-8"),
        "Base-Request-Param": 'encrypted=0;gzip=all;encoding=65001'
    }
    merged_headers = {**headers, **gzip_headers}

    session = requests.Session()
    retry = Retry(
        total=2,
        connect=2,
        read=2,
        status=1,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    api_url = api_url.rstrip("/")

    try:
        response = session.post(
            f"{api_url}/v1/get_download_url",
            data=gzip_data,
            headers=merged_headers,
            timeout=15
        )
        response.raise_for_status()
        if response.status_code == 200:
            return response.text.strip().strip('"')
    except requests.exceptions.RequestException as e:
        print(f"v1 get download URL failed, falling back to v0: {e}")
    except Exception as e:
        print(f"Unexpected error in v1: {e}")

    try:
        result = session.get(
            f"{api_url}/v0/get_download_url/{package_id}/{package_version}",
            headers={"User-Agent": f"AndroidToolBox Installer {BuildConfig.PKGUTILS_VERSION_STR}", "Connection": "close"},
            timeout=15
        )
        result.raise_for_status()
        return result.text.strip().strip('"')
    except requests.exceptions.RequestException as e:
        print(f"v0 get download URL failed: {e}")
    except Exception as e:
        print(f"Unexpected error in v0: {e}")

    raise RuntimeError(f"Failed to get download URL for {package_id}")


async def get_download_url(
    api_url: str,
    package_id: str,
    package_version: Optional[Union[int, str]] = None
) -> str:
    return await asyncio.to_thread(
        _get_download_url_sync,
        api_url,
        package_id,
        package_version
    )


def _get_packages_sync(api_url: str) -> str | None:
    headers = {
        "User-Agent": f"AndroidToolBox Installer {BuildConfig.PKGUTILS_VERSION_STR}"
    }
    try:
        response = requests.get(f"{api_url}/v1/packages", headers=headers, timeout=15)
        response.raise_for_status()
        if response.status_code == 200:
            return response.text.strip()
    except requests.exceptions.RequestException as e:
        print(f"v1 packages request failed: {e}")
    except Exception as e:
        print(f"Unexpected error in v1 packages: {e}")

    try:
        result = requests.get(f"{api_url}/v0/packages", headers=headers, timeout=15)
        result.raise_for_status()
        return result.text.strip()
    except requests.exceptions.RequestException as e:
        print(f"v0 packages request failed: {e}")
    except Exception as e:
        print(f"Unexpected error in v0 packages: {e}")

    return None


async def get_packages(api_url: str) -> str:
    result = await asyncio.to_thread(_get_packages_sync, api_url)
    if result is None:
        try:
            with open("packages.xml", "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    raise ValueError("packages.xml is empty")
                return content
        except FileNotFoundError:
            raise Exception("Failed to fetch package info from API and local packages.xml not found")
        except Exception as e:
            raise Exception(f"Failed to read local packages.xml: {e}")
    return result


def version_string_to_int(version: str) -> int:
    try:
        parts = version.split(".")
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        return major * 10000 + minor * 100 + patch
    except (ValueError, AttributeError):
        return 0
