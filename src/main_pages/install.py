from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QMessageBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from typing import List
from utils import get_download_url
from utils.theme import is_dark_mode, progress_qss
import os
import re
import asyncio
import tempfile
import zipfile
import tarfile
import requests
import shutil
import subprocess
import math
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed


class DownloadWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url, save_path, nmp=False, proxy=""):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.nmp = bool(nmp)
        self.proxy = proxy
        self._stop_event = threading.Event()
        self._executor = None

    def stop(self):
        self._stop_event.set()
        self.requestInterruption()
        if self._executor is not None:
            self._executor.shutdown(wait=False, cancel_futures=True)

    def _make_proxies(self):
        if not self.proxy:
            return None
        return {"http": self.proxy, "https": self.proxy}

    def _download_single(self, headers, proxies):
        if self._stop_event.is_set() or self.isInterruptionRequested():
            raise RuntimeError("Download cancelled")
        response = requests.get(self.url, stream=True, headers=headers, timeout=30, proxies=proxies)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        with open(self.save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if self._stop_event.is_set() or self.isInterruptionRequested():
                    raise RuntimeError("Download cancelled")
                if chunk:
                    file.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = int(downloaded * 100 / total_size)
                        self.progress.emit(percent)

    def _supports_range(self, headers, proxies):
        head_resp = requests.head(self.url, headers=headers, timeout=30, allow_redirects=True, proxies=proxies)
        head_resp.raise_for_status()
        total_size = int(head_resp.headers.get("content-length", 0))
        accept_ranges = head_resp.headers.get("accept-ranges", "").lower()
        if total_size <= 0:
            return False, total_size
        if "bytes" in accept_ranges:
            return True, total_size
        range_resp = requests.get(
            self.url,
            headers={**headers, "Range": "bytes=0-0"},
            stream=True,
            timeout=30,
            proxies=proxies,
        )
        range_resp.raise_for_status()
        return range_resp.status_code == 206, total_size

    def _download_multi(self, headers, proxies, threads=8):
        supports_range, total_size = self._supports_range(headers, proxies)
        if not supports_range:
            self._download_single(headers, proxies)
            return

        threads = max(1, int(threads))
        part_size = int(math.ceil(total_size / threads))
        lock = threading.Lock()
        downloaded = 0

        with open(self.save_path, "wb") as f:
            f.truncate(total_size)

        def _download_part(start, end):
            nonlocal downloaded
            if self._stop_event.is_set() or self.isInterruptionRequested():
                raise RuntimeError("Download cancelled")
            part_headers = {**headers, "Range": f"bytes={start}-{end}"}
            resp = requests.get(self.url, stream=True, headers=part_headers, timeout=30, proxies=proxies)
            resp.raise_for_status()
            if resp.status_code != 206:
                raise ValueError("Server does not support partial content")
            offset = start
            with open(self.save_path, "r+b") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 64):
                    if self._stop_event.is_set() or self.isInterruptionRequested():
                        raise RuntimeError("Download cancelled")
                    if not chunk:
                        continue
                    f.seek(offset)
                    f.write(chunk)
                    offset += len(chunk)
                    with lock:
                        downloaded += len(chunk)
                        percent = int(downloaded * 100 / total_size)
                        self.progress.emit(percent)

        ranges = []
        for i in range(threads):
            start = i * part_size
            if start >= total_size:
                break
            end = min(total_size - 1, start + part_size - 1)
            ranges.append((start, end))

        self._executor = ThreadPoolExecutor(max_workers=threads)
        try:
            futures = [self._executor.submit(_download_part, start, end) for start, end in ranges]
            for future in as_completed(futures):
                future.result()
        finally:
            self._executor.shutdown(wait=False, cancel_futures=True)
            self._executor = None

    def run(self):
        try:
            self.status.emit("Downloading...")
            headers = {"User-Agent": "pan.baidu.com"}
            proxies = self._make_proxies()
            if not self.nmp:
                self._download_multi(headers=headers, proxies=proxies, threads=8)
            else:
                self._download_single(headers=headers, proxies=proxies)

            self.status.emit("Download complete")
            self.finished.emit(self.save_path)
        except requests.exceptions.Timeout:
            error_msg = "Download timed out"
            print(error_msg)
            self.error.emit(error_msg)
        except RuntimeError as e:
            error_msg = str(e)
            print(error_msg)
            self.error.emit(error_msg)
        except requests.exceptions.ConnectionError:
            error_msg = "Network connection failed"
            print(error_msg)
            self.error.emit(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Download failed: {str(e)}"
            print(error_msg)
            self.error.emit(error_msg)
        except OSError as e:
            error_msg = f"Failed to save file: {str(e)}"
            print(error_msg)
            self.error.emit(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(error_msg)
            self.error.emit(error_msg)


class UnpackWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, file_path, extract_to):
        super().__init__()
        self.file_path = file_path
        self.extract_to = extract_to

    def run(self):
        try:
            self.status.emit("Extracting...")
            os.makedirs(self.extract_to, exist_ok=True)

            if self.file_path.endswith(".zip"):
                with zipfile.ZipFile(self.file_path, 'r') as zip_ref:
                    total_files = len(zip_ref.namelist())
                    for i, member in enumerate(zip_ref.infolist()):
                        zip_ref.extract(member, self.extract_to)
                        percent = int((i + 1) * 100 / total_files)
                        self.progress.emit(percent)
            elif self.file_path.endswith((".tar.gz", ".tar.xz", ".tar.bz2")):
                with tarfile.open(self.file_path, 'r:*') as tar_ref:
                    total_files = len(tar_ref.getmembers())
                    for i, member in enumerate(tar_ref.getmembers()):
                        tar_ref.extract(member, self.extract_to)
                        percent = int((i + 1) * 100 / total_files)
                        self.progress.emit(percent)
            elif self.file_path.endswith(".7z"):
                # with py7zr.SevenZipFile(self.file_path, mode='r') as archive:
                #     all_files = archive.getnames()
                #     total_files = len(all_files)
                #     for i, member in enumerate(all_files):
                #         archive.extract(targets=[member], path=self.extract_to)
                #         percent = int((i + 1) * 100 / total_files)
                #         self.progress.emit(percent)
                # with libarchive.file_reader(self.file_path) as archive:
                #     total_files = sum(1 for _ in archive)
                # if total_files <= 0:
                #     total_files = 1
                # with libarchive.file_reader(self.file_path) as archive:
                #     for i, entry in enumerate(archive):
                #         member = getattr(entry, "pathname", "")
                #         if not member:
                #             percent = int((i + 1) * 100 / total_files)
                #             self.progress.emit(percent)
                #             continue
                #         relative_member = os.path.normpath(member.lstrip("/\\"))
                #         if relative_member.startswith(".."):
                #             raise ValueError(f"Unsafe archive member path: {member}")
                #         target_path = os.path.join(self.extract_to, relative_member)
                #         is_dir = member.endswith("/")
                #         entry_isdir = getattr(entry, "isdir", False)
                #         if callable(entry_isdir):
                #             is_dir = is_dir or bool(entry_isdir())
                #         else:
                #             is_dir = is_dir or bool(entry_isdir)
                #         if is_dir:
                #             os.makedirs(target_path, exist_ok=True)
                #         else:
                #             os.makedirs(os.path.dirname(target_path), exist_ok=True)
                #             try:
                #                 with open(target_path, "wb") as f:
                #                     for block in entry.get_blocks():
                #                         f.write(block)
                #             except IsADirectoryError:
                #                 os.makedirs(target_path, exist_ok=True)
                #         percent = int((i + 1) * 100 / total_files)
                #         self.progress.emit(percent)
                # archive = Py7zip()
                # archive.extract(self.file_path, self.extract_to)
                seven_zip_path = os.path.join(os.path.dirname(__file__), "..", "7z.exe")
                if not os.path.exists(seven_zip_path):
                    raise FileNotFoundError(f"7z executable not found: {seven_zip_path}")
                cmd = [seven_zip_path, "x", self.file_path, f"-o{self.extract_to}", "-y", "-bsp1"]
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    bufsize=1,
                )
                percent_pattern = re.compile(r"(\d+)%")
                if process.stdout is not None:
                    for line in process.stdout:
                        match = percent_pattern.search(line)
                        if match:
                            percent = max(0, min(100, int(match.group(1))))
                            self.progress.emit(percent)
                stderr_text = ""
                if process.stderr is not None:
                    stderr_text = process.stderr.read()
                return_code = process.wait()
                if return_code != 0:
                    raise subprocess.CalledProcessError(return_code, cmd, stderr=stderr_text)
                self.progress.emit(100)

            else:
                raise ValueError(f"Unsupported file type: {self.file_path}")

            self.status.emit("Extraction complete")
            self.finished.emit()
        except (zipfile.BadZipFile, tarfile.TarError) as e:
            error_msg = f"Invalid archive: {str(e)}"
            print(error_msg)
            self.error.emit(error_msg)
        except OSError as e:
            error_msg = f"Failed to extract files: {str(e)}"
            print(error_msg)
            self.error.emit(error_msg)
        except Exception as e:
            error_msg = f"Extraction failed: {str(e)}"
            print(error_msg)
            self.error.emit(error_msg)


