from config.settings import INPUT_EXCEL_PATH
import pandas as pd


def _load_registration_numbers():
    file_path = INPUT_EXCEL_PATH
    if not file_path.exists():
        raise FileNotFoundError(f"Excel file not found at: {file_path}")

    df = pd.read_excel(file_path)
    print(f"[DEBUG] Columns in Excel: {df.columns}")
    print(f"[DEBUG] Data Preview:\n{df.head()}")

    # Adjust based on header
    reg_list = df.iloc[:, 0].dropna().astype(str).tolist()
    reg_list = reg_list[:1000]
    print(f"[INFO] Loaded {len(reg_list)} registration numbers.")
    return reg_list


if __name__ == "__main__":
    _load_registration_numbers()