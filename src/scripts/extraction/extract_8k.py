"""
Extract data from 8-K Current Reports.

8-K files report material events and vary widely in structure.
Focus on extracting:
- Metadata (filing date, items reported)
- Embedded tables (payment schedules, pricing terms, etc.)
- Signature information
"""

import pandas as pd
from pathlib import Path
import sys
from typing import Dict, List, Optional
import re

sys.path.append(str(Path(__file__).parent.parent))
from utils.excel_parser import (get_filing_metadata, extract_table_from_sheet,
                                get_sheet_names, read_excel_with_merged_cells)
from utils.data_cleaner import clean_financial_table, clean_whitespace


def extract_8k_metadata(file_path: str) -> Dict[str, any]:
    """
    Extract metadata from 8-K filing.
    
    Returns:
        Dict with filing info including items reported
    """
    metadata = get_filing_metadata(file_path)
    sheet_names = get_sheet_names(file_path)
    
    metadata['sheet_count'] = len(sheet_names)
    metadata['sheet_names'] = sheet_names
    
    # Try to detect items reported from sheet names or content
    items_reported = []
    
    # Common 8-K item patterns
    item_patterns = [
        r'item\s+(\d+\.\d+)',
        r'item\s+(\d+)',
    ]
    
    # Check sheet names and first sheet content
    for sheet_name in sheet_names:
        for pattern in item_patterns:
            matches = re.findall(pattern, sheet_name.lower())
            items_reported.extend(matches)
    
    if items_reported:
        metadata['items_reported'] = list(set(items_reported))
    
    return metadata


def extract_tables_from_8k(file_path: str) -> List[Dict]:
    """
    Extract all tables from 8-K filing.
    
    Returns:
        List of dicts with sheet_name and dataframe
    """
    sheet_names = get_sheet_names(file_path)
    extracted_tables = []
    
    for sheet_name in sheet_names:
        # Skip sheets that are typically just signatures
        if 'signature' in sheet_name.lower() and len(sheet_names) > 1:
            continue
        
        try:
            df = extract_table_from_sheet(file_path, sheet_name, header_rows=1)
            
            # Only keep if there's meaningful data
            if not df.empty and len(df) > 2 and len(df.columns) > 1:
                # Check if it looks like a table (has some numeric data)
                numeric_count = sum(df.map(lambda x: isinstance(x, (int, float))).sum())
                
                if numeric_count > 3:  # At least some numeric values
                    df = clean_financial_table(df)
                    extracted_tables.append({
                        'sheet_name': sheet_name,
                        'data': df
                    })
        except Exception as e:
            print(f"    Warning: Could not extract table from {sheet_name}: {e}")
            continue
    
    return extracted_tables


def extract_payment_schedule(file_path: str) -> Optional[pd.DataFrame]:
    """
    Look for payment schedules (common in 8-K filings about debt).
    
    Look for sheets with payment/installment information.
    """
    sheet_names = get_sheet_names(file_path)
    
    for sheet_name in sheet_names:
        sheet_lower = sheet_name.lower()
        if any(keyword in sheet_lower for keyword in ['installment', 'payment', 'schedule', 'principal']):
            print(f"  Found payment schedule: {sheet_name}")
            df = extract_table_from_sheet(file_path, sheet_name, header_rows=1)
            
            if not df.empty:
                return clean_financial_table(df)
    
    return None


def extract_signature_info(file_path: str) -> Optional[pd.DataFrame]:
    """
    Extract signature information from 8-K.
    """
    sheet_keywords = ['signature', 'signatures']
    sheet_names = get_sheet_names(file_path)
    
    for sheet_name in sheet_names:
        if any(keyword in sheet_name.lower() for keyword in sheet_keywords):
            df = read_excel_with_merged_cells(file_path, sheet_name)
            
            if not df.empty:
                df = clean_whitespace(df)
                return df
    
    return None


