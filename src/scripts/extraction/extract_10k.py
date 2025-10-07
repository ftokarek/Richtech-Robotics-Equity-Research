

import pandas as pd
from pathlib import Path
import sys
from typing import Dict, List, Optional

sys.path.append(str(Path(__file__).parent.parent))
from utils.excel_parser import (get_filing_metadata, extract_table_from_sheet,
                                find_sheets_by_keyword, get_sheet_names)
from utils.data_cleaner import clean_financial_table


def extract_revenue_model(file_path: str) -> Optional[pd.DataFrame]:
    
    sheet_keywords = ['revenue model', 'our revenue model']
    matching_sheets = find_sheets_by_keyword(file_path, sheet_keywords)
    
    if not matching_sheets:
        return None
    
    print(f"  Extracting revenue model from: {matching_sheets[0]}")
    df = extract_table_from_sheet(file_path, matching_sheets[0], header_rows=1)
    
    if df.empty:
        return None
    
    return clean_financial_table(df)


def extract_patents(file_path: str) -> Optional[pd.DataFrame]:
    
    sheet_keywords = ['patents', 'patent']
    matching_sheets = find_sheets_by_keyword(file_path, sheet_keywords)
    
    if not matching_sheets:
        return None
    
    print(f"  Extracting patents from: {matching_sheets[0]}")
    df = extract_table_from_sheet(file_path, matching_sheets[0], header_rows=1)
    
    if df.empty:
        return None
    
    return clean_financial_table(df)


def extract_trademarks(file_path: str) -> Optional[pd.DataFrame]:
    
    sheet_keywords = ['trademarks', 'trademark']
    matching_sheets = find_sheets_by_keyword(file_path, sheet_keywords)
    
    if not matching_sheets:
        return None
    
    print(f"  Extracting trademarks from: {matching_sheets[0]}")
    df = extract_table_from_sheet(file_path, matching_sheets[0], header_rows=1)
    
    if df.empty:
        return None
    
    return clean_financial_table(df)


def extract_employees(file_path: str) -> Optional[pd.DataFrame]:
    
    sheet_keywords = ['employees', 'employee']
    matching_sheets = find_sheets_by_keyword(file_path, sheet_keywords)
    
    if not matching_sheets:
        return None
    
    print(f"  Extracting employees from: {matching_sheets[0]}")
    df = extract_table_from_sheet(file_path, matching_sheets[0], header_rows=1)
    
    if df.empty:
        return None
    
    return clean_financial_table(df)


def extract_properties(file_path: str) -> Optional[pd.DataFrame]:
    
    sheet_keywords = ['properties', 'property', 'item 2 properties']
    matching_sheets = find_sheets_by_keyword(file_path, sheet_keywords)
    
    if not matching_sheets:
        return None
    
    print(f"  Extracting properties from: {matching_sheets[0]}")
    df = extract_table_from_sheet(file_path, matching_sheets[0], header_rows=1)
    
    if df.empty:
        return None
    
    return clean_financial_table(df)


def extract_compensation(file_path: str) -> Optional[pd.DataFrame]:
    
    sheet_keywords = ['summary compensation', 'compensation', 'executive compensation']
    matching_sheets = find_sheets_by_keyword(file_path, sheet_keywords)
    
    if not matching_sheets:
        return None
    
    print(f"  Extracting compensation from: {matching_sheets[0]}")
    df = extract_table_from_sheet(file_path, matching_sheets[0], header_rows=1)
    
    if df.empty:
        return None
    
    return clean_financial_table(df)


def extract_ownership(file_path: str) -> Optional[pd.DataFrame]:
    
    sheet_keywords = ['ownership', 'security ownership', 'item 12 security ownership']
    matching_sheets = find_sheets_by_keyword(file_path, sheet_keywords)
    
    if not matching_sheets:
        return None
    
    print(f"  Extracting ownership from: {matching_sheets[0]}")
    df = extract_table_from_sheet(file_path, matching_sheets[0], header_rows=1)
    
    if df.empty:
        return None
    
    return clean_financial_table(df)


def extract_balance_sheet(file_path: str) -> Optional[pd.DataFrame]:
    
    sheet_keywords = ['balance', 'consolidated balance', 'in thousands except share']
    matching_sheets = find_sheets_by_keyword(file_path, sheet_keywords)
    
    if not matching_sheets:
        return None
    
    
    for sheet in matching_sheets:
        if 'balance' in sheet.lower() or 'assets' in sheet.lower():
            print(f"  Extracting balance sheet from: {sheet}")
            df = extract_table_from_sheet(file_path, sheet, header_rows=2)
            if not df.empty:
                return clean_financial_table(df, in_thousands=True)
    
    return None


def extract_income_statement(file_path: str) -> Optional[pd.DataFrame]:
    
    sheet_keywords = ['operations', 'income', 'statement']
    matching_sheets = find_sheets_by_keyword(file_path, sheet_keywords)
    
    if not matching_sheets:
        return None
    
    for sheet in matching_sheets:
        if 'operations' in sheet.lower() and 'cash' not in sheet.lower():
            print(f"  Extracting income statement from: {sheet}")
            df = extract_table_from_sheet(file_path, sheet, header_rows=2)
            if not df.empty:
                return clean_financial_table(df, in_thousands=True)
    
    return None


def process_10k_file(file_path: str, output_dir: str) -> Dict[str, str]:
    
    print(f"\nProcessing 10-K: {Path(file_path).name}")
    
    metadata = get_filing_metadata(file_path)
    filing_date = metadata.get('filing_date', 'unknown').replace('-', '')
    
    results = {'status': 'success', 'metadata': metadata, 'files_created': []}
    
    
    extractors = {
        'revenue_model': extract_revenue_model,
        'patents': extract_patents,
        'trademarks': extract_trademarks,
        'employees': extract_employees,
        'properties': extract_properties,
        'compensation': extract_compensation,
        'ownership': extract_ownership,
        'balance_sheet': extract_balance_sheet,
        'income_statement': extract_income_statement,
    }
    
    for name, extractor_func in extractors.items():
        try:
            df = extractor_func(file_path)
            if df is not None and not df.empty:
                output_file = f"{output_dir}/10k_{name}_{filing_date}.csv"
                df.to_csv(output_file, index=False)
                results['files_created'].append(output_file)
                print(f"  ✓ Saved {name}")
        except Exception as e:
            print(f"  ✗ Error extracting {name}: {e}")
    
    return results


def process_all_10k_files(input_dir: str, output_dir: str) -> List[Dict]:
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    
    files_10k = list(input_path.glob('**/*Annual report*.xlsx'))
    
    print(f"\nProcessing {len(files_10k)} 10-K files...")
    print("=" * 80)
    
    results = []
    for file_path in files_10k:
        try:
            result = process_10k_file(str(file_path), str(output_path))
            results.append(result)
        except Exception as e:
            print(f"  Error processing {file_path.name}: {e}")
            results.append({'status': 'error', 'file': str(file_path), 'error': str(e)})
    
    successful = sum(1 for r in results if r.get('status') == 'success')
    print(f"\n{'=' * 80}")
    print(f"10-K Processing Complete: {successful}/{len(files_10k)} successful")
    
    return results


if __name__ == '__main__':
    base_dir = Path(__file__).parent.parent.parent.parent
    input_dir = base_dir / 'data' / 'raw' / 'annual reports'
    output_dir = base_dir / 'data' / 'processed' / 'annual reports'
    
    process_all_10k_files(str(input_dir), str(output_dir))

