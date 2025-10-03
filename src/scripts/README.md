# SEC Filings Data Extraction Scripts

Automated data extraction from Richtech Robotics SEC filings in Excel format.

## Overview

This suite of Python scripts extracts structured data from various SEC filing types and converts them to CSV format for analysis.

## Supported Filing Types

| Filing Type | Description | Files | Extractors |
|------------|-------------|-------|------------|
| **Form 4** | Insider transactions | 5 | `extract_form4.py` |
| **10-Q** | Quarterly financial reports | 6 | `extract_10q.py` |
| **10-K** | Annual financial reports | 2 | `extract_10k.py` |
| **8-K** | Current event reports | 17 | `extract_8k.py` |
| **DEF 14A** | Proxy statements | 1 | `extract_def14a.py` |
| **S-1/424B4** | Registration statements | 3 | `extract_registration.py` |

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `pandas` - Data manipulation
- `openpyxl` - Excel file handling
- `numpy` - Numerical operations

## Usage

### Quick Start - Extract All Data

```bash
cd src/scripts
python run_extraction.py
```

This will process all Excel files from `data/raw/` and save CSV outputs to `data/processed/`.

### Run Specific Extractor

```bash
# Extract only Form 4 data
python run_extraction.py --only form4

# Extract only 10-Q data
python run_extraction.py --only 10q

# Extract only 10-K data
python run_extraction.py --only 10k
```

### Skip Specific Extractor

```bash
# Run all except 8-K (which can be slow)
python run_extraction.py --skip 8k
```

### Save Detailed Report

```bash
python run_extraction.py --save-report
```

This creates a JSON report in `data/processed/` with detailed extraction results.

### Run Individual Extractors

You can also run each extractor independently:

```bash
# From src/scripts directory
python extraction/extract_form4.py
python extraction/extract_10q.py
python extraction/extract_10k.py
python extraction/extract_8k.py
python extraction/extract_def14a.py
python extraction/extract_registration.py
```

## What Gets Extracted

### Form 4 - Insider Transactions
- Reporting person information (name, title, relationship)
- Non-derivative securities transactions (stock purchases/sales)
- Derivative securities transactions (options, warrants)

**Output files:**
- `form4_nonderivative_[date]_[person].csv`
- `form4_derivative_[date]_[person].csv`

### 10-Q - Quarterly Reports
- Balance sheets (assets, liabilities, equity)
- Income statements (revenue, expenses, net income)
- Cash flow statements
- Stockholders' equity statements
- Revenue breakdown by segment
- Earnings per share (EPS)

**Output files:**
- `10q_balance_sheet_[date].csv`
- `10q_income_statement_[date].csv`
- `10q_cash_flow_[date].csv`
- `10q_stockholders_equity_[date].csv`
- `10q_revenue_breakdown_[date].csv`
- `10q_earnings_per_share_[date].csv`

### 10-K - Annual Reports
- All financial statements (like 10-Q)
- Revenue model breakdown
- Patent information
- Trademark information
- Employee data by function
- Property/facility information
- Executive compensation
- Security ownership

**Output files:**
- `10k_revenue_model_[date].csv`
- `10k_patents_[date].csv`
- `10k_trademarks_[date].csv`
- `10k_employees_[date].csv`
- `10k_properties_[date].csv`
- `10k_compensation_[date].csv`
- `10k_ownership_[date].csv`
- `10k_balance_sheet_[date].csv`
- `10k_income_statement_[date].csv`

### 8-K - Current Reports
- Filing metadata (items reported, dates)
- Payment schedules
- Embedded tables
- Exhibit information
- Signature details

**Output files:**
- `8k_metadata_[date].csv`
- `8k_payment_schedule_[date].csv` (if applicable)
- `8k_table_[date]_[sheet_name].csv`
- `8k_exhibit_[date]_[exhibit_name].csv`

