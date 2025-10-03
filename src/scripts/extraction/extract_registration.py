"""
Extract data from S-1 and 424B4 Registration Statements.

These files contain:
- Offering information
- Pre-IPO and post-IPO ownership tables
- Use of proceeds
- Financial data (similar to 10-K/10-Q)
- Risk factors (text-heavy, may skip)
"""

import pandas as pd
from pathlib import Path
import sys
from typing import Dict, List, Optional

sys.path.append(str(Path(__file__).parent.parent))
from utils.excel_parser import (get_filing_metadata, extract_table_from_sheet,
                                find_sheets_by_keyword, get_sheet_names)
from utils.data_cleaner import clean_financial_table


def extract_offering_information(file_path: str) -> Optional[pd.DataFrame]:
    """
    Extract offering details (number of shares, price, etc.).
    
    Look for sheets with: 'offering', 'prospectus'
    """
    sheet_keywords = ['offering', 'prospectus', 'shares']
    matching_sheets = find_sheets_by_keyword(file_path, sheet_keywords)
    
    if not matching_sheets:
        return None
    
    sheet_name = matching_sheets[0]
    print(f"  Extracting offering info from: {sheet_name}")
    
    df = extract_table_from_sheet(file_path, sheet_name, header_rows=1)
    
    if df.empty:
        return None
    
    return clean_financial_table(df)


def extract_preipo_ownership(file_path: str) -> Optional[pd.DataFrame]:
    """
    Extract pre-IPO private placement information.
    
    Look for sheets with: 'pre-ipo', 'preipo', 'private placement'
    """
    sheet_keywords = ['pre-ipo', 'preipo', 'private placement']
    matching_sheets = find_sheets_by_keyword(file_path, sheet_keywords)
    
    if not matching_sheets:
        print("  No pre-IPO ownership table found")
        return None
    
    sheet_name = matching_sheets[0]
    print(f"  Extracting pre-IPO ownership from: {sheet_name}")
    
    df = extract_table_from_sheet(file_path, sheet_name, header_rows=1)
    
    if df.empty:
        return None
    
    return clean_financial_table(df)


def extract_beneficial_ownership_table(file_path: str) -> Optional[pd.DataFrame]:
    """
    Extract beneficial ownership table.
    
    Look for sheets with: 'beneficial ownership', 'ownership table'
    """
    sheet_keywords = ['beneficial ownership', 'ownership table']
    matching_sheets = find_sheets_by_keyword(file_path, sheet_keywords)
    
    if not matching_sheets:
        print("  No beneficial ownership table found")
        return None
    
    sheet_name = matching_sheets[0]
    print(f"  Extracting beneficial ownership from: {sheet_name}")
    
    df = extract_table_from_sheet(file_path, sheet_name, header_rows=1)
    
    if df.empty:
        return None
    
    return clean_financial_table(df)


def extract_use_of_proceeds(file_path: str) -> Optional[pd.DataFrame]:
    """
    Extract use of proceeds information.
    
    Look for sheets with: 'proceeds', 'use of proceeds'
    """
    sheet_keywords = ['proceeds', 'use of proceeds']
    matching_sheets = find_sheets_by_keyword(file_path, sheet_keywords)
    
    if not matching_sheets:
        return None
    
    sheet_name = matching_sheets[0]
    print(f"  Extracting use of proceeds from: {sheet_name}")
    
    df = extract_table_from_sheet(file_path, sheet_name, header_rows=1)
    
    if df.empty:
        return None
    
    return clean_financial_table(df)


def extract_placement_agent_warrants(file_path: str) -> Optional[pd.DataFrame]:
    """
    Extract placement agent warrants information.
    
    Look for sheets with: 'placement agent', 'warrants'
    """
    sheet_keywords = ['placement agent warrants', 'placement agent']
    matching_sheets = find_sheets_by_keyword(file_path, sheet_keywords)
    
    if not matching_sheets:
        return None
    
    sheet_name = matching_sheets[0]
    print(f"  Extracting placement agent warrants from: {sheet_name}")
    
    df = extract_table_from_sheet(file_path, sheet_name, header_rows=1)
    
    if df.empty:
        return None
    
    return clean_financial_table(df)


def extract_risk_factors_summary(file_path: str) -> Optional[pd.DataFrame]:
    """
    Extract risk factors if in tabular form.
    
    Look for sheets with: 'risk factors', 'risk'
    """
    sheet_keywords = ['risk factors', 'risk']
    matching_sheets = find_sheets_by_keyword(file_path, sheet_keywords)
    
    if not matching_sheets:
        return None
    
    sheet_name = matching_sheets[0]
    print(f"  Extracting risk factors from: {sheet_name}")
    
    df = extract_table_from_sheet(file_path, sheet_name, header_rows=1)
    
    if df.empty or len(df.columns) < 2:
        return None
    
    return clean_financial_table(df)


