

import pandas as pd
import numpy as np
from pathlib import Path
import re
from typing import Dict, List, Optional
import sys

sys.path.append(str(Path(__file__).parent.parent / 'scripts'))
from utils.data_cleaner import clean_numeric_column


def extract_date_from_filename(filename: str) -> Optional[str]:
    
    match = re.search(r'(\d{8})', filename)
    if match:
        date_str = match.group(1)
        
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    return None


def find_value_in_df(df: pd.DataFrame, keywords: List[str]) -> Optional[float]:
    
    for keyword in keywords:
        
        for idx, row in df.iterrows():
            first_col_val = str(row.iloc[0]).lower() if pd.notna(row.iloc[0]) else ''
            
            
            
            
            apostrophes = [chr(8217), chr(8216), chr(8220), chr(8221), "'", '"']
            for apos in apostrophes:
                first_col_val = first_col_val.replace(apos, '')
            
            search_keyword = keyword.lower()
            for apos in apostrophes:
                search_keyword = search_keyword.replace(apos, '')
            
            if search_keyword in first_col_val:
                
                for col in reversed(df.columns[1:]):  
                    val = row[col]
                    if pd.notna(val):
                        try:
                            
                            numeric_val = float(val)
                            
                            if 2000 <= numeric_val <= 2100:
                                continue
                            return numeric_val
                        except (ValueError, TypeError):
                            continue
    return None


def parse_balance_sheet(file_path: str) -> Dict:
    
    df = pd.read_csv(file_path)
    
    metrics = {
        'date': extract_date_from_filename(file_path),
        'source_file': Path(file_path).name
    }
    
    
    search_terms = {
        'total_assets': ['total assets'],
        'current_assets': ['total current assets', 'current assets'],
        'total_liabilities': ['total liabilities'],
        'current_liabilities': ['total current liabilities', 'current liabilities'],
        'stockholders_equity': ["total stockholders' equity", "total controlling stockholders' equity", 
                               'total stockholders equity', 'stockholders equity', 'shareholders equity', 'total equity'],
        'cash': ['cash and cash equivalents', 'cash'],
        'inventory': ['inventory', 'inventories'],
        'accounts_receivable': ['accounts receivable', 'trade receivables']
    }
    
    for metric_name, keywords in search_terms.items():
        value = find_value_in_df(df, keywords)
        metrics[metric_name] = value
    
    return metrics


def parse_income_statement(file_path: str) -> Dict:
    
    df = pd.read_csv(file_path)
    
    metrics = {
        'date': extract_date_from_filename(file_path),
        'source_file': Path(file_path).name
    }
    
    search_terms = {
        'revenue': ['revenue, net', 'revenue', 'total revenue', 'net revenue', 'sales'],
        'cogs': ['cost of revenue, net', 'cost of revenue', 'cost of goods sold', 'cost of sales', 'cogs'],
        'gross_profit': ['gross profit', 'gross income'],
        'operating_expenses': ['total operating expenses', 'operating expenses'],
        'operating_income': ['loss from operations', 'income from operations', 'operating income', 'operating profit'],
        'interest_expense': ['interest expense, net', 'interest expense', 'interest cost'],
        'net_income': ['net loss attributable to common stockholders', 'consolidated net loss', 'net loss attributable to the company', 'net income', 'net loss', 'net profit'],
        'ebit': ['loss before income tax expense', 'loss before income tax', 'income before income taxes', 'earnings before tax'],
        'eps_basic': ['basic and diluted net loss per share', 'basic earnings per share', 'basic eps'],
        'eps_diluted': ['basic and diluted net loss per share', 'diluted earnings per share', 'diluted eps'],
        'depreciation': ['depreciation and amortization']
    }
    
    for metric_name, keywords in search_terms.items():
        value = find_value_in_df(df, keywords)
        metrics[metric_name] = value
    
    
    if metrics.get('gross_profit') is None and metrics.get('revenue') and metrics.get('cogs'):
        metrics['gross_profit'] = metrics['revenue'] - abs(metrics['cogs'])
    
    return metrics


def parse_cash_flow(file_path: str) -> Dict:
    
    df = pd.read_csv(file_path)
    
    metrics = {
        'date': extract_date_from_filename(file_path),
        'source_file': Path(file_path).name
    }
    
    search_terms = {
        'operating_cf': ['net cash provided by operating activities', 'net cash used in operating activities', 
                        'cash from operations', 'operating cash flow'],
        'investing_cf': ['net cash used in investing activities', 'net cash provided by investing activities',
                        'cash from investing', 'investing cash flow'],
        'financing_cf': ['net cash provided by financing activities', 'net cash used in financing activities',
                        'cash from financing', 'financing cash flow'],
        'capex': ['purchase of equipment', 'capital expenditures', 'purchase of property', 
                 'purchases of property and equipment', 'capex', 'purchases of equipment'],
        'depreciation': ['depreciation and amortization', 'depreciation']
    }
    
    for metric_name, keywords in search_terms.items():
        value = find_value_in_df(df, keywords)
        metrics[metric_name] = value
    
    
    if metrics.get('operating_cf') and metrics.get('capex'):
        metrics['free_cash_flow'] = metrics['operating_cf'] - abs(metrics.get('capex', 0))
    elif metrics.get('operating_cf'):
        metrics['free_cash_flow'] = metrics['operating_cf']
    
    return metrics


