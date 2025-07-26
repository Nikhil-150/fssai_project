import pdfplumber
import re
import logging
from pathlib import Path


class PDFExtractorSegment1:
    def __init__(self, reg_id: str, application_path: Path, registration_path: Path):
        self.reg_id = reg_id
        self.application_path = application_path
        self.registration_path = registration_path

    def extract(self) -> dict | None:
        try:
            app_text = self._extract_text(self.application_path)
            reg_text = self._extract_text(self.registration_path)

            app_no = self._find(app_text, r"Application No:\s*(\d+)")
            reg_no = self._find(reg_text, r"Registration Number:?:?\s*(\d+)")

            # REF = register ID used for downloading both files
            ref = self.reg_id

            # Validity From – from last row of table on page 3
            validity_from = self._find_from_table_on_page(
                self.registration_path,
                start_page=3,
                target_column="Validity From"
            )

            # Match full line first, then split
            sub_div_line1 = ""
            match1 = re.search(r"(Sub-Division/Station/.*)", app_text)
            if match1:
                full_line = match1.group(1).strip()
                # Remove the heading part
                sub_div_line1 = full_line.replace("Sub-Division/Station/", "").replace(":", "").strip()

            # Same for Division(Railways):
            sub_div_line2 = ""
            match2 = re.search(r"(Division\(Railways\):.*)", app_text)
            if match2:
                full_line = match2.group(1).strip()
                sub_div_line2 = full_line.replace("Division(Railways):", "").strip()

            # Final clean result
            sub_division = f"{sub_div_line1} {sub_div_line2}".strip()

            # Address block under Application
            address_of_location = self._find(
                app_text,
                r"Address of Premises Where Food Business Is Located[\w\W]*?Address\s*:\s*([^\n]+)"
            )
            pin_code = self._find(app_text, r"Pin Code:\s*([^\n]+)")
            # Pin code must be extracted from application form earlier
            pin_code = pin_code.strip()

            match = re.search(r"Name and permanent address of Food\s*:?\s*([^\n]+)", reg_text, re.IGNORECASE)
            value = match.group(1).strip() if match else ""

            # Pattern:
            # - Matches "Business Operator (FBO)" (optionally followed by / Hindi)
            # - Optionally matches next line if it's Hindi (ऑपरेटर का नाम और स्थायी पता:)
            # - Then captures all lines until the pin code
            pattern = (
                    r"Business Operator\s*\(FBO\)(?:\s*/[^\n]*)?\s*(?:\n[^\n]*ऑपरेटर.*?:)?\s*([\w\W]+?)"
                    + pin_code
            )
            match = re.search(pattern, reg_text, re.IGNORECASE)
            block = match.group(1).strip() if match else ""

            # Optionally split lines
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            name = lines[0] if lines else ""
            address = " ".join(lines[1:]).strip() if len(lines) > 1 else ""
            concat_address = name + " " + address + " " + pin_code
            redundant = "ऑपरेटर का नाम और स्थायी पता: "
            if redundant in concat_address:
                concat_address = concat_address.replace(redundant, "")

            kob_match = re.search(
                r"Kind of Business(?:\s*/\s*[^:\n]+)?\s*:?\s*([^\n]+)",
                reg_text,
                re.IGNORECASE
            )
            kind_of_business = kob_match.group(1).strip() if match else ""
            data = {
                "Registration No.:": reg_no,
                "NAME OF FOOD BUSINESS OPERATOR": value,
                "Address of location where food business": concat_address,
                "REF": ref,
                "District/Region/Zone:": self._extract_block_between(app_text, "District/Region/Zone", "Village", ["State", "Sub-Division/Station", "Pan No", "Division(Railways):"]),
                "State": self._find(app_text, r"State:\s*([^\n]+)"),
                "Mobile No:": self._find(app_text, r"Mobile No:\s*([^\n]+?)\s*Email-ID"),
                "Contact Person": self._extract_block_between(app_text, "Contact Person", "Other Details", ["Email-ID"]),
                "Application No": app_no,
                "Kind of Business": kind_of_business,
                "Validity Upto": self._find(reg_text, r"(?:Valid Upto|वैधता):?\s*(\d{2}-\d{2}-\d{4})"),
                "Validity From": validity_from,
                "Issued On": self._find(reg_text, r"Issued On\s*/?\s*(?:िदनांक)?\s*:?\s*(\d{2}-\d{2}-\d{4})"),
                "Fee Paid": self._add_inr(self._find(app_text, r"Amount\s*\n.*?(\d+\.\d+)", re.DOTALL)),
                "Type": self._find(app_text, r"Application Type:?:?\s*(.+)"),
                "Village": self._extract_block_between(app_text, "Village", "Pin Code", ["Sub-Division", "Pan No"]),
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

    def _find_from_table_on_page(self, pdf_path: str | Path, start_page: int, target_column: str) -> str:
        """
        Extracts 'target_column' from the last row of the first matching table
        between start_page and end of PDF.
        """
        pdf_path = str(pdf_path)
        import pdfplumber

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for i in range(start_page - 1, len(pdf.pages)):
                    table = pdf.pages[i].extract_table()
                    if table and len(table) > 1:
                        header = table[0]
                        if target_column in header:
                            col_idx = header.index(target_column)
                            last_row = table[-1]
                            if len(last_row) > col_idx:
                                return last_row[col_idx].strip()
        except Exception as e:
            logging.warning(f"{self.reg_id} - Failed to extract '{target_column}' from table: {e}")

        return ""

    def _extract_block_between(self, text: str, start_heading: str, bottom_stopper: str,
                               right_stoppers: list[str] = None) -> str:
        """
        Extracts text block between start_heading and stop headings (bottom/right).
        """
        import re

        pattern = rf"{re.escape(start_heading)}\s*:?([\w\W]+?)({re.escape(bottom_stopper)}|$)"
        match = re.search(pattern, text)
        if match:
            block = match.group(1)
            if right_stoppers:
                for stopper in right_stoppers:
                    block = re.split(rf"{re.escape(stopper)}", block)[0]
            return block.strip()
        return ""

