# CSV Analyser
An interactive CSV exploration and cleaning dashboard built with Python, Pandas, NumPy, Streamlit, and Plotly.

## Features
- Upload CSV files from the browser.
- View row count, column count, missing cells, and duplicate rows.
- Preview the first 100 rows and inspect column data types.
- Review per-column missing-value percentages and unique-value counts.
- Explore numeric summary statistics and categorical value counts.
- Create interactive histograms, bar charts, scatter plots, and box plots.
- Optionally trim text whitespace, remove duplicate rows, and fill missing values.
- Download a cleaned CSV without changing the original uploaded data.

## Requirements
- Python 3.10–3.12 recommended
- pip
- VS Code (recommended)

## Run locally on Windows
Open PowerShell in this project folder.

### 1. Create a virtual environment

```powershell
py -m venv .venv
```

### 2. Activate it
```powershell
.\.venv\Scripts\Activate.ps1
```
If PowerShell blocks activation, you can use Command Prompt instead:
```bat
.venv\Scripts\activate.bat
```
Or run the environment's Python directly without activation:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Install dependencies
```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Launch the app
```powershell
python -m streamlit run app.py
```
Streamlit will show a local URL

## Quick test
Run the automated utility tests:
```powershell
python -m pytest -q
```
You can also create a sample CSV manually and upload it:

## Project structure

```text
CSV_Analyser/
├── app.py
├── csv_utils.py
├── requirements.txt
├── README.md
├── .gitignore
└── tests/
    └── test_csv_utils.py
```
## Limitations
- The app currently accepts CSV files only, not Excel workbooks.
- Numeric columns are detected from the types inferred by Pandas. Numbers stored as text may need preprocessing.
- Cleaning is intentionally simple and should be reviewed before using the exported file for important decisions.
- Large files may be limited by the hosting service's available memory.
- No user accounts, database, or permanent file storage are included.

## Future improvements
- Add configurable file-size limits and more robust large-file handling.
- Add date-column detection and time-series charts.
- Add downloadable data-quality reports.
- Add a data-type conversion panel for numeric values stored as text.
- Online deployement