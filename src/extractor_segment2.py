import pdfplumber
import re
import logging
from pathlib import Path
from datetime import datetime

class PDFExtractorSegment2:
    def __init__(self, input_id: str, licence_path: Path):
        self.input_id = input_id
        self.licence_path = licence_path

    def extract(self) -> dict | None:
        try:
            licence_text = self._extract_text(self.licence_path)

            third_page_licence_text = self._get_third_last_page_text(self.licence_path)
            split_text = third_page_licence_text.split(
                "Person responsible for complying with conditions of license", 1
            )

            section1 = split_text[0]  # "Person in charge of operations" section
            section2 = split_text[1] if len(split_text) > 1 else ""  # Responsible person section

            pin_code = self._find(section1, r"Pin Code:\s*([^\n]*?)\s+ Photo Id Card:")
            escaped_pin = re.escape(pin_code.strip())

            pattern = (
                    r"(?:Name & Registered Office address of\s*"
                    r"(?:Licensee[^\n]*\n)?"  # optional second line
                    r"(?:और पता:)?\s*)"
                    r"([\w\W]+?)\b" + escaped_pin
            )

            match = re.search(pattern, licence_text, re.IGNORECASE)
            address_block = match.group(1).strip() if match else ""

            match = re.search(
                r"Kind of Business(?:\s*/[^\n]*)?\s*:?\s*([\w\W]+?)\n\s*Dairy Business Details",
                licence_text,
                re.IGNORECASE
            )
            if match:
                kind_of_business = match.group(1).strip()
            else:
                kind_of_business = ""

            match = re.search(
                r"Category of License(?:\s*/[^\n]*)?:\s*([^\n]+)",
                licence_text
            )
            if match:
                category_of_license = match.group(1).strip()
            else:
                category_of_license = ""

            read_table = self._extract_license_table_fields(self.licence_path)

            doi = self._find(licence_text, r"Issued On(?:\s*/\s*िदनांक)?:\s*(\d{2}-\d{2}-\d{4})")
            validity_upto = self._find(licence_text, r"Valid Upto(?:\s*/\s*वैधता)?:\s*(\d{2}-\d{2}-\d{4})")

            # Extract Address of Authorized Premises
            authorized_address = ""
            address_pattern_english = r"Address of Authorized Premises:([\w\W]+?)" + re.escape(pin_code)
            address_pattern_bilingual = r"Address of Authorized Premises\s*/\s*प्रािधकत\s*\nपिरसरो का पता:([\w\W]+?)" + re.escape(
                pin_code)

            match1 = re.search(address_pattern_bilingual, licence_text, re.IGNORECASE)
            match2 = re.search(address_pattern_english, licence_text, re.IGNORECASE)

            if match1:
                authorized_address = match1.group(1).strip()
            elif match2:
                authorized_address = match2.group(1).strip()

            # Fetch Sub Division
            # Step 1: Match from State–PIN backwards
            sub_division = ""
            match = re.search(
                r"(?P<subdivision>.+?),\s*(?P<district>[A-Za-z ]+),\s*(?P<state>[A-Za-z ]+)-(?P<pincode>\d{6})$",
                authorized_address)

            if match:
                sub_division = match.group("subdivision").strip()
            else:
                print("Pattern not matched.")

            data = {
                "NAME": self._find(licence_text, r"Name & Registered Office address of\s*:?\s*([^\n]+)"),
                "Address of Authorized Premises": address_block,
                "DISTRICT": self._find(section1, r"District:\s*([^\n]+)"),
                "STATE": self._find(section1, r"State:\s*([^\n]*?)\s+District:"),
                "KIND OF BUSINESS": kind_of_business,
                "Person in charge of operations Name:": self._find(section1, r"Name:\s*([^\n]*?)\s+Qualification:"),
                "Person in charge of operations Mobile:": self._find(section1, r"Mobile No::\s*([^\n]+)"),
                "Y": (datetime.strptime(validity_upto, "%d-%m-%Y") - datetime.strptime(doi, "%d-%m-%Y")).days // 365,
                "REF ID": self.input_id,
                "AMOUNT": read_table["AMOUNT"],
                "LICENSE NUMBER": self._find(licence_text, r"License Number:\s*(\d+)"),
                "Person responsible for complying MOBILE": self._find(section2, r"Mobile No::\s*([^\n]+)"),
                "EXPIRY": validity_upto,
                "DOI": doi,
                "TYPE": read_table["TYPE"],
                "CATEGORY OF LICENSE": category_of_license,
                "SUB DIVISION": sub_division,
                "PIN CODE": pin_code,
                "Person in charge of operations E-mail": self._find(section1, r"Email-ID:\s*([^\n]*?)\s+Address:"),
                "VALIDITY FROM": read_table["VALIDITY FROM"],
                "ISSUED ON": read_table["ISSUED ON"],
            }

            return data
        except Exception as e:
            logging.error(f"{self.input_id} - Extraction failed: {e}")
            return None

    def _extract_text(self, pdf_path: Path) -> str:
        with pdfplumber.open(pdf_path) as pdf:
            return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

    def _find(self, text: str, pattern: str, flags=0) -> str:
        match = re.search(pattern, text, flags)
        if match:
            return match.group(1).strip()

        return ""

    def _get_third_last_page_text(self, pdf_path: Path) -> str:
        import pdfplumber

        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) >= 3:
                third_last_page = pdf.pages[-3]  # Negative index: -1 is last, -2 is second-last, -3 is third-last
                return third_last_page.extract_text() or ""
            else:
                return ""  # PDF has fewer than 3 pages

    def _extract_license_table_fields(self, pdf_path: Path) -> dict:
        result = {
            "VALIDITY FROM": "",
            "EXPIRY": "",
            "ISSUED ON": "",
            "AMOUNT": "",
            "TYPE": ""
        }

        with pdfplumber.open(pdf_path) as pdf:
            # Check all pages except the last 3
            for page in pdf.pages[:-3]:
                tables = page.extract_tables()
                for table in tables:
                    if not table or len(table) < 2:
                        continue  # Skip empty or header-only tables

                    headers = [cell.strip() if cell else "" for cell in table[0]]

                    # Ensure it's the expected table
                    if "Validity From" in headers and "Fee Paid" in headers:
                        last_row = table[-1]
                        try:
                            result["VALIDITY FROM"] = last_row[headers.index("Validity From")].strip()
                            result["EXPIRY"] = last_row[headers.index("Validity Upto")].strip()
                            result["ISSUED ON"] = last_row[headers.index("Issued On")].strip()
                            result["AMOUNT"] = last_row[headers.index("Fee Paid")].strip()
                            result["TYPE"] = last_row[headers.index("Type")].strip()
                            return result
                        except Exception:
                            continue  # Gracefully skip if column mismatch

        return result

