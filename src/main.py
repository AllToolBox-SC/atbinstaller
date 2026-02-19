from gui import App
from qasync import QEventLoop
import json
import os
import sys
import locale
import asyncio
import argparse
import urllib.request


data = {
    "$global": {},
    "main_window": {}
}


def main(*adata: list):
    # os.add_dll_directory(os.path.dirname(os.path.abspath(__file__)))
    # os.add_dll_directory(os.path.dirname(os.path.abspath(sys.executable)))
    nmp: bool = adata[0] if len(adata) > 0 else False 
    proxy: str = adata[1] if len(adata) > 1 else ""
    # Load global data
    with open(os.path.join(os.path.dirname(__file__), "locals/global.json"), "r", encoding="utf-8") as f:
        data["$global"] = json.load(f)

    system_locale = locale.getdefaultlocale()[0]
    print(f"System locale detected: {system_locale}")
    if system_locale is None:
        system_locale = "en_US"
    local_file = os.path.join(os.path.dirname(__file__), f"locals/{system_locale}.json")
    print(f"Looking for local file: {local_file}")
    if os.path.exists(local_file):
        with open(local_file, "r", encoding="utf-8") as f:
            data["main_window"] = json.load(f).get("main_window", {})
    else:
        print(f"Locale {system_locale} not found, using default (en_US).")
        with open(os.path.join(os.path.dirname(__file__), "locals/en_US.json"), "r", encoding="utf-8") as f:
            data["main_window"] = json.load(f).get("main_window", {})

    app = App(data)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Start the event loop and run the coroutine
    loop.run_until_complete(app.load_package_data())

    with loop:
        return app.exec()


if __name__ == "__main__":
    no_multi_threads: bool = False
    proxies = urllib.request.getproxies()
    enable_proxy: str | bool = proxies.get("https", False) or proxies.get("http", False)
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-multi-threads", help="Disable Multi Threads Download", action="store_true", default=False, required=False)
    parser.add_argument("--use-proxy", help="Use HTTP(s) Proxy", type=str, required=False, default="")
    parser = parser.parse_args()
    if parser.no_multi_threads: no_multi_threads = True
    proxy_domain: str
    if parser.use_proxy.rstrip() is "": proxy_domain = enable_proxy if enable_proxy else ""
    else: proxy_domain = parser.use_proxy.rstrip()
    sys.exit(main(no_multi_threads, proxy_domain))
