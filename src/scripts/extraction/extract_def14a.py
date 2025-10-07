

import pandas as pd
from pathlib import Path
import sys
from typing import Dict, List, Optional

sys.path.append(str(Path(__file__).parent.parent))
from utils.excel_parser import (get_filing_metadata, extract_table_from_sheet,
                                find_sheets_by_keyword, get_sheet_names)
from utils.data_cleaner import clean_financial_table


def extract_executive_compensation(file_path: str) -> Optional[pd.DataFrame]:
    
    sheet_keywords = ['summary compensation', 'executive compensation', 'compensation']
    matching_sheets = find_sheets_by_keyword(file_path, sheet_keywords)
    
    if not matching_sheets:
        print("  No executive compensation table found")
        return None
    
    
    for sheet in matching_sheets:
        if 'summary' in sheet.lower():
            sheet_name = sheet
            break
    else:
        sheet_name = matching_sheets[0]
    
    print(f"  Extracting executive compensation from: {sheet_name}")
    
    df = extract_table_from_sheet(file_path, sheet_name, header_rows=1)
    
    if df.empty:
        return None
    
    df = clean_financial_table(df)
    
    return df


def extract_director_compensation(file_path: str) -> Optional[pd.DataFrame]:
    
    sheet_keywords = ['director compensation', 'director']
    matching_sheets = find_sheets_by_keyword(file_path, sheet_keywords)
    
    if not matching_sheets:
        print("  No director compensation table found")
        return None
    
    sheet_name = matching_sheets[0]
    print(f"  Extracting director compensation from: {sheet_name}")
    
    df = extract_table_from_sheet(file_path, sheet_name, header_rows=1)
    
    if df.empty:
        return None
    
    df = clean_financial_table(df)
    
    return df


def extract_beneficial_ownership(file_path: str) -> Optional[pd.DataFrame]:
    
    sheet_keywords = ['beneficial ownership', 'ownership', 'security ownership']
    matching_sheets = find_sheets_by_keyword(file_path, sheet_keywords)
    
    
    matching_sheets = [s for s in matching_sheets if 'compensation' not in s.lower()]
    
    if not matching_sheets:
        print("  No beneficial ownership table found")
        return None
    
    sheet_name = matching_sheets[0]
    print(f"  Extracting beneficial ownership from: {sheet_name}")
    
    df = extract_table_from_sheet(file_path, sheet_name, header_rows=1)
    
    if df.empty:
        return None
    
    df = clean_financial_table(df)
    
    return df


def extract_audit_fees(file_path: str) -> Optional[pd.DataFrame]:
    
    sheet_keywords = ['audit fees', 'audit', 'fees']
    matching_sheets = find_sheets_by_keyword(file_path, sheet_keywords)
    
    if not matching_sheets:
        print("  No audit fees table found")
        return None
    
    sheet_name = matching_sheets[0]
    print(f"  Extracting audit fees from: {sheet_name}")
    
    df = extract_table_from_sheet(file_path, sheet_name, header_rows=1)
    
    if df.empty:
        return None
    
    df = clean_financial_table(df)
    
    return df


def extract_stock_option_grants(file_path: str) -> Optional[pd.DataFrame]:
    
    sheet_keywords = ['option grants', 'stock awards', 'option awards']
    matching_sheets = find_sheets_by_keyword(file_path, sheet_keywords)
    
    if not matching_sheets:
        return None
    
    sheet_name = matching_sheets[0]
    print(f"  Extracting stock options from: {sheet_name}")
    
    df = extract_table_from_sheet(file_path, sheet_name, header_rows=1)
    
    if df.empty:
        return None
    
    df = clean_financial_table(df)
    
    return df


def process_def14a_file(file_path: str, output_dir: str) -> Dict[str, str]:
    
    print(f"\nProcessing DEF 14A: {Path(file_path).name}")
    
    metadata = get_filing_metadata(file_path)
    filing_date = metadata.get('filing_date', 'unknown').replace('-', '')
    
    results = {'status': 'success', 'metadata': metadata, 'files_created': []}
    
    
    exec_comp_df = extract_executive_compensation(file_path)
    if exec_comp_df is not None and not exec_comp_df.empty:
        output_file = f"{output_dir}/def14a_executive_compensation_{filing_date}.csv"
        exec_comp_df.to_csv(output_file, index=False)
        results['files_created'].append(output_file)
        print(f"  ✓ Saved executive compensation")
    
    
    dir_comp_df = extract_director_compensation(file_path)
    if dir_comp_df is not None and not dir_comp_df.empty:
        output_file = f"{output_dir}/def14a_director_compensation_{filing_date}.csv"
        dir_comp_df.to_csv(output_file, index=False)
        results['files_created'].append(output_file)
        print(f"  ✓ Saved director compensation")
    
    
    ownership_df = extract_beneficial_ownership(file_path)
    if ownership_df is not None and not ownership_df.empty:
        output_file = f"{output_dir}/def14a_beneficial_ownership_{filing_date}.csv"
        ownership_df.to_csv(output_file, index=False)
        results['files_created'].append(output_file)
        print(f"  ✓ Saved beneficial ownership")
    
    
    audit_df = extract_audit_fees(file_path)
    if audit_df is not None and not audit_df.empty:
        output_file = f"{output_dir}/def14a_audit_fees_{filing_date}.csv"
        audit_df.to_csv(output_file, index=False)
        results['files_created'].append(output_file)
        print(f"  ✓ Saved audit fees")
    
    
    options_df = extract_stock_option_grants(file_path)
    if options_df is not None and not options_df.empty:
        output_file = f"{output_dir}/def14a_stock_options_{filing_date}.csv"
        options_df.to_csv(output_file, index=False)
        results['files_created'].append(output_file)
        print(f"  ✓ Saved stock options")
    
    return results


def process_all_def14a_files(input_dir: str, output_dir: str) -> List[Dict]:
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    
    files_def14a = list(input_path.glob('**/*proxy*.xlsx'))
    
    print(f"\nProcessing {len(files_def14a)} DEF 14A files...")
    print("=" * 80)
    
    results = []
    for file_path in files_def14a:
        try:
            result = process_def14a_file(str(file_path), str(output_path))
            results.append(result)
        except Exception as e:
            print(f"  Error processing {file_path.name}: {e}")
            results.append({'status': 'error', 'file': str(file_path), 'error': str(e)})
    
    successful = sum(1 for r in results if r.get('status') == 'success')
    print(f"\n{'=' * 80}")
    print(f"DEF 14A Processing Complete: {successful}/{len(files_def14a)} successful")
    
    return results


if __name__ == '__main__':
    base_dir = Path(__file__).parent.parent.parent.parent
    input_dir = base_dir / 'data' / 'raw' / 'proxies and info statements'
    output_dir = base_dir / 'data' / 'processed' / 'proxies and info statements'
    
    process_all_def14a_files(str(input_dir), str(output_dir))

