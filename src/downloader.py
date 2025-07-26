import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from config.settings import HEADERS, PDF_DIR, COOKIES, MAX_WORKERS, REGISTRATION_FORMS_DIR, APPLICATION_FORMS_DIR, LICENCE_FORMS_DIR
from pathlib import Path
import signal
import threading
from queue import Queue


class PDFDownloader:
    def __init__(self, input_ids: list[str], user_choice_segment: str, max_threads=MAX_WORKERS):
        self.input_ids = input_ids
        self.user_choice_segment = user_choice_segment
        self.max_threads = max_threads
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.session.cookies.update(COOKIES)
        self.failed_reg_ids = []
        self.failure_reasons = []
        self.output_queue = None

    def _download_for_single_reg(self, input_id: str):
        """
        Downloads both Registration Certificate and Application Form.
        """
        try:
            reg_path = REGISTRATION_FORMS_DIR / f"registration_{input_id}.pdf"
            app_path = APPLICATION_FORMS_DIR / f"application_form_{input_id}.pdf"
            licence_path = LICENCE_FORMS_DIR / f"Licence_form_{input_id}.pdf"

            if self.user_choice_segment == '1':
                self._download_file(input_id, file_type="registration", filename=reg_path)
                self._download_file(input_id, file_type="application", filename=app_path)
            elif self.user_choice_segment == '2':
                self._download_file(input_id, file_type="licence", filename=licence_path)
            else:
                print(f"Invalid Choice !")

            # Push to queue if both succeed
            # Push to queue with appropriate files based on segment
            if self.output_queue:
                if self.user_choice_segment == '1':
                    self.output_queue.put((input_id, app_path, reg_path))
                elif self.user_choice_segment == '2':
                    self.output_queue.put((input_id, licence_path))

        except Exception as e:
            print(f"[FAILED] Both PDFs for Reg ID {input_id} - {e}")
            self.failed_reg_ids.append(input_id)
            self.failure_reasons.append(str(e))

    def _download_file(self, input_id: str, file_type: str, filename: Path):
        """
        Downloads a single PDF file. No retries.
        """
        if file_type == "registration":
            url = f"https://foscos.fssai.gov.in/gateway/downloadpdf2/registration/{input_id}"
        elif file_type == "application":
            url = f"https://foscos.fssai.gov.in/gateway/downloadpdf2/forma/{input_id}"
        elif file_type == "licence":
            url = f"https://foscos.fssai.gov.in/gateway/downloadpdf2/license/{input_id}/2"
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

            for i, reg_no in enumerate(self.input_ids, start=1):
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