class InstallPage(QWidget):
    installation_completed = pyqtSignal(int)

    def __init__(self, *data: list):
        super().__init__()
        self.data = data[0] if data else {}
        self.packages = data[1] if len(data) > 1 else {}
        self.install_to = data[2] if len(data) > 2 else os.path.join("C:\\", "AndroidToolBox")

        self.nmp = data[3] if len(data) > 3 else False
        self.proxy = data[4] if len(data) > 4 else ""

        self.installation_started = False
        self.current_package_index = 0
        self.download_worker = None
        self.unpack_worker = None
        self._aborting = False

        self.init_ui()

    def init_ui(self):
        try:
            dark_mode = is_dark_mode(self)
            layout = QVBoxLayout(self)
            layout.setContentsMargins(10, 0, 0, 0)
            layout.setAlignment(Qt.AlignmentFlag.AlignTop)

            title = self.data.get("install_page", {}).get("installing", "Installing...")
            title_label = QLabel(title, self)
            title_label.setStyleSheet("font-size: 12px;")
            layout.addWidget(title_label)

            content = self.data.get("install_page", {}).get("total", "Total")
            content_browser = QLabel(content, self)
            content_browser.setStyleSheet("font-size: 12px;")
            layout.addWidget(content_browser)

            self.progress_bar = QProgressBar(self)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.progress_bar.setTextVisible(False)
            self.progress_bar.setStyleSheet(progress_qss(dark_mode))
            layout.addWidget(self.progress_bar)

            self.details_content = self.data.get("install_page", {}).get("details", "Details: ")
            self.details_label = QLabel(self.details_content, self)
            self.details_label.setStyleSheet("font-size: 12px;")
            layout.addWidget(self.details_label)

            self.details_progress = QProgressBar(self)
            self.details_progress.setRange(0, 100)
            self.details_progress.setValue(0)
            self.details_progress.setTextVisible(False)
            self.details_progress.setStyleSheet(progress_qss(dark_mode))

            layout.addWidget(self.details_progress)
            self.setLayout(layout)
        except Exception as e:
            print(f"Error in init_ui: {e}")

    def start_installation(self):
        try:
            if self.installation_started:
                return 0

            self.installation_started = True

            if os.path.exists(self.install_to):
                try:
                    if os.listdir(self.install_to):
                        reply = QMessageBox.question(
                            self, self.data.get("install_page", {}).get("confirm_installation", "Confirm Installation"),
                            self.data.get("install_page", {}).get("confirm_installation_message", f"The installation directory {self.install_to} is not empty. Continue?\nThis may overwrite existing files."),
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.No
                        )
                        if reply == QMessageBox.StandardButton.No:
                            return 2
                except OSError:
                    pass
                return 0
            else:
                try:
                    os.makedirs(self.install_to, exist_ok=True)
                    return 0
                except OSError as e:
                    print(f"Failed to create installation directory: {e}")
                    return 1
        except Exception as e:
            print(f"Error in start_installation: {e}")
            return 1

    def install_packages(self):
        try:
            if not self.packages:
                self.update_status("No components selected for installation")
                return

            self.current_package_index = 0
            self.install_next_package()
        except Exception as e:
            print(f"Error in install_packages: {e}")
            self.abort_installation(f"Error: {str(e)}")

    def install_next_package(self):
        try:
            if self.current_package_index >= len(self.packages):
                self.update_status("All components installed successfully!")
                self.update_progress(100)
                self.installation_completed.emit(0)
                return

            package_info = self.packages[self.current_package_index]
            if not package_info:
                self.current_package_index += 1
                self.install_next_package()
                return

            package_id = package_info.get('id', 'unknown')
            version = package_info.get('version', 'latest')
            unpack = package_info.get('unpack', True)

            self.update_status(f"Preparing to install {package_id} (version: {version})...")

            self.install_package(package_id, version, unpack=unpack)
        except Exception as e:
            print(f"Error in install_next_package: {e}")
            self.abort_installation(f"Error: {str(e)}")

    def stop_all_workers(self):
        if self.download_worker is not None:
            try:
                self.download_worker.stop()
            except Exception:
                pass
            if self.download_worker.isRunning():
                self.download_worker.wait(1500)
                if self.download_worker.isRunning():
                    self.download_worker.terminate()
                    self.download_worker.wait(500)
            self.download_worker = None

        if self.unpack_worker is not None:
            if self.unpack_worker.isRunning():
                self.unpack_worker.requestInterruption()
                self.unpack_worker.wait(1000)
                if self.unpack_worker.isRunning():
                    self.unpack_worker.terminate()
                    self.unpack_worker.wait(500)
            self.unpack_worker = None

    def abort_installation(self, message: str, status_code: int = 2):
        if self._aborting:
            return
        self._aborting = True
        self.update_status(message)
        self.stop_all_workers()
        self.installation_completed.emit(status_code)

    def install_package(self, package_id, version, unpack: bool = True):
        try:
            url = asyncio.run(get_download_url(open(os.path.join(os.path.dirname(__file__), "..", "api_server.txt")).read().rstrip() or "https://atb.xgj.qzz.io/", package_id, version))
            if not url:
                raise ValueError("Empty download URL")

            filename = url.split("/")[-1]
            if not filename:
                filename = f"{package_id}_{version}.zip"

            save_path = os.path.join(tempfile.gettempdir(), filename)

            self.download_worker = DownloadWorker(url, save_path, nmp=self.nmp, proxy=self.proxy)
            self.download_worker.progress.connect(self.update_details_progress)
            self.download_worker.status.connect(self.update_status)
            self.download_worker.finished.connect(self.on_download_finished)
            self.download_worker.error.connect(self.on_download_error)
            self.download_worker.start()
        except asyncio.CancelledError:
            self.update_status("Download cancelled")
        except Exception as e:
            error_msg = f"Failed to get download URL: {str(e)}"
            print(error_msg)
            self.update_status(error_msg)

    @staticmethod
    def _is_true(value) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)

    def on_download_finished(self, file_path):
        try:
            self.update_status("Download complete, extracting...")

            package_info = self.packages[self.current_package_index]
            install_to_subdir = package_info.get('installto', '/')
            target_dir = os.path.join(self.install_to, install_to_subdir.lstrip('/'))

            if self._is_true(package_info.get('unpack', True)):
                self.unpack_worker = UnpackWorker(file_path, target_dir)
                self.unpack_worker.progress.connect(self.update_details_progress)
                self.unpack_worker.status.connect(self.update_status)
                self.unpack_worker.finished.connect(self.on_unpack_finished)
                self.unpack_worker.error.connect(self.on_unpack_error)
                self.unpack_worker.start()
            else:
                try:
                    target_file = os.path.join(target_dir, os.path.basename(file_path))
                    os.makedirs(target_dir, exist_ok=True)
                    shutil.copy2(file_path, target_file)
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass
                    self.on_unpack_finished()
                except Exception as e:
                    self.on_unpack_error(f"Failed to copy file: {str(e)}")
        except Exception as e:
            print(f"Error in on_download_finished: {e}")
            self.abort_installation(f"Error: {str(e)}")

    def on_download_error(self, error_msg):
        if self._aborting:
            return
        self.abort_installation(f"Failed to download package: {error_msg}")
        QMessageBox.warning(self, "Download Failed", f"Failed to download package: {error_msg}")

    def on_unpack_finished(self):
        try:
            package_info = self.packages[self.current_package_index]
            version = package_info.get('version', 'latest')
            package_id = package_info.get('id', 'unknown')

            self.update_status(f"{package_id} (version: {version}) installed successfully")

            total_packages = len(self.packages)
            completed_percentage = int(((self.current_package_index + 1) / total_packages) * 100)
            self.update_progress(completed_percentage)

            self.current_package_index += 1
            QTimer.singleShot(500, self.install_next_package)
        except Exception as e:
            print(f"Error in on_unpack_finished: {e}")
            self.abort_installation(f"Error in unpack finish: {str(e)}")

    def on_unpack_error(self, error_msg):
        if self._aborting:
            return
        self.abort_installation(f"Failed to extract package: {error_msg}")
        QMessageBox.warning(self, "Extraction Failed", f"Failed to extract package: {error_msg}")

    def update_progress(self, value):
        try:
            self.progress_bar.setValue(value)
        except Exception:
            pass

    def update_details_progress(self, value):
        try:
            self.details_progress.setValue(value)
        except Exception:
            pass

    def update_status(self, message):
        try:
            self.details_label.setText(f"Details: {message}")
        except Exception:
            pass
