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

            # REF = register ID used for downloading both files
            ref = self.reg_id

            # Validity From – from last row of table on page 3
            validity_from = self._find_from_table_on_page(
                self.registration_path,
                page_number=3,
                target_column="Validity From"  # your logic in the helper method
            )

            # Sub-Division full line
            sub_division = self._find(app_text, r"Sub-Division/Station/.*?:?\s*([^\n]+(?:\n[^\n]+)?)")

            # Full firm/applicant block for fallback
            name_block = self._find(
                app_text,
                r"Name of Applicant\s*/\s*([\w\W]+?)\s*Application Date"
            )
            name_of_firm = name_block.strip().replace("\n", " ") if name_block else ""

            # Address block under Application
            address_of_location = self._find(
                app_text,
                r"Address of Premises Where Food Business Is Located[\w\W]*?Address\s*:\s*([^\n]+)"
            )

            data = {
                "Registration No.:": reg_no,
                "NAME OF FOOD BUSINESS OPERATOR": name_of_firm,
                "Address of location where food business": address_of_location,
                "REF": ref,
                "District/Region/Zone:": self._find(app_text, r"District/Region/Zone:\s*([^\n]+)"),
                "State": self._find(app_text, r"State:\s*([^\n]+)"),
                "Mobile No:": self._find(app_text, r"Mobile No:\s*([^\n]+)"),
                "Contact Person": self._find(app_text, r"Contact Person:\s*([^\n]+)"),
                "Application No": app_no,
                "Kind of Business": self._find(reg_text, r"Kind of Business.*?:\s*([^\n]+)"),
                "Validity Upto": self._find(reg_text, r"(?:Valid Upto|वैधता):?\s*(\d{2}-\d{2}-\d{4})"),
                "Validity From": validity_from,
                "Issued On": issued_on,
                "Fee Paid": self._add_inr(self._find(app_text, r"Amount\s*\n.*?(\d+\.\d+)", re.DOTALL)),
                "Type": self._find(app_text, r"Application Type:?:?\s*(.+)"),
                "Village": self._find(app_text, r"Village:\s*([^\n]+)"),
                "Pin Code": self._find(app_text, r"Pin Code:\s*([^\n]+)"),
                "Sub-Division": sub_division,
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

    def _find_from_table_on_page(self, pdf_path: str | Path, page_number: int, target_column: str) -> str:
        """
        Extract from the last row of a table on the given page number.
        You can use `pdfplumber` to extract the table.
        """
        pdf_path = str(pdf_path)  # ensure compatibility with pdfplumber
        import pdfplumber
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) >= page_number:
                    table = pdf.pages[page_number - 1].extract_table()
                    if table and len(table) > 1:
                        last_row = table[-1]
                        # Choose the correct column from the last_row index
                        # Example: validity_from = last_row[2]  # Adjust index based on table format
                        return last_row[2].strip() if len(last_row) > 2 else ""
        except Exception as e:
            logging.warning(f"{self.reg_id} - Failed to extract validity from: {e}")
        return ""

