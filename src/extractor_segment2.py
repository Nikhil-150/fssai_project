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
            print(f"[TRACE] Starting extraction for: {self.input_id}")
            licence_text = self._extract_text(self.licence_path)
            third_last_page_text = self._get_third_last_page_text(self.licence_path)

            # Split third-last page to isolate two sections
            split_sections = third_last_page_text.split(
                "Person responsible for complying with conditions of license", 1
            )
            operations_section = split_sections[0]
            compliance_section = split_sections[1] if len(split_sections) > 1 else ""

            pin_code = self._find(operations_section, r"Pin Code:\s*([^\n]*?)\s+Photo Id Card:")
            # escaped_pin_code = re.escape(pin_code.strip())

            # Table values (DOI, Validity From, Upto, etc.)
            license_table_data = self._extract_license_table_fields(self.licence_path)

            doi = self._find(licence_text, r"Issued On(?:\s*/\s*िदनांक)?:\s*(\d{2}-\d{2}-\d{4})")
            validity_upto = self._find(licence_text, r"Valid Upto(?:\s*:?\s*/\s*वैधता)?\s*:?\s*(\d{2}-\d{2}-\d{4})")

            authorized_address = self._extract_authorized_address(licence_text)

            data = {
                "NAME": self._find(licence_text, r"Name & Registered Office address of\s*:?\s*([^\n]+)"),
                "Address of Authorized Premises": authorized_address,
                "DISTRICT": self._find(operations_section, r"District:\s*([^\n]+)"),
                "STATE": self._find(operations_section, r"State:\s*([^\n]*?)\s+District:"),
                "KIND OF BUSINESS": self._kind_of_business(licence_text),
                "Person in charge of operations Name:": self._find(operations_section, r"Name:\s*([^\n]*?)\s+Qualification:"),
                "Person in charge of operations Mobile:": self._find(operations_section, r"Mobile No:\s*([^\n]+)"),
                "Y": (
                    (datetime.strptime(validity_upto, "%d-%m-%Y") - datetime.strptime(doi, "%d-%m-%Y")).days // 364
                    if validity_upto and doi
                    else ""
                ),
                "REF ID": self.input_id,
                "AMOUNT": license_table_data["AMOUNT"],
                "LICENSE NUMBER": self._find(licence_text, r"License Number:\s*(\d+)"),
                "Person responsible for complying MOBILE": self._find(compliance_section, r"Mobile No:\s*([^\n]+)"),
                "EXPIRY": validity_upto,
                "DOI": doi,
                "TYPE": license_table_data["TYPE"],
                "CATEGORY OF LICENSE": self._category_of_licence(licence_text),
                "SUB DIVISION": self._extract_sub_division_from_address(authorized_address),
                "PIN CODE": pin_code,
                "Person in charge of operations E-mail": self._find(operations_section, r"Email-ID:\s*([^\n\r]+?)(?=\s*Address)"),
                "VALIDITY FROM": license_table_data["VALIDITY FROM"],
                "ISSUED ON": license_table_data["ISSUED ON"],
            }
            print(f"[TRACE] Successfully built data for: {self.input_id}")
            return data
        except Exception as e:
            print(f"[ERROR] Exception in extract(): {self.input_id} - {e}")
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

    def _kind_of_business(self, licence_text):
        # Kind of Business
        kind_match = re.search(
            r"Kind of Business\s*(?:/[^:\n]*)?\s*:?\s*([\w\W]*?)\n\s*4\.\s*Dairy Business Details",
            licence_text,
            re.IGNORECASE
        )

        if kind_match:
            raw_value = kind_match.group(1).strip()
            # Replace all line breaks and extra spacing with a single space
            kind_of_business = re.sub(r'\s*\n\s*', ' ', raw_value)
        else:
            kind_of_business = ""

        return kind_of_business

    def _extract_authorized_address(self, licence_text: str) -> str:
        """
        Extract the full address under '2. Address of Authorized Premises'
        from the licence text. Supports English-only and bilingual headings.
        Stops extraction at '3. Kind of Business'.
        """
        # Step 1: Extract block
        pattern = r"Address of Authorized Premises[\w\W]+?(?=\n\s*3\.\s*Kind of Business)"
        match = re.search(pattern, licence_text, re.IGNORECASE)

        if not match:
            return ""

        block = match.group(0).strip()

        # Step 2: Remove all known unwanted heading fragments
        cleanup_patterns = [
            r"Address of Authorized Premises\s*/?.*?:?",  # English heading
            r"प्राधिकृत परिसर का पता[:：]?",  # Hindi version
            r"पिरसरो का पता[:：]?",  # Common Hindi line
            r"प्रािधकृत",  # Standalone unwanted Hindi word
        ]

        for pat in cleanup_patterns:
            block = re.sub(pat, '', block, flags=re.IGNORECASE)

        # Step 3: Normalize whitespace and return
        block = re.sub(r'\s*\n\s*', ', ', block)  # Convert newlines to commas
        block = re.sub(r',\s*,', ', ', block)  # Fix double commas
        return block.strip()

    def _category_of_licence(self, licence_text):
        # Category of License
        category_match = re.search(
            r"Category of License(?:\s*/[^\n]*)?:\s*([^\n]+)", licence_text
        )
        category_of_license = category_match.group(1).strip() if category_match else ""

        return category_of_license

    def _extract_sub_division_from_address(self, address: str) -> str:
        """
        Extracts Sub-Division from the authorized address string.
        It walks backward from the Pin Code -> State -> District -> Sub-Division.
        """
        # Normalize commas, remove duplicate commas
        address = re.sub(r',+', ',', address.strip())

        # Split by comma and clean individual parts
        parts = [part.strip() for part in address.split(',') if part.strip()]

        # Look from the end to find a 6-digit pin code
        for i in range(len(parts) - 1, 2, -1):
            if re.search(r'\b\d{6}\b', parts[i]):  # Pin Code
                try:
                    sub_division = parts[i - 2]  # 3 elements before pin code
                    return sub_division.strip()
                except IndexError:
                    return ""

        return ""