def extract_financial_statements(file_path: str) -> Dict[str, pd.DataFrame]:
    """
    Extract financial statements if present in registration statement.
    
    Returns dict with balance_sheet, income_statement, etc.
    """
    results = {}
    
    # Balance sheet
    balance_keywords = ['balance sheet', 'balance']
    balance_sheets = find_sheets_by_keyword(file_path, balance_keywords)
    if balance_sheets:
        df = extract_table_from_sheet(file_path, balance_sheets[0], header_rows=2)
        if not df.empty:
            results['balance_sheet'] = clean_financial_table(df, in_thousands=True)
            print(f"  ✓ Found balance sheet")
    
    # Income statement
    income_keywords = ['income', 'operations', 'statement of operations']
    income_sheets = find_sheets_by_keyword(file_path, income_keywords)
    if income_sheets:
        for sheet in income_sheets:
            if 'cash' not in sheet.lower():
                df = extract_table_from_sheet(file_path, sheet, header_rows=2)
                if not df.empty:
                    results['income_statement'] = clean_financial_table(df, in_thousands=True)
                    print(f"  ✓ Found income statement")
                break
    
    return results


def process_registration_file(file_path: str, output_dir: str) -> Dict[str, str]:
    """
    Process a single registration statement file and save extracted data.
    
    Args:
        file_path: Path to S-1/424B4 Excel file
        output_dir: Directory to save output CSVs
        
    Returns:
        Dict with paths to output files and status
    """
    print(f"\nProcessing Registration: {Path(file_path).name}")
    
    metadata = get_filing_metadata(file_path)
    filing_date = metadata.get('filing_date', 'unknown').replace('-', '')
    form_code = metadata.get('form_code', 'reg').replace(' ', '_').replace('/', '_')
    
    results = {'status': 'success', 'metadata': metadata, 'files_created': []}
    
    # Extract offering information
    offering_df = extract_offering_information(file_path)
    if offering_df is not None and not offering_df.empty:
        output_file = f"{output_dir}/{form_code}_offering_info_{filing_date}.csv"
        offering_df.to_csv(output_file, index=False)
        results['files_created'].append(output_file)
        print(f"  ✓ Saved offering information")
    
    # Extract pre-IPO ownership
    preipo_df = extract_preipo_ownership(file_path)
    if preipo_df is not None and not preipo_df.empty:
        output_file = f"{output_dir}/{form_code}_preipo_ownership_{filing_date}.csv"
        preipo_df.to_csv(output_file, index=False)
        results['files_created'].append(output_file)
        print(f"  ✓ Saved pre-IPO ownership")
    
    # Extract beneficial ownership
    ownership_df = extract_beneficial_ownership_table(file_path)
    if ownership_df is not None and not ownership_df.empty:
        output_file = f"{output_dir}/{form_code}_beneficial_ownership_{filing_date}.csv"
        ownership_df.to_csv(output_file, index=False)
        results['files_created'].append(output_file)
        print(f"  ✓ Saved beneficial ownership")
    
    # Extract use of proceeds
    proceeds_df = extract_use_of_proceeds(file_path)
    if proceeds_df is not None and not proceeds_df.empty:
        output_file = f"{output_dir}/{form_code}_use_of_proceeds_{filing_date}.csv"
        proceeds_df.to_csv(output_file, index=False)
        results['files_created'].append(output_file)
        print(f"  ✓ Saved use of proceeds")
    
    # Extract placement agent warrants
    warrants_df = extract_placement_agent_warrants(file_path)
    if warrants_df is not None and not warrants_df.empty:
        output_file = f"{output_dir}/{form_code}_placement_warrants_{filing_date}.csv"
        warrants_df.to_csv(output_file, index=False)
        results['files_created'].append(output_file)
        print(f"  ✓ Saved placement agent warrants")
    
    # Extract financial statements
    financial_statements = extract_financial_statements(file_path)
    for stmt_type, df in financial_statements.items():
        output_file = f"{output_dir}/{form_code}_{stmt_type}_{filing_date}.csv"
        df.to_csv(output_file, index=False)
        results['files_created'].append(output_file)
        print(f"  ✓ Saved {stmt_type}")
    
    return results


def process_all_registration_files(input_dir: str, output_dir: str) -> List[Dict]:
    """
    Process all registration statement files in the input directory.
    
    Args:
        input_dir: Directory containing S-1/424B4 Excel files
        output_dir: Directory to save output CSVs
        
    Returns:
        List of processing results for each file
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all registration files (S-1, 424B4, etc.)
    files_reg = list(input_path.glob('**/*.xlsx'))
    
    print(f"\nProcessing {len(files_reg)} Registration Statement files...")
    print("=" * 80)
    
    results = []
    for file_path in files_reg:
        try:
            result = process_registration_file(str(file_path), str(output_path))
            results.append(result)
        except Exception as e:
            print(f"  Error processing {file_path.name}: {e}")
            results.append({'status': 'error', 'file': str(file_path), 'error': str(e)})
    
    successful = sum(1 for r in results if r.get('status') == 'success')
    print(f"\n{'=' * 80}")
    print(f"Registration Processing Complete: {successful}/{len(files_reg)} successful")
    
    return results


if __name__ == '__main__':
    base_dir = Path(__file__).parent.parent.parent.parent
    input_dir = base_dir / 'data' / 'raw' / 'registration statements'
    output_dir = base_dir / 'data' / 'processed' / 'registration statements'
    
    process_all_registration_files(str(input_dir), str(output_dir))