def extract_exhibit_info(file_path: str) -> List[Dict]:
    """
    Extract information about exhibits listed in 8-K.
    """
    sheet_names = get_sheet_names(file_path)
    exhibits = []
    
    for sheet_name in sheet_names:
        if 'exhibit' in sheet_name.lower():
            try:
                df = extract_table_from_sheet(file_path, sheet_name, header_rows=1)
                if not df.empty:
                    exhibits.append({
                        'exhibit_name': sheet_name,
                        'data': clean_financial_table(df)
                    })
            except:
                continue
    
    return exhibits


def process_8k_file(file_path: str, output_dir: str) -> Dict[str, str]:
    """
    Process a single 8-K file and save extracted data.
    
    Args:
        file_path: Path to 8-K Excel file
        output_dir: Directory to save output CSVs
        
    Returns:
        Dict with paths to output files and status
    """
    print(f"\nProcessing 8-K: {Path(file_path).name}")
    
    metadata = extract_8k_metadata(file_path)
    filing_date = metadata.get('filing_date', 'unknown').replace('-', '')
    
    results = {'status': 'success', 'metadata': metadata, 'files_created': []}
    
    # Save metadata
    metadata_df = pd.DataFrame([metadata])
    output_file = f"{output_dir}/8k_metadata_{filing_date}.csv"
    metadata_df.to_csv(output_file, index=False)
    results['files_created'].append(output_file)
    print(f"  ✓ Saved metadata")
    
    # Extract payment schedule if exists
    payment_df = extract_payment_schedule(file_path)
    if payment_df is not None and not payment_df.empty:
        output_file = f"{output_dir}/8k_payment_schedule_{filing_date}.csv"
        payment_df.to_csv(output_file, index=False)
        results['files_created'].append(output_file)
        print(f"  ✓ Saved payment schedule")
    
    # Extract all tables
    tables = extract_tables_from_8k(file_path)
    for i, table_info in enumerate(tables):
        sheet_name = table_info['sheet_name'].replace(' ', '_').replace('/', '_')[:50]
        output_file = f"{output_dir}/8k_table_{filing_date}_{sheet_name}.csv"
        table_info['data'].to_csv(output_file, index=False)
        results['files_created'].append(output_file)
        print(f"  ✓ Saved table from: {table_info['sheet_name']}")
    
    # Extract exhibits
    exhibits = extract_exhibit_info(file_path)
    for i, exhibit_info in enumerate(exhibits):
        exhibit_name = exhibit_info['exhibit_name'].replace(' ', '_')[:50]
        output_file = f"{output_dir}/8k_exhibit_{filing_date}_{exhibit_name}.csv"
        exhibit_info['data'].to_csv(output_file, index=False)
        results['files_created'].append(output_file)
        print(f"  ✓ Saved exhibit: {exhibit_info['exhibit_name']}")
    
    return results


def process_all_8k_files(input_dir: str, output_dir: str) -> List[Dict]:
    """
    Process all 8-K files in the input directory.
    
    Args:
        input_dir: Directory containing 8-K Excel files
        output_dir: Directory to save output CSVs
        
    Returns:
        List of processing results for each file
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all 8-K files
    files_8k = list(input_path.glob('**/*Current report*.xlsx'))
    
    print(f"\nProcessing {len(files_8k)} 8-K files...")
    print("=" * 80)
    
    results = []
    for file_path in files_8k:
        try:
            result = process_8k_file(str(file_path), str(output_path))
            results.append(result)
        except Exception as e:
            print(f"  Error processing {file_path.name}: {e}")
            results.append({'status': 'error', 'file': str(file_path), 'error': str(e)})
    
    successful = sum(1 for r in results if r.get('status') == 'success')
    print(f"\n{'=' * 80}")
    print(f"8-K Processing Complete: {successful}/{len(files_8k)} successful")
    
    return results


if __name__ == '__main__':
    base_dir = Path(__file__).parent.parent.parent.parent
    input_dir = base_dir / 'data' / 'raw' / '8-k related'
    output_dir = base_dir / 'data' / 'processed' / '8-k related'
    
    process_all_8k_files(str(input_dir), str(output_dir))

