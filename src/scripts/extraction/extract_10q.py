"""
Extract data from 10-Q Quarterly Reports.

10-Q files contain:
- Consolidated balance sheets
- Consolidated statements of operations
- Consolidated statements of cash flows
- Consolidated statements of stockholders' equity
- Notes to financial statements
"""

import pandas as pd
from pathlib import Path
import sys
from typing import Dict, List, Optional

sys.path.append(str(Path(__file__).parent.parent))
from utils.excel_parser import (get_filing_metadata, extract_table_from_sheet,
                                find_sheets_by_keyword, get_sheet_names)
from utils.data_cleaner import clean_financial_table, standardize_date


def extract_balance_sheet(file_path: str) -> Optional[pd.DataFrame]:
    """
    Extract consolidated balance sheet data.
    
    Look for sheets with keywords: 'balance', 'assets', 'liabilities'
    """
    # Try specific sheet names first (better quality)
    priority_keywords = ['part i  financial informat', 'unaudited consolidated bal', 'consolidated balance sheets']
    matching_sheets = find_sheets_by_keyword(file_path, priority_keywords)
    
    # Fallback to more generic keywords
    if not matching_sheets:
        sheet_keywords = ['balance', 'assets']
        matching_sheets = find_sheets_by_keyword(file_path, sheet_keywords)
    
    if not matching_sheets:
        print("  No balance sheet found")
        return None
    
    # Use first matching sheet
    sheet_name = matching_sheets[0]
    print(f"  Extracting balance sheet from: {sheet_name}")
    
    df = extract_table_from_sheet(file_path, sheet_name, header_rows=2)
    
    if df.empty:
        return None
    
    # Clean the data
    df = clean_financial_table(df, in_thousands=True)
    
    return df


def extract_income_statement(file_path: str) -> Optional[pd.DataFrame]:
    """
    Extract consolidated statement of operations (income statement).
    
    Look for sheets with keywords: 'operations', 'income', 'statement of operations'
    """
    sheet_keywords = ['operations', 'income', 'statement of operations', 
                     'unaudited consolidated sta', 'unaudited statements']
    matching_sheets = find_sheets_by_keyword(file_path, sheet_keywords)
    
    if not matching_sheets:
        print("  No income statement found")
        return None
    
    # Filter out cash flow and equity statements
    for sheet in matching_sheets:
        if 'cash' not in sheet.lower() and 'equity' not in sheet.lower():
            sheet_name = sheet
            break
    else:
        sheet_name = matching_sheets[0]
    
    print(f"  Extracting income statement from: {sheet_name}")
    
    df = extract_table_from_sheet(file_path, sheet_name, header_rows=2)
    
    if df.empty:
        return None
    
    df = clean_financial_table(df, in_thousands=True)
    
    return df


def extract_cash_flow(file_path: str) -> Optional[pd.DataFrame]:
    """
    Extract consolidated statement of cash flows.
    
    Look for sheets with keywords: 'cash flow', 'cash'
    """
    sheet_keywords = ['cash flow', 'cash', 'consolidated statements of cash']
    matching_sheets = find_sheets_by_keyword(file_path, sheet_keywords)
    
    if not matching_sheets:
        print("  No cash flow statement found")
        return None
    
    sheet_name = matching_sheets[0]
    print(f"  Extracting cash flow from: {sheet_name}")
    
    df = extract_table_from_sheet(file_path, sheet_name, header_rows=2)
    
    if df.empty:
        return None
    
    df = clean_financial_table(df, in_thousands=True)
    
    return df


def extract_stockholders_equity(file_path: str) -> Optional[pd.DataFrame]:
    """
    Extract consolidated statement of stockholders' equity.
    
    Look for sheets with keywords: 'equity', 'stockholders'
    """
    sheet_keywords = ['equity', 'stockholders', 'shareholders', 
                     'consolidated statements of stockholders']
    matching_sheets = find_sheets_by_keyword(file_path, sheet_keywords)
    
    if not matching_sheets:
        print("  No stockholders' equity statement found")
        return None
    
    sheet_name = matching_sheets[0]
    print(f"  Extracting stockholders' equity from: {sheet_name}")
    
    df = extract_table_from_sheet(file_path, sheet_name, header_rows=2)
    
    if df.empty:
        return None
    
    df = clean_financial_table(df, in_thousands=True)
    
    return df


def extract_revenue_breakdown(file_path: str) -> Optional[pd.DataFrame]:
    """
    Extract revenue disaggregation/breakdown from notes.
    
    Look for sheets with: 'revenue', 'disaggregation'
    """
    sheet_keywords = ['revenue', 'disaggregation', 'disaggregation of revenue']
    matching_sheets = find_sheets_by_keyword(file_path, sheet_keywords)
    
    if not matching_sheets:
        return None
    
    sheet_name = matching_sheets[0]
    print(f"  Extracting revenue breakdown from: {sheet_name}")
    
    df = extract_table_from_sheet(file_path, sheet_name, header_rows=1)
    
    if df.empty:
        return None
    
    df = clean_financial_table(df, in_thousands=True)
    
    return df


