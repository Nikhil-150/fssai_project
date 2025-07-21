import pdfplumber
import re
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    filename='logs/extraction.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class PDFExtractor:
    def __init__(self, reg_id: str, application_path: Path, registration_path: Path):
        self.reg_id = reg_id
        self.application_path = application_path
        self.registration_path = registration_path

    def extract(self) -> dict | None:
        try:
            app_text = self._extract_text(self.application_path)
            reg_text = self._extract_text(self.registration_path)

            app_no = self._find(app_text, r"Application No:\s*(\d+)")
            app_date = self._find(app_text, r"Application Date:\s*(\d{2}-\d{2}-\d{4})")
            reg_no = self._find(reg_text, r"Registration Number:?:?\s*(\d+)")
            issued_on = self._find(reg_text, r"Issued On\s*/\s*िदनांक:?:?\s*(\d{2}-\d{2}-\d{4})")

            document_id_application = f"{app_no[-9:]}_{app_date}-application-certificate" if app_no and app_date else ""
            document_id_registration = f"{reg_no[-9:]}_{issued_on}-registration-certificate" if reg_no and issued_on else ""
            combined_document_id = f"{reg_no[-9:]}_{issued_on}" if reg_no and issued_on else ""

            firm_name, applicant_name = self._split_firm_and_name(
                self._find(app_text, r"Name of Applicant\s*/\s*([\w\W]+?)\s*Application Date")
            )

            data = {
                "Application No.": app_no,
                "Application Type": self._find(app_text, r"Application Type:?:?\s*(.+)"),
                "Application Date": app_date,
                "Expiry Date": self._find(reg_text, r"Valid Upto\s*:?/?\s*:?\s*(\d{2}-\d{2}-\d{4})"),
                "District/Region/Zone": self._find(app_text, r"District/Region/Zone:\s*([^\n]+)"),
                "Village": self._find(app_text, r"Village:\s*([^\n]+)"),
                "PIN Code": self._find(app_text, r"Pin Code:\s*([^\n]+)"),
                "State": self._find(app_text, r"State:\s*([^\n]+)"),
                "Sub-Division": self._find(app_text, r"Sub-Division/Station/.*?:?\s*([^\n]+)"),
                "Contact Person": self._find(app_text, r"Contact Person:\s*([^\n]+)"),
                "Mobile No.": self._find(app_text, r"Mobile No:\s*([^\n]+)"),
                "Name of the food category": self._find(reg_text, r"Name of the food category.*?\n(.+)"),
                "District": self._find(app_text, r"District/Region/Zone:\s*([^\n]+)"),
                "Name of Company": firm_name,
                "Address": self._find(app_text, r"Address:\s*(.+?)\nDistrict", re.DOTALL),
                "Kind of Business": self._find(reg_text, r"Kind of Business.*?:\s*(\w+)"),
                "Validity From": issued_on,
                "Validity Upto": self._find(reg_text, r"(?:Valid Upto|वैधता):?\s*(\d{2}-\d{2}-\d{4})"),
                "Issued On": issued_on,
                "Fee Paid": self._add_inr(self._find(app_text, r"Amount\s*\n.*?(\d+\.\d+)", re.DOTALL)),
                "Type": self._find(app_text, r"Application Type:?:?\s*(.+)"),
                "Registration NO.": reg_no,
                "Document ID Registration": document_id_registration,
                "Combined Document ID": combined_document_id
            }

            return data
        except Exception as e:
            logging.error(f"{self.reg_id} - Extraction failed: {e}")
            return None

    def _extract_text(self, pdf_path: Path) -> str:
        with pdfplumber.open(pdf_path) as pdf:
            return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

    def _find(self, text: str, pattern: str, flags=0) -> str:
        match = re.search(pattern, text, flags)
        if match:
            return match.group(1).strip()

        return ""

    def _split_firm_and_name(self, text: str) -> tuple[str, str]:
        if "/" in text:
            parts = text.split("/")
            firm = parts[0].strip()
            name = "/".join(parts[1:]).strip()
            return firm, name
        return "", ""

    def _extract_after_slash(self, text: str) -> str:
        if "/" in text:
            return text.split("/")[-1].strip()
        return text.strip()

    def _add_inr(self, fee: str) -> str:
        return f"{fee} INR" if fee else ""
