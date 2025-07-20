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
        self.failed_reg_ids = []
        self.failure_reasons = []

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
            print(f"[FAILED] Both PDFs for Reg ID {reg_no} - {e}")
            self.failed_reg_ids.append(reg_no)
            self.failure_reasons.append(str(e))

    def _download_file(self, reg_no: str, file_type: str, filename: Path):
        """
        Downloads a single PDF file. No retries.
        """
        if file_type == "registration":
            url = f"https://foscos.fssai.gov.in/gateway/downloadpdf2/registration/{reg_no}"
        elif file_type == "application":
            url = f"https://foscos.fssai.gov.in/gateway/downloadpdf2/forma/{reg_no}"
        else:
            raise ValueError("Unknown file_type: must be 'registration' or 'application'")

        response = self.session.get(url)
        if response.status_code == 200 and response.content:
            filename.parent.mkdir(parents=True, exist_ok=True)
            with open(filename, "wb") as f:
                f.write(response.content)
        else:
            raise Exception(f"Status: {response.status_code}, URL: {url}")

    def download_all(self):
        """
        Multithreaded download of all registration numbers.
        """
        stop_event = threading.Event()

        def signal_handler(sig, frame):
            print("\n[!] Interrupt received. Shutting down gracefully...")
            stop_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = []

            for i, reg_no in enumerate(self.reg_no_list, start=1):
                if stop_event.is_set():
                    print("[!] Stopping before submitting more tasks.")
                    break
                futures.append(executor.submit(self._download_for_single_reg, reg_no))
                if i % 50 == 0:
                    print(f"[INFO] Submitted {i} download tasks...")

            try:
                for future in as_completed(futures):  # No timeout
                    if stop_event.is_set():
                        print("[!] Cancelling remaining futures.")
                        break
                    future.result()
            except KeyboardInterrupt:
                print("\n[!] Caught KeyboardInterrupt. Exiting...")
                stop_event.set()
                for f in futures:
                    f.cancel()
                executor.shutdown(wait=False, cancel_futures=True)
                raise

        if self.failed_reg_ids:
            print(f"\n[SUMMARY] Total Failed Registration IDs: {len(self.failed_reg_ids)}")
            for reg_id in self.failed_reg_ids:
                print(f" - {reg_id}")

            unique_errors = set(self.failure_reasons)
            print(f"\n[SUMMARY] Unique Error Reasons ({len(unique_errors)}): ")
            for reason in unique_errors:
                print(f"- {reason}")
