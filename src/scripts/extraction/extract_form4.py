

import pandas as pd
from pathlib import Path
import sys
from typing import Dict, List, Optional


sys.path.append(str(Path(__file__).parent.parent))
from utils.excel_parser import (get_filing_metadata, extract_table_from_sheet, 
                                get_sheet_names, read_excel_with_merged_cells)
from utils.data_cleaner import (clean_numeric_column, standardize_date, 
                               clean_financial_table, clean_whitespace)


def extract_reporting_person(file_path: str, sheet_name: str) -> Dict[str, str]:
    
    df = read_excel_with_merged_cells(file_path, sheet_name)
    
    person_info = {}
    
    
    for idx, row in df.iterrows():
        row_str = ' '.join([str(val) for val in row if pd.notna(val)])
        
        
        if 'Name and Address of Reporting Person' in row_str or idx == 0:
            
            for val in row:
                if pd.notna(val) and isinstance(val, str) and len(str(val)) > 3:
                    if 'Name and Address' not in str(val):
                        person_info['name'] = str(val).strip()
                        break
        
        
        if 'Relationship of Reporting Person' in row_str or 'Director' in row_str or 'Officer' in row_str:
            
            if 'Director' in row_str:
                person_info['is_director'] = 'X' in row_str or '☑' in row_str
            if 'Officer' in row_str:
                person_info['is_officer'] = 'X' in row_str or '☑' in row_str
            if '10% Owner' in row_str:
                person_info['is_10pct_owner'] = 'X' in row_str or '☑' in row_str
            
            
            for val in row:
                if pd.notna(val) and isinstance(val, str):
                    if any(title in str(val) for title in ['President', 'CEO', 'CFO', 'Director', 'Officer']):
                        person_info['title'] = str(val).strip()
    
    return person_info


def extract_nonderivative_transactions(file_path: str, sheet_name: str) -> pd.DataFrame:
    
    df = extract_table_from_sheet(file_path, sheet_name, header_rows=2)
    
    if df.empty:
        return pd.DataFrame()
    
    
    df = clean_whitespace(df)
    
    
    column_mapping = {
        'title of security': 'security_title',
        '1. title of security': 'security_title',
        'transaction date': 'transaction_date',
        '2. transaction date': 'transaction_date',
        'transaction code': 'transaction_code',
        '3. transaction code': 'transaction_code',
        'code': 'transaction_code',
        'amount': 'amount',
        'shares': 'shares',
        'price': 'price',
        'price per share': 'price_per_share',
        'securities acquired': 'securities_acquired',
        'securities disposed': 'securities_disposed',
        'amount of securities beneficially owned': 'securities_owned_after',
        '5. amount of securities beneficially owned': 'securities_owned_after',
        'ownership form': 'ownership_form',
        '6. ownership form': 'ownership_form'
    }
    
    
    for old_name, new_name in column_mapping.items():
        for col in df.columns:
            if old_name in str(col).lower():
                df.rename(columns={col: new_name}, inplace=True)
                break
    
    
    numeric_cols = ['amount', 'shares', 'price', 'price_per_share', 
                   'securities_acquired', 'securities_disposed', 'securities_owned_after']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = clean_numeric_column(df[col])
    
    
    if 'transaction_date' in df.columns:
        df['transaction_date'] = df['transaction_date'].apply(standardize_date)
    
    
    df = df.dropna(how='all')
    
    return df


