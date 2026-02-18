from gui import App
from qasync import QEventLoop
import json
import os
import sys
import locale
import asyncio

data = {
    "$global": {},
    "main_window": {}
}


def main():
    # os.add_dll_directory(os.path.dirname(os.path.abspath(__file__)))
    # os.add_dll_directory(os.path.dirname(os.path.abspath(sys.executable)))
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
    sys.exit(main())
