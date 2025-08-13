from config.settings import INPUT_EXCEL_PATH_SEGMENT_1, INPUT_EXCEL_PATH_SEGMENT_2, OUTPUT_EXCEL_PATH_SEGMENT_1, \
    OUTPUT_EXCEL_PATH_SEGMENT_2
from src.downloader import PDFDownloader
from src.utils import read_registration_numbers
from src.extractor_segment1 import PDFExtractorSegment1
from src.extractor_segment2 import PDFExtractorSegment2
from src.utils import format_excel
from multiprocessing import Queue
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import pandas as pd
from pathlib import Path
from multiprocessing import Manager, Process
from datetime import datetime
import threading
import time


def extract_worker_segment_1(task):
    reg_id, app_path, reg_path = task
    extractor = PDFExtractorSegment1(reg_id, app_path, reg_path)
    result = extractor.extract()
    if result:
        print(f"[EXTRACT] ✅ Data extracted for ID: {reg_id} at {datetime.now().strftime('%H:%M:%S')}")
    return result


def extract_worker_segment_2(task):
    input_id, licence_path = task
    try:
        extractor = PDFExtractorSegment2(input_id, licence_path)
        result = extractor.extract()
        if result:
            print(f"[EXTRACT] ✅ Data extracted for ID: {input_id} at {datetime.now().strftime('%H:%M:%S')}")
        return result
    except Exception as e:
        print(f"[ERROR] Failed extraction for {input_id}: {e}")
        return None


def extractor_worker_process_segment_1(queue, result_list):
    while True:
        task = queue.get()
        if task is None:
            break
        reg_id, app_path, reg_path = task
        try:
            result = extract_worker_segment_1((reg_id, app_path, reg_path))
            if result:
                result_list.append(result)
        except Exception as e:
            print(f"[ERROR] Failed extraction for {reg_id}: {e}")


def extractor_worker_process_segment_2(queue, result_list):
    while True:
        task = queue.get()
        if task is None:
            break
        input_id, licence_path = task
        try:
            result = extract_worker_segment_2((input_id, licence_path))
            if result:
                result_list.append(result)
        except Exception as e:
            print(f"[ERROR] Failed extraction for {input_id}: {e}")


