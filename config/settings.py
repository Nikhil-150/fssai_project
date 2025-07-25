from pathlib import Path


# === Bearer Token from Text File === #
TOKEN_FILE = Path(__file__).parent / "bearer_token.txt"

try:
    BEARER_TOKEN = TOKEN_FILE.read_text().strip()
except FileNotFoundError:
    BEARER_TOKEN = ""
    print("Warning: Bearer token file not found.")

# === Base Directories === #
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PDF_DIR = DATA_DIR / "pdfs"
LOG_DIR = BASE_DIR / "logs"

# === Input/Output Files === #
INPUT_EXCEL_PATH = DATA_DIR / "registration_numbers.xlsx"
OUTPUT_EXCEL_PATH = DATA_DIR / "extracted_data.xlsx"
LOG_FILE_PATH = LOG_DIR / "download.log"

# === PDF Naming Patterns === #
REGISTRATION_PDF_NAME = "registration_{reg_no}.pdf"
APPLICATION_PDF_NAME = "application_form_{reg_no}.pdf"

# === Auth Settings (to be filled from browser each time) === #
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Referer": "https://foscos.fssai.gov.in/",
    "Content-Type": "application/json",
    "Authorization": BEARER_TOKEN,
    "x-auth-user-id": "f33RY6DAyt+WQt8UJG54SQUxr5GrXYXkSwv4uzKRUiI=",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Priority": "u=0"
}

COOKIES = {
    "_ga": "GA1.3.1387273733.1752841346",
    "_gid": "GA1.3.1395180104.1752841346",
    "_ga_E101FG0RXN": "GS2.3.s1752850885$o4$g1$t1752851351$j60$l0$h0",
    "key_20521031000795": "ZFPF3b4Rwihz9PiHWxvfJ8ou2rb8NjE8rGW9nMy/hmA=",
    "_ga_X6L29149T6": "GS2.3.s1752841503$o1$g1$t1752842990$j19$l0$h0",
    "_gat": "1"
}

# === URLs === #
REGISTRATION_FORM_URL = "https://foscos.fssai.gov.in/gateway/downloadpdf2/registration/{reg_no}"
APPLICATION_FORM_URL = "https://foscos.fssai.gov.in/gateway/downloadpdf2/forma/{reg_no}"

# === Threading Settings === #
MAX_WORKERS = 25

# === Ensure folders exist === #
PDF_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)