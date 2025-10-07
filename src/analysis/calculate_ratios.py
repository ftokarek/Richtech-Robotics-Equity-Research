

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict


def calculate_profitability_ratios(df_combined: pd.DataFrame) -> pd.DataFrame:
    
    df = df_combined.copy()
    
    
    if 'revenue' in df.columns and 'cogs' in df.columns:
        df['gross_margin'] = ((df['revenue'] - abs(df['cogs'])) / df['revenue']) * 100
    elif 'gross_profit' in df.columns and 'revenue' in df.columns:
        df['gross_margin'] = (df['gross_profit'] / df['revenue']) * 100
    
    
    if 'operating_income' in df.columns and 'revenue' in df.columns:
        df['operating_margin'] = (df['operating_income'] / df['revenue']) * 100
    
    
    if 'net_income' in df.columns and 'revenue' in df.columns:
        df['net_margin'] = (df['net_income'] / df['revenue']) * 100
    
    
    if 'operating_income' in df.columns:
        if 'depreciation' in df.columns:
            df['ebitda'] = df['operating_income'] + df['depreciation']
        else:
            
            df['ebitda'] = df['operating_income']
    
    
    if 'ebitda' in df.columns and 'revenue' in df.columns:
        df['ebitda_margin'] = (df['ebitda'] / df['revenue']) * 100
    
    return df


def calculate_return_ratios(df_combined: pd.DataFrame) -> pd.DataFrame:
    
    df = df_combined.copy()
    
    
    if 'net_income' in df.columns and 'stockholders_equity' in df.columns:
        df['roe'] = (df['net_income'] / df['stockholders_equity']) * 100
    
    
    if 'net_income' in df.columns and 'total_assets' in df.columns:
        df['roa'] = (df['net_income'] / df['total_assets']) * 100
    
    
    
    if 'operating_income' in df.columns and 'stockholders_equity' in df.columns:
        
        nopat = df['operating_income'] * 0.79
        invested_capital = df['stockholders_equity']
        if 'total_liabilities' in df.columns:
            invested_capital = df['stockholders_equity'] + df['total_liabilities']
        df['roic'] = (nopat / invested_capital) * 100
    
    return df


def calculate_liquidity_ratios(df_combined: pd.DataFrame) -> pd.DataFrame:
    
    df = df_combined.copy()
    
    
    if 'current_assets' in df.columns and 'current_liabilities' in df.columns:
        df['current_ratio'] = df['current_assets'] / df['current_liabilities']
    
    
    if 'current_assets' in df.columns and 'current_liabilities' in df.columns:
        inventory = df.get('inventory', 0)
        df['quick_ratio'] = (df['current_assets'] - inventory) / df['current_liabilities']
    
    
    if 'cash' in df.columns and 'current_liabilities' in df.columns:
        df['cash_ratio'] = df['cash'] / df['current_liabilities']
    
    return df


def calculate_leverage_ratios(df_combined: pd.DataFrame) -> pd.DataFrame:
    
    df = df_combined.copy()
    
    
    if 'total_liabilities' in df.columns and 'stockholders_equity' in df.columns:
        df['debt_to_equity'] = df['total_liabilities'] / df['stockholders_equity']
    
    
    if 'total_liabilities' in df.columns and 'total_assets' in df.columns:
        df['debt_to_assets'] = df['total_liabilities'] / df['total_assets']
    
    
    if 'ebit' in df.columns and 'interest_expense' in df.columns:
        
        df['interest_coverage'] = np.where(
            df['interest_expense'] > 0,
            df['ebit'] / df['interest_expense'],
            np.nan
        )
    
    return df


def calculate_efficiency_ratios(df_combined: pd.DataFrame) -> pd.DataFrame:
    
    df = df_combined.copy()
    
    
    if 'revenue' in df.columns and 'total_assets' in df.columns:
        df['asset_turnover'] = df['revenue'] / df['total_assets']
    
    
    if 'cogs' in df.columns and 'inventory' in df.columns:
        df['inventory_turnover'] = abs(df['cogs']) / df['inventory']
    
    return df


def calculate_all_ratios(metrics_dict: Dict[str, pd.DataFrame], output_dir: str) -> pd.DataFrame:
    
    print("\n" + "=" * 80)
    print("CALCULATING FINANCIAL RATIOS")
    print("=" * 80)
    
    
    df_balance = metrics_dict['balance_sheet']
    df_income = metrics_dict['income_statement']
    df_cashflow = metrics_dict['cash_flow']
    
    
    df_combined = pd.merge(df_balance, df_income, on='date', how='outer', suffixes=('_bs', '_is'))
    
    
    df_combined = pd.merge(df_combined, df_cashflow, on='date', how='outer')
    
    
    df_combined = df_combined.sort_values('date').reset_index(drop=True)
    
    print(f"\nMerged data shape: {df_combined.shape}")
    print(f"Date range: {df_combined['date'].min()} to {df_combined['date'].max()}")
    
    
    print("\nCalculating profitability ratios...")
    df_combined = calculate_profitability_ratios(df_combined)
    
    print("Calculating return ratios...")
    df_combined = calculate_return_ratios(df_combined)
    
    print("Calculating liquidity ratios...")
    df_combined = calculate_liquidity_ratios(df_combined)
    
    print("Calculating leverage ratios...")
    df_combined = calculate_leverage_ratios(df_combined)
    
    print("Calculating efficiency ratios...")
    df_combined = calculate_efficiency_ratios(df_combined)
    
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    ratios_file = output_path / 'quarterly' / 'financial_ratios.csv'
    ratios_file.parent.mkdir(parents=True, exist_ok=True)
    df_combined.to_csv(ratios_file, index=False)
    
    print(f"\n✓ Saved financial ratios to: {ratios_file}")
    print(f"  Total metrics/ratios: {len(df_combined.columns)}")
    print(f"  Periods: {len(df_combined)}")
    
    
    ratio_columns = [col for col in df_combined.columns if any(
        keyword in col.lower() for keyword in 
        ['margin', 'ratio', 'roe', 'roa', 'roic', 'turnover', 'coverage', 'ebitda']
    )]
    
    print(f"\nCalculated ratios ({len(ratio_columns)}):")
    for col in ratio_columns:
        non_null = df_combined[col].notna().sum()
        print(f"  - {col}: {non_null}/{len(df_combined)} periods")
    
    return df_combined


if __name__ == '__main__':
    base_dir = Path(__file__).parent.parent.parent
    metrics_dir = base_dir / 'data' / 'metrics'
    
    
    metrics_dict = {
        'balance_sheet': pd.read_csv(metrics_dir / 'quarterly' / 'balance_sheet_metrics.csv'),
        'income_statement': pd.read_csv(metrics_dir / 'quarterly' / 'income_statement_metrics.csv'),
        'cash_flow': pd.read_csv(metrics_dir / 'quarterly' / 'cash_flow_metrics.csv')
    }
    
    df_ratios = calculate_all_ratios(metrics_dict, str(metrics_dir))
    
    print(f"\n{'=' * 80}")
    print("RATIO CALCULATION COMPLETE")
    print(f"{'=' * 80}\n")