class FSSAIOrchestrator:
    def __init__(self, segment: str = "1"):
        """
        :param segment: '1' for Registration + Application (Segment 1),
                        '2' for Licence Certificate only (Segment 2)
        """
        self.segment = segment
        self.input_ids = []
        self.download_queue = Queue()
        self.extracted_rows = []

        self.manager = Manager()
        self.extracted_rows = self.manager.list()
        self.autosave_stop_event = threading.Event()
        self.failed_ids = []
        self.extraction_done = False

    def load_registration_numbers(self, user_choice_for_segment):
        """Reads the registration / licence ref id numbers from the Excel file."""
        if user_choice_for_segment == "1":
            self.input_ids = read_registration_numbers(INPUT_EXCEL_PATH_SEGMENT_1)
            print(f"[INFO] Found {len(self.input_ids)} REF ids for Segment 1(Registration + Application).")
        if user_choice_for_segment == "2":
            self.input_ids = read_registration_numbers(INPUT_EXCEL_PATH_SEGMENT_2)
            print(f"[INFO] Found {len(self.input_ids)} REF ids for Segment 2(Licence Certificate).")

    def download_pdfs(self):
        """Passes REF ids numbers (for downloading Reg + App or Licence) to downloader."""
        if not self.input_ids:
            raise ValueError("Registration numbers not loaded.")

        downloader = PDFDownloader(self.input_ids, self.segment, output_queue=self.download_queue)
        downloader.output_queue = self.download_queue  # Inject the queue
        downloader.download_all()

    def run_extraction_segment_1(self):
        """Extracts data from downloaded PDFs using multiprocessing."""
        print("[INFO] Starting extraction...")

        tasks = []
        while not self.download_queue.empty():
            reg_id, app_path, reg_path = self.download_queue.get()
            tasks.append((reg_id, app_path, reg_path))

        with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
            futures = [executor.submit(extract_worker_segment_1, task) for task in tasks]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    self.extracted_rows.append(result)

        print(f"[INFO] Extracted data for {len(self.extracted_rows)} entries.")

    def run_extraction_segment_2(self):
        """Extracts data from downloaded PDFs using multiprocessing."""
        print("[INFO] Starting extraction...")

        tasks = []
        while not self.download_queue.empty():
            input_id, licence_path = self.download_queue.get()
            tasks.append((input_id, licence_path))
        print(f"[DEBUG] Total tasks loaded for extraction: {len(tasks)}")

        with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
            futures = [executor.submit(extract_worker_segment_2, task) for task in tasks]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    self.extracted_rows.append(result)

        print(f"[INFO] Extracted data for {len(self.extracted_rows)} entries.")

    def save_to_excel(self):
        print(f"[INFO] Saving results to Excel...")
        df = pd.DataFrame(list(self.extracted_rows))

        output_path = None
        if self.segment == "1":
            output_path = Path(OUTPUT_EXCEL_PATH_SEGMENT_1)
        elif self.segment == "2":
            output_path = Path(OUTPUT_EXCEL_PATH_SEGMENT_2)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(output_path, index=False)

        format_excel(str(output_path))  # 📦 Apply formatting
        print(f"[SUCCESS] Excel saved to {output_path}")

    def extractor_worker_segment_1(self):
        while True:
            task = self.download_queue.get()
            if task is None:
                break
            reg_id, app_path, reg_path = task
            try:
                result = extract_worker_segment_1((reg_id, app_path, reg_path))
                if result:
                    self.extracted_rows.append(result)
            except Exception as e:
                print(f"[ERROR] Extraction failed for {reg_id}: {e}")

    def extractor_worker_segment_2(self):
        while True:
            task = self.download_queue.get()
            if task is None:
                break
            input_id, licence_path = task
            try:
                result = extract_worker_segment_2((input_id, licence_path))
                if result:
                    self.extracted_rows.append(result)
            except Exception as e:
                print(f"[ERROR] Extraction failed for {input_id}: {e}")

    def run(self):
        self.load_registration_numbers(self.segment)

        # ✅ Create a lock for thread-safe autosave
        lock = threading.Lock()

        # ✅ Start autosave thread before processing
        autosave_thread = threading.Thread(target=self.autosave_worker, args=(lock,), daemon=True)
        autosave_thread.start()

        # ✅ Start extractor workers first
        workers = []
        for _ in range(multiprocessing.cpu_count()):
            if self.segment == '1':
                p = Process(target=extractor_worker_process_segment_1, args=(self.download_queue, self.extracted_rows))
            else:
                p = Process(target=extractor_worker_process_segment_2, args=(self.download_queue, self.extracted_rows))
            p.start()
            workers.append(p)

        # ✅ Start downloading (this will push items into the queue)
        self.download_pdfs()

        # ✅ STEP 3: Check which REF IDs were successfully downloaded
        from config.settings import REGISTRATION_FORMS_DIR, APPLICATION_FORMS_DIR, LICENCE_FORMS_DIR

        if self.segment == '1':
            reg_files = {f.stem.replace("registration_", "") for f in REGISTRATION_FORMS_DIR.glob("*.pdf")}
            app_files = {f.stem.replace("application_form_", "") for f in APPLICATION_FORMS_DIR.glob("*.pdf")}
            downloaded_ids = reg_files & app_files  # Must have both

        elif self.segment == '2':
            licence_files = {f.stem.replace("Licence_form_", "") for f in LICENCE_FORMS_DIR.glob("*.pdf")}
            downloaded_ids = licence_files

        else:
            print("[ERROR] Invalid segment. Exiting...")
            return

        original_ids = set(self.input_ids)
        self.failed_ids = list(original_ids - downloaded_ids)

        if self.failed_ids:
            print(f"[WARNING] ❌ {len(self.failed_ids)} REF IDs failed to download completely.\n")
            for ref in self.failed_ids:
                print(f" - {ref}")
        else:
            print("[INFO] ✅ All REF IDs downloaded successfully.\n")

        # ✅ Signal workers to stop after queue is exhausted
        for _ in workers:
            self.download_queue.put(None)

        # ✅ Wait for all workers to finish
        for p in workers:
            p.join()

        self.extraction_done = True

        # ✅ Stop autosave thread after everything is done
        self.autosave_stop_event.set()
        autosave_thread.join()

        # ✅ Final save to Excel
        self.save_to_excel()

        # ✅ STEP 4: Save failed REF IDs to Excel
        if self.failed_ids:
            failed_df = pd.DataFrame({"Failed_REF_IDs": self.failed_ids})
            segment_name = f"Segment_{self.segment}"
            failed_excel_path = Path("data/Output Excels") / f"Failed_REF_IDs_for_{segment_name}.xlsx"
            failed_excel_path.parent.mkdir(parents=True, exist_ok=True)
            failed_df.to_excel(failed_excel_path, index=False)
            print(f"[FAILED REF IDs] ❌ Saved to: {failed_excel_path}")
        else:
            print("[FAILED REF IDs] ✅ No failed REF IDs. Skipping failure Excel.")

    def autosave_worker(self, lock):
        while not self.autosave_stop_event.is_set():
            time.sleep(300)  # 10 minutes

            with lock:
                if self.extracted_rows:
                    print(f"[AUTOSAVE] Saving partial results at {datetime.now().strftime('%H:%M:%S')}...")

                    df = pd.DataFrame(list(self.extracted_rows))

                    output_path = Path(OUTPUT_EXCEL_PATH_SEGMENT_1) if self.segment == "1" else Path(
                        OUTPUT_EXCEL_PATH_SEGMENT_2)

                    if self.segment == "1":
                        temp_path = output_path.parent / "Reg_Seg_1_Output_Temp.xlsx"
                    else:
                        temp_path = output_path.parent / "Lice_Seg_2_Output_Temp.xlsx"

                    output_path.parent.mkdir(parents=True, exist_ok=True)

                    try:
                        df.to_excel(temp_path, index=False, sheet_name="Autosave")
                        temp_path.replace(output_path)
                        print(f"[AUTOSAVE] ✅ Excel autosaved to {output_path}")
                    except Exception as e:
                        print(f"[AUTOSAVE ERROR] ❌ Failed to autosave: {e}")

            # ✅ Stop autosave thread if extraction is done
            if self.extraction_done:
                print("[AUTOSAVE] 🛑 Extraction complete. Stopping autosave thread.")
                break