def extract_derivative_transactions(file_path: str, sheet_name: str) -> pd.DataFrame:
    
    df = extract_table_from_sheet(file_path, sheet_name, header_rows=2)
    
    if df.empty:
        return pd.DataFrame()
    
    
    df = clean_whitespace(df)
    
    
    column_mapping = {
        'title of derivative security': 'derivative_title',
        '1. title of derivative security': 'derivative_title',
        'conversion or exercise price': 'exercise_price',
        '2. conversion or exercise price': 'exercise_price',
        'transaction date': 'transaction_date',
        '3. transaction date': 'transaction_date',
        'transaction code': 'transaction_code',
        '4. transaction code': 'transaction_code',
        'number of derivative securities': 'number_of_securities',
        'date exercisable': 'date_exercisable',
        'expiration date': 'expiration_date',
        'title and amount of securities underlying': 'underlying_securities',
        'price of derivative security': 'derivative_price'
    }
    
    for old_name, new_name in column_mapping.items():
        for col in df.columns:
            if old_name in str(col).lower():
                df.rename(columns={col: new_name}, inplace=True)
                break
    
    
    numeric_cols = ['exercise_price', 'number_of_securities', 'derivative_price']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = clean_numeric_column(df[col])
    
    
    date_cols = ['transaction_date', 'date_exercisable', 'expiration_date']
    for col in date_cols:
        if col in df.columns:
            df[col] = df[col].apply(standardize_date)
    
    df = df.dropna(how='all')
    
    return df


def process_form4_file(file_path: str, output_dir: str) -> Dict[str, str]:
    
    print(f"Processing Form 4: {Path(file_path).name}")
    
    metadata = get_filing_metadata(file_path)
    sheet_names = get_sheet_names(file_path)
    
    if len(sheet_names) < 2:
        print(f"  Warning: Expected 3 sheets, found {len(sheet_names)}")
        return {'status': 'error', 'message': 'Insufficient sheets'}
    
    results = {'status': 'success', 'metadata': metadata}
    
    
    person_info = extract_reporting_person(file_path, sheet_names[0])
    results['person_info'] = person_info
    
    
    nonderivative_df = extract_nonderivative_transactions(file_path, sheet_names[1])
    
    
    for key, value in metadata.items():
        nonderivative_df[key] = value
    for key, value in person_info.items():
        nonderivative_df[f'person_{key}'] = value
    
    
    if not nonderivative_df.empty:
        filing_date = metadata.get('filing_date', 'unknown').replace('-', '')
        person_name = person_info.get('name', 'unknown').replace(' ', '_').replace('.', '')
        output_file = f"{output_dir}/form4_nonderivative_{filing_date}_{person_name}.csv"
        nonderivative_df.to_csv(output_file, index=False)
        results['nonderivative_file'] = output_file
        print(f"  Saved non-derivative transactions: {output_file}")
    
    
    if len(sheet_names) >= 3:
        derivative_df = extract_derivative_transactions(file_path, sheet_names[2])
        
        
        for key, value in metadata.items():
            derivative_df[key] = value
        for key, value in person_info.items():
            derivative_df[f'person_{key}'] = value
        
        if not derivative_df.empty:
            output_file = f"{output_dir}/form4_derivative_{filing_date}_{person_name}.csv"
            derivative_df.to_csv(output_file, index=False)
            results['derivative_file'] = output_file
            print(f"  Saved derivative transactions: {output_file}")
    
    return results


def process_all_form4_files(input_dir: str, output_dir: str) -> List[Dict]:
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    
    form4_files = list(input_path.glob('**/*Statement of changes in beneficial ownership*.xlsx'))
    
    print(f"\nProcessing {len(form4_files)} Form 4 files...")
    print("=" * 80)
    
    results = []
    for file_path in form4_files:
        try:
            result = process_form4_file(str(file_path), str(output_path))
            results.append(result)
        except Exception as e:
            print(f"  Error processing {file_path.name}: {e}")
            results.append({'status': 'error', 'file': str(file_path), 'error': str(e)})
    
    
    successful = sum(1 for r in results if r.get('status') == 'success')
    print(f"\n{'=' * 80}")
    print(f"Form 4 Processing Complete: {successful}/{len(form4_files)} successful")
    
    return results


if __name__ == '__main__':
    
    base_dir = Path(__file__).parent.parent.parent.parent
    input_dir = base_dir / 'data' / 'raw' / 'insider transactions'
    output_dir = base_dir / 'data' / 'processed' / 'insider transactions'
    
    process_all_form4_files(str(input_dir), str(output_dir))

