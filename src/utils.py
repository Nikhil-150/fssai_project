import pandas as pd
from config.settings import LOG_DIR
from pathlib import Path
import logging
import shutil
from config.settings import PDF_DIR
import os
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter


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
        registration_numbers = registration_numbers[:4]
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


def format_excel(filepath: str):
    wb = load_workbook(filepath)
    ws = wb.active

    # Format header
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
    alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for col_num, col in enumerate(ws.iter_cols(min_row=1, max_row=1), 1):
        cell = col[0]
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = alignment

    # Auto-adjust column widths
    for col_num, col in enumerate(ws.columns, 1):
        max_length = 0
        col_letter = get_column_letter(col_num)
        for cell in col:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except:
                pass
        ws.column_dimensions[col_letter].width = max_length + 2  # Padding for better fit

    wb.save(filepath)


if __name__ == "__main__":
    clear_pdfs_folder()