def extract_earnings_per_share(file_path: str) -> Optional[pd.DataFrame]:
    """
    Extract earnings per share details.
    
    Look for sheets with: 'earnings per share', 'eps'
    """
    sheet_keywords = ['earnings per share', 'eps', 'note 3 earnings']
    matching_sheets = find_sheets_by_keyword(file_path, sheet_keywords)
    
    if not matching_sheets:
        return None
    
    sheet_name = matching_sheets[0]
    print(f"  Extracting EPS from: {sheet_name}")
    
    df = extract_table_from_sheet(file_path, sheet_name, header_rows=1)
    
    if df.empty:
        return None
    
    df = clean_financial_table(df, in_thousands=True)
    
    return df


def process_10q_file(file_path: str, output_dir: str) -> Dict[str, str]:
    """
    Process a single 10-Q file and save extracted data.
    
    Args:
        file_path: Path to 10-Q Excel file
        output_dir: Directory to save output CSVs
        
    Returns:
        Dict with paths to output files and status
    """
    print(f"\nProcessing 10-Q: {Path(file_path).name}")
    
    metadata = get_filing_metadata(file_path)
    filing_date = metadata.get('filing_date', 'unknown').replace('-', '')
    
    results = {'status': 'success', 'metadata': metadata, 'files_created': []}
    
    # Extract balance sheet
    balance_df = extract_balance_sheet(file_path)
    if balance_df is not None and not balance_df.empty:
        output_file = f"{output_dir}/10q_balance_sheet_{filing_date}.csv"
        balance_df.to_csv(output_file, index=False)
        results['files_created'].append(output_file)
        print(f"  ✓ Saved balance sheet")
    
    # Extract income statement
    income_df = extract_income_statement(file_path)
    if income_df is not None and not income_df.empty:
        output_file = f"{output_dir}/10q_income_statement_{filing_date}.csv"
        income_df.to_csv(output_file, index=False)
        results['files_created'].append(output_file)
        print(f"  ✓ Saved income statement")
    
    # Extract cash flow
    cashflow_df = extract_cash_flow(file_path)
    if cashflow_df is not None and not cashflow_df.empty:
        output_file = f"{output_dir}/10q_cash_flow_{filing_date}.csv"
        cashflow_df.to_csv(output_file, index=False)
        results['files_created'].append(output_file)
        print(f"  ✓ Saved cash flow")
    
    # Extract stockholders' equity
    equity_df = extract_stockholders_equity(file_path)
    if equity_df is not None and not equity_df.empty:
        output_file = f"{output_dir}/10q_stockholders_equity_{filing_date}.csv"
        equity_df.to_csv(output_file, index=False)
        results['files_created'].append(output_file)
        print(f"  ✓ Saved stockholders' equity")
    
    # Extract revenue breakdown
    revenue_df = extract_revenue_breakdown(file_path)
    if revenue_df is not None and not revenue_df.empty:
        output_file = f"{output_dir}/10q_revenue_breakdown_{filing_date}.csv"
        revenue_df.to_csv(output_file, index=False)
        results['files_created'].append(output_file)
        print(f"  ✓ Saved revenue breakdown")
    
    # Extract EPS
    eps_df = extract_earnings_per_share(file_path)
    if eps_df is not None and not eps_df.empty:
        output_file = f"{output_dir}/10q_earnings_per_share_{filing_date}.csv"
        eps_df.to_csv(output_file, index=False)
        results['files_created'].append(output_file)
        print(f"  ✓ Saved EPS data")
    
    return results


def process_all_10q_files(input_dir: str, output_dir: str) -> List[Dict]:
    """
    Process all 10-Q files in the input directory.
    
    Args:
        input_dir: Directory containing 10-Q Excel files
        output_dir: Directory to save output CSVs
        
    Returns:
        List of processing results for each file
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all 10-Q files
    files_10q = list(input_path.glob('**/*quarterly reports*.xlsx'))
    
    print(f"\nProcessing {len(files_10q)} 10-Q files...")
    print("=" * 80)
    
    results = []
    for file_path in files_10q:
        try:
            result = process_10q_file(str(file_path), str(output_path))
            results.append(result)
        except Exception as e:
            print(f"  Error processing {file_path.name}: {e}")
            results.append({'status': 'error', 'file': str(file_path), 'error': str(e)})
    
    successful = sum(1 for r in results if r.get('status') == 'success')
    print(f"\n{'=' * 80}")
    print(f"10-Q Processing Complete: {successful}/{len(files_10q)} successful")
    
    return results


if __name__ == '__main__':
    base_dir = Path(__file__).parent.parent.parent.parent
    input_dir = base_dir / 'data' / 'raw' / 'quarterly reports'
    output_dir = base_dir / 'data' / 'processed' / 'quarterly reports'
    
    process_all_10q_files(str(input_dir), str(output_dir))

