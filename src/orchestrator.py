from config.settings import INPUT_EXCEL_PATH
from src.downloader import AsyncPDFDownloader
from src.utils import read_registration_numbers
import asyncio

class FSSAIOrchestrator:
    def __init__(self):
        self.registration_numbers = []

    def load_registration_numbers(self):
        """Reads the registration numbers from the Excel file."""
        self.registration_numbers = read_registration_numbers(INPUT_EXCEL_PATH)
        print(f"[INFO] Found {len(self.registration_numbers)} registration numbers.")

    def download_pdfs(self):
        """Passes registration numbers to downloader."""
        if not self.registration_numbers:
            raise ValueError("Registration numbers not loaded.")

        downloader = AsyncPDFDownloader(self.registration_numbers)
        asyncio.run(downloader.download_all())

    def run(self):
        """Main method to coordinate the download process."""
        self.load_registration_numbers()
        self.download_pdfs()
