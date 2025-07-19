import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from config.settings import HEADERS, PDF_DIR, COOKIES, MAX_WORKERS
from src.utils import log_success, log_failure
from pathlib import Path
import signal
import threading


class PDFDownloader:
    def __init__(self, reg_no_list: list[str], max_threads=MAX_WORKERS):
        self.reg_no_list = reg_no_list
        self.max_threads = max_threads
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.session.cookies.update(COOKIES)

    def _download_for_single_reg(self, reg_no: str):
        """
        Downloads both Registration Certificate and Application Form.
        """
        try:
            self._download_file(
                reg_no,
                file_type="registration",
                filename=PDF_DIR / f"registration_{reg_no}.pdf"
            )
            self._download_file(
                reg_no,
                file_type="application",
                filename=PDF_DIR / f"application_form_{reg_no}.pdf"
            )
        except Exception as e:
            log_failure(reg_no, "both", str(e))

    def _download_file(self, reg_no: str, file_type: str, filename: Path):
        """
        Downloads a single PDF file based on type and saves to disk.
        """
        if file_type == "registration":
            url = f"https://foscos.fssai.gov.in/gateway/downloadpdf2/registration/{reg_no}"
        elif file_type == "application":
            url = f"https://foscos.fssai.gov.in/gateway/fbo_readonly/getlogintofortacereg/{reg_no}"
        else:
            raise ValueError("Unknown file_type: must be 'registration' or 'application'")

        headers = {
            **self.session.headers
        }

        response = self.session.get(url)
        if response.status_code == 200 and response.content:
            filename.parent.mkdir(parents=True, exist_ok=True)
            with open(filename, "wb") as f:
                f.write(response.content)
            log_success(reg_no, file_type)
        else:
            raise Exception(f"Status: {response.status_code}, URL: {url}")

    def download_all(self):
        """
        Starts multithreaded downloads using stored registration numbers.
        Handles graceful shutdown on KeyboardInterrupt (Ctrl+C).
        """
        stop_event = threading.Event()

        def signal_handler(sig, frame):
            print("\n[!] Interrupt received. Shutting down gracefully...")
            stop_event.set()

        # Register signal handler for graceful shutdown
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = []

            for reg_no in self.reg_no_list:
                if stop_event.is_set():
                    print("[!] Stopping before submitting more tasks.")
                    break
                futures.append(executor.submit(self._download_for_single_reg, reg_no))

            try:
                for future in as_completed(futures):
                    if stop_event.is_set():
                        print("[!] Cancelling remaining futures.")
                        break
                    future.result()
            except KeyboardInterrupt:
                print("\n[!] Caught KeyboardInterrupt. Exiting...")
                stop_event.set()
                # Cancel running futures (optional if downloads are short-lived)
                for f in futures:
                    f.cancel()
                executor.shutdown(wait=False, cancel_futures=True)
                raise
