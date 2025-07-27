from config.settings import INPUT_EXCEL_PATH_SEGMENT_1, INPUT_EXCEL_PATH_SEGMENT_2, OUTPUT_EXCEL_PATH_SEGMENT_1, OUTPUT_EXCEL_PATH_SEGMENT_2
from src.downloader import PDFDownloader
from src.utils import read_registration_numbers
from src.extractor_segment1 import PDFExtractorSegment1
from src.extractor_segment2 import PDFExtractorSegment2
from src.utils import format_excel
from queue import Queue
from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor
import multiprocessing
import pandas as pd
from pathlib import Path


def extract_worker_segment_1(task):
    reg_id, app_path, reg_path = task
    extractor = PDFExtractorSegment1(reg_id, app_path, reg_path)
    return extractor.extract()


def extract_worker_segment_2(task):
    input_id, licence_path = task
    try:
        extractor = PDFExtractorSegment2(input_id, licence_path)
        result = extractor.extract()
        if result:
            print(f"[DEBUG] Extracted for {input_id}")
        return result
    except Exception as e:
        print(f"[ERROR] Failed extraction for {input_id}: {e}")
        return None


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

        downloader = PDFDownloader(self.input_ids, self.segment)
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
        df = pd.DataFrame(self.extracted_rows)

        output_path = None
        if self.segment == "1":
            output_path = Path(OUTPUT_EXCEL_PATH_SEGMENT_1)
        elif self.segment == "2":
            output_path = Path(OUTPUT_EXCEL_PATH_SEGMENT_2)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(output_path, index=False)

        format_excel(str(output_path))  # 📦 Apply formatting
        print(f"[SUCCESS] Excel saved to {output_path}")

    def run(self):
        """Main method to coordinate the download and extraction process."""
        self.load_registration_numbers(self.segment)
        self.download_pdfs()
        if self.segment == '1':
            self.run_extraction_segment_1()
        elif self.segment == '2':
            self.run_extraction_segment_2()
        else:
            print(f"Invalid choice!")
        self.save_to_excel()


