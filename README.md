# 📄 FSSAI Data Extraction Tool

This tool extracts structured data from PDFs (Registration + Application Forms or Licence Certificates) obtained from the FSSAI system, and exports the results to Excel.

---

## 📦 Project Structure
project_root/
├── config/
│ └── bearer_token.txt # Daily token must be saved here
├── data/
│ ├── pdf/
│ │ ├── application forms/ # Downloaded Application PDFs
│ │ ├── registration forms/ # Downloaded Registration PDFs
│ │ └── licence forms/ # Downloaded Licence PDFs (Segment 2)
│ ├── registration_numbers.xlsx # Input for Segment 1
│ ├── state.xlsx # Input for Segment 2
│ └── Output Excels/
│ ├── Registration_Segment_1_Output.xlsx
│ └── Licence_Segment_2_Output.xlsx
├── src/
│ ├── downloader.py # Handles PDF downloads
│ ├── extractor.py # Extracts data from PDFs
│ ├── orchestrator.py # Coordinates workflow
│ ├── utils.py # Utility functions
│ └── init.py
├── config/
│ └── settings.py
├── requirements.txt # Required Python packages
├── main.py # Entry point
└── README.md # You're here


---

## 🛠️ Setup Instructions (PyCharm)

1. **Extract the ZIP** anywhere on your system.
2. **Open the folder in PyCharm.**
3. When prompted:
   - Select **"Create a new virtual environment"** (`.venv`) — this is preferred to avoid conflicts with other projects.
4. After the `.venv` is created:
   - Open **Terminal** inside PyCharm.
   - Run:
     ```bash
     .venv\Scripts\activate
     ```
   - Once activated, your terminal prompt will show: `(venv)`  
   - Now install required libraries:
     ```bash
     pip install -r requirements.txt
     ```
   - After installation, you may close the terminal.

---

## ⚙️ Configuration Details

- **Bearer Token**:  
  Save the daily token inside: config/bearer_token.txt


- **Input Excel Files**:
- **Segment 1**:  
  Input file: `registration_numbers.xlsx`  
  Location: `data/`  
  Contains the REF IDs to fetch registration and application PDFs.

- **Segment 2**:  
  Input file: `state.xlsx`  
  Location: `data/`  
  Contains the REF IDs to fetch licence PDFs.

- **PDF Storage Locations**:
- Application PDFs → `data/pdf/application forms/`
- Registration PDFs → `data/pdf/registration forms/`
- Licence PDFs → `data/pdf/licence forms/`

- **Excel Output Files**:
- Segment 1: `data/Output Excels/Registration_Segment_1_Output.xlsx`
- Segment 2: `data/Output Excels/Licence_Segment_2_Output.xlsx`

---

## ▶️ How to Run the Project

1. In PyCharm, right-click `main.py` and select **Run 'main'**  
 *(Alternatively, use the steps below to configure Run properly.)*

---

## ⚙️ PyCharm Run Configuration (Important)

1. Go to **Run > Edit Configurations** in the top menu.
2. Click the **`+`** icon and choose **Python**.
3. Name it: `FSSAI Main Run`
4. Set:
 - **Script path**: Point to `main.py`
 - **Python interpreter**: Select the one from `.venv`
5. Click **OK**, then click **Run > Run 'FSSAI Main Run'**

---

## 🧪 Usage Instructions

1. When `main.py` runs, you'll be prompted:
👉 Do you want to work with Segment 1 or Segment 2?
📌 Type '1' for Segment 1 (Registration + Application)
📌 Type '2' for Segment 2 (Licence Certificate Only)
2. Based on your input:
   - The tool will download PDFs using the bearer token
   - Parse the data
   - Save results to the appropriate Excel file