def parse_revenue_breakdown(file_path: str) -> Dict:
    
    df = pd.read_csv(file_path)
    
    metrics = {
        'date': extract_date_from_filename(file_path),
        'source_file': Path(file_path).name
    }
    
    
    search_terms = {
        'product_revenue': ['product', 'products', 'product sale'],
        'service_revenue': ['service', 'services', 'service revenue']
    }
    
    for metric_name, keywords in search_terms.items():
        value = find_value_in_df(df, keywords)
        metrics[metric_name] = value
    
    return metrics


def extract_all_metrics(processed_dir: str, output_dir: str) -> Dict[str, pd.DataFrame]:
    
    processed_path = Path(processed_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("EXTRACTING FINANCIAL METRICS")
    print("=" * 80)
    
    
    balance_sheets = []
    income_statements = []
    cash_flows = []
    revenue_breakdowns = []
    
    
    quarterly_dir = processed_path / 'quarterly reports'
    if quarterly_dir.exists():
        print(f"\nProcessing quarterly reports from: {quarterly_dir}")
        
        for file in quarterly_dir.glob('10q_balance_sheet_*.csv'):
            print(f"  Processing: {file.name}")
            metrics = parse_balance_sheet(str(file))
            balance_sheets.append(metrics)
        
        for file in quarterly_dir.glob('10q_income_statement_*.csv'):
            print(f"  Processing: {file.name}")
            metrics = parse_income_statement(str(file))
            income_statements.append(metrics)
        
        for file in quarterly_dir.glob('10q_cash_flow_*.csv'):
            print(f"  Processing: {file.name}")
            metrics = parse_cash_flow(str(file))
            cash_flows.append(metrics)
        
        for file in quarterly_dir.glob('10q_revenue_breakdown_*.csv'):
            print(f"  Processing: {file.name}")
            metrics = parse_revenue_breakdown(str(file))
            revenue_breakdowns.append(metrics)
    
    
    annual_dir = processed_path / 'annual reports'
    if annual_dir.exists():
        print(f"\nProcessing annual reports from: {annual_dir}")
        
        for file in annual_dir.glob('10k_balance_sheet_*.csv'):
            print(f"  Processing: {file.name}")
            metrics = parse_balance_sheet(str(file))
            balance_sheets.append(metrics)
        
        for file in annual_dir.glob('10k_income_statement_*.csv'):
            print(f"  Processing: {file.name}")
            metrics = parse_income_statement(str(file))
            income_statements.append(metrics)
    
    
    df_balance = pd.DataFrame(balance_sheets).sort_values('date').reset_index(drop=True)
    df_income = pd.DataFrame(income_statements).sort_values('date').reset_index(drop=True)
    df_cashflow = pd.DataFrame(cash_flows).sort_values('date').reset_index(drop=True)
    
    
    print(f"\n{'=' * 80}")
    print("SAVING EXTRACTED METRICS")
    print(f"{'=' * 80}")
    
    balance_file = output_path / 'quarterly' / 'balance_sheet_metrics.csv'
    balance_file.parent.mkdir(parents=True, exist_ok=True)
    df_balance.to_csv(balance_file, index=False)
    print(f"✓ Saved balance sheet metrics: {balance_file}")
    print(f"  Records: {len(df_balance)}")
    
    income_file = output_path / 'quarterly' / 'income_statement_metrics.csv'
    df_income.to_csv(income_file, index=False)
    print(f"✓ Saved income statement metrics: {income_file}")
    print(f"  Records: {len(df_income)}")
    
    cashflow_file = output_path / 'quarterly' / 'cash_flow_metrics.csv'
    df_cashflow.to_csv(cashflow_file, index=False)
    print(f"✓ Saved cash flow metrics: {cashflow_file}")
    print(f"  Records: {len(df_cashflow)}")
    
    return {
        'balance_sheet': df_balance,
        'income_statement': df_income,
        'cash_flow': df_cashflow
    }


if __name__ == '__main__':
    base_dir = Path(__file__).parent.parent.parent
    processed_dir = base_dir / 'data' / 'processed'
    output_dir = base_dir / 'data' / 'metrics'
    
    metrics = extract_all_metrics(str(processed_dir), str(output_dir))
    
    print(f"\n{'=' * 80}")
    print("EXTRACTION COMPLETE")
    print(f"{'=' * 80}\n")

