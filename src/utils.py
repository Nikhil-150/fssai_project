import pandas as pd
from config.settings import LOG_DIR
from pathlib import Path
import logging
import shutil
from config.settings import PDF_DIR
import os

# Optional: basic logger setup
LOG_FILE = LOG_DIR / "download.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)


def read_registration_numbers(file_path: Path) -> list[str]:
    """
    Reads an Excel file containing a column of registration numbers.
    Returns a list of cleaned registration numbers as strings.
    """
    try:
        df = pd.read_excel(file_path)
        reg_col = df.columns[0]  # assumes registration numbers are in the first column
        registration_numbers = df[reg_col].dropna().astype(str).str.strip().tolist()
        registration_numbers = registration_numbers[:1000]
        return registration_numbers
    except Exception as e:
        logging.error(f"Failed to read registration numbers from {file_path}: {e}")
        return []


def log_success(reg_no: str, file_type: str):
    logging.info(f"Downloaded {file_type} for Registration No: {reg_no}")


def log_failure(reg_no: str, file_type: str, error_msg: str):
    logging.error(f"❌ Failed {file_type} for {reg_no} — {error_msg}")


def handle_remove_readonly(func, path, exc_info):
    """
    Error handler for removing read-only or in-use files on Windows.
    """
    try:
        os.chmod(path, 0o777)
        func(path)
    except Exception as e:
        print(f"[ERROR] Could not delete {path}: {e}")


def clear_pdfs_folder():
    if PDF_DIR.exists():
        shutil.rmtree(PDF_DIR, onerror=handle_remove_readonly)
        print("[INFO] PDF folder cleared.")


if __name__ == "__main__":
    clear_pdfs_folder()