### DEF 14A - Proxy Statements
- Executive compensation tables
- Director compensation
- Beneficial ownership of securities
- Audit fees
- Stock option grants

**Output files:**
- `def14a_executive_compensation_[date].csv`
- `def14a_director_compensation_[date].csv`
- `def14a_beneficial_ownership_[date].csv`
- `def14a_audit_fees_[date].csv`
- `def14a_stock_options_[date].csv`

### S-1/424B4 - Registration Statements
- Offering information (shares, pricing)
- Pre-IPO ownership
- Beneficial ownership tables
- Use of proceeds
- Placement agent warrants
- Financial statements

**Output files:**
- `[form_code]_offering_info_[date].csv`
- `[form_code]_preipo_ownership_[date].csv`
- `[form_code]_beneficial_ownership_[date].csv`
- `[form_code]_use_of_proceeds_[date].csv`
- `[form_code]_placement_warrants_[date].csv`

## Project Structure

```
src/scripts/
├── extraction/           # Individual extractor modules
│   ├── extract_form4.py
│   ├── extract_10q.py
│   ├── extract_10k.py
│   ├── extract_8k.py
│   ├── extract_def14a.py
│   └── extract_registration.py
├── utils/               # Utility functions
│   ├── excel_parser.py  # Excel file handling
│   └── data_cleaner.py  # Data cleaning functions
├── run_extraction.py    # Master script
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Utility Modules

### `utils/excel_parser.py`

Functions for reading and parsing Excel files:
- `get_filing_metadata()` - Extract metadata from filename
- `read_excel_with_merged_cells()` - Handle merged cells
- `find_sheets_by_keyword()` - Find sheets by name patterns
- `extract_table_from_sheet()` - Extract clean tables
- `detect_table_boundaries()` - Find actual data boundaries

### `utils/data_cleaner.py`

Functions for cleaning extracted data:
- `clean_numeric_value()` - Handle currency, percentages, negatives
- `standardize_date()` - Convert dates to ISO format
- `clean_financial_table()` - Clean financial data tables
- `remove_empty_rows_cols()` - Remove formatting rows/columns
- `standardize_column_names()` - Normalize column names

## Data Handling Notes

### Numeric Data
- Values in parentheses `(123)` are converted to negative `-123`
- Currency symbols and commas are removed: `$1,234.56` → `1234.56`
- Percentages are converted: `45%` → `0.45`
- "In thousands" notation is handled (multiplied by 1000 where appropriate)

### Date Formats
- All dates are standardized to ISO format: `YYYY-MM-DD`
- Handles various input formats: `January 15, 2024`, `01/15/2024`, etc.

### Missing Values
- Common representations (`-`, `N/A`, `None`) are converted to `NaN`
- Empty rows and columns used for formatting are removed

### Merged Cells
- Merged cells are detected and values are propagated
- Multi-level headers are combined into single column names

## Troubleshooting

### Import Errors
```bash
# If you see "ModuleNotFoundError"
pip install -r requirements.txt
```

### Empty Output Files
- Check that input files exist in `data/raw/`
- Verify Excel files are not corrupted
- Run with `--verbose` flag for detailed output

### Encoding Issues
- Excel files should be in `.xlsx` format (Excel 2007+)
- Older `.xls` files may need conversion

### Memory Issues
- Process large files individually rather than all at once
- Use `--only` flag to run one extractor at a time

## Development

### Adding a New Extractor

1. Create `extraction/extract_[type].py`
2. Implement `process_all_[type]_files(input_dir, output_dir)` function
3. Add to `EXTRACTORS` dict in `run_extraction.py`
4. Update this README

### Testing

Test individual extractors on sample files:

```python
from extraction.extract_form4 import process_form4_file

result = process_form4_file(
    'data/raw/insider transactions/2025/sample.xlsx',
    'data/processed/insider transactions'
)
print(result)
```

## License

Part of Richtech Robotics Equity Research project.

## Contact

For questions or issues, please create an issue in the project repository.

