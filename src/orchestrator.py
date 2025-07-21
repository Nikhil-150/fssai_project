from config.settings import INPUT_EXCEL_PATH, PDF_DIR
from src.downloader import PDFDownloader
from src.utils import read_registration_numbers
from src.extractor import PDFExtractor
from src.utils import format_excel
from queue import Queue
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import pandas as pd
from pathlib import Path


def extract_worker(task):
    reg_id, app_path, reg_path = task
    extractor = PDFExtractor(reg_id, app_path, reg_path)
    return extractor.extract()


class FSSAIOrchestrator:
    def __init__(self):
        self.registration_numbers = []
        self.download_queue = Queue()
        self.extracted_rows = []

    def load_registration_numbers(self):
        """Reads the registration numbers from the Excel file."""
        self.registration_numbers = read_registration_numbers(INPUT_EXCEL_PATH)
        print(f"[INFO] Found {len(self.registration_numbers)} registration numbers.")

    def download_pdfs(self):
        """Passes registration numbers to downloader."""
        if not self.registration_numbers:
            raise ValueError("Registration numbers not loaded.")

        downloader = PDFDownloader(self.registration_numbers)
        downloader.output_queue = self.download_queue  # Inject the queue
        downloader.download_all()

    def run_extraction(self):
        """Extracts data from downloaded PDFs using multiprocessing."""
        print("[INFO] Starting extraction...")

        tasks = []
        while not self.download_queue.empty():
            reg_id, app_path, reg_path = self.download_queue.get()
            tasks.append((reg_id, app_path, reg_path))

        with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
            futures = [executor.submit(extract_worker, task) for task in tasks]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    self.extracted_rows.append(result)

        print(f"[INFO] Extracted data for {len(self.extracted_rows)} entries.")

    def save_to_excel(self):
        print(f"[INFO] Saving results to Excel...")
        df = pd.DataFrame(self.extracted_rows)

        output_path = Path("data/Output Excels/extracted_data.xlsx")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(output_path, index=False)

        format_excel(str(output_path))  # 📦 Apply formatting
        print(f"[SUCCESS] Excel saved to {output_path}")

    def run(self):
        """Main method to coordinate the download and extraction process."""
        self.load_registration_numbers()
        self.download_pdfs()
        self.run_extraction()
        self.save_to_excel()


