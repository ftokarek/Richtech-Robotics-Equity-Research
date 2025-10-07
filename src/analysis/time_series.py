

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional


def add_quarter_info(df: pd.DataFrame) -> pd.DataFrame:
    
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['year'] = df['date'].dt.year
    df['quarter'] = df['date'].dt.quarter
    df['year_quarter'] = df['year'].astype(str) + '-Q' + df['quarter'].astype(str)
    return df


def calculate_growth_rates(df: pd.DataFrame, metrics: list) -> pd.DataFrame:
    
    df = df.copy()
    df = df.sort_values('date').reset_index(drop=True)
    
    for metric in metrics:
        if metric not in df.columns:
            continue
        
        
        df[f'{metric}_qoq'] = df[metric].pct_change() * 100
        
        
        df[f'{metric}_yoy'] = df[metric].pct_change(periods=4) * 100
    
    return df


def calculate_trailing_twelve_months(df: pd.DataFrame, metrics: list) -> pd.DataFrame:
    
    df = df.copy()
    df = df.sort_values('date').reset_index(drop=True)
    
    for metric in metrics:
        if metric not in df.columns:
            continue
        
        
        df[f'{metric}_ttm'] = df[metric].rolling(window=4, min_periods=1).sum()
    
    return df


def calculate_moving_averages(df: pd.DataFrame, metrics: list, windows: list = [2, 4]) -> pd.DataFrame:
    
    df = df.copy()
    df = df.sort_values('date').reset_index(drop=True)
    
    for metric in metrics:
        if metric not in df.columns:
            continue
        
        for window in windows:
            df[f'{metric}_ma{window}q'] = df[metric].rolling(window=window, min_periods=1).mean()
    
    return df


def create_comprehensive_timeseries(df_ratios: pd.DataFrame, output_dir: str) -> pd.DataFrame:
    
    print("\n" + "=" * 80)
    print("CREATING COMPREHENSIVE TIME SERIES")
    print("=" * 80)
    
    df = df_ratios.copy()
    
    
    df = add_quarter_info(df)
    
    print(f"\nData range: {df['year_quarter'].min()} to {df['year_quarter'].max()}")
    print(f"Total periods: {len(df)}")
    
    
    growth_metrics = [
        'revenue', 'net_income', 'gross_profit', 'operating_income',
        'operating_cf', 'free_cash_flow', 'total_assets', 'stockholders_equity'
    ]
    
    
    print("\nCalculating growth rates (YoY, QoQ)...")
    available_metrics = [m for m in growth_metrics if m in df.columns]
    df = calculate_growth_rates(df, available_metrics)
    
    
    ttm_metrics = ['revenue', 'net_income', 'operating_income', 'operating_cf']
    print("\nCalculating Trailing Twelve Months (TTM)...")
    available_ttm = [m for m in ttm_metrics if m in df.columns]
    df = calculate_trailing_twelve_months(df, available_ttm)
    
    
    ma_metrics = ['revenue', 'net_income', 'net_margin', 'roe', 'roa']
    print("\nCalculating moving averages...")
    available_ma = [m for m in ma_metrics if m in df.columns]
    df = calculate_moving_averages(df, available_ma)
    
    
    df = df.sort_values('date').reset_index(drop=True)
    
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timeseries_file = output_path / 'aggregated' / 'comprehensive_timeseries.csv'
    timeseries_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(timeseries_file, index=False)
    
    print(f"\n✓ Saved comprehensive time series to: {timeseries_file}")
    print(f"  Total columns: {len(df.columns)}")
    print(f"  Periods: {len(df)}")
    
    
    if len(df) > 0:
        print(f"\nLatest quarter ({df['year_quarter'].iloc[-1]}):")
        key_metrics = {
            'Revenue': df['revenue'].iloc[-1] if 'revenue' in df.columns else None,
            'Net Income': df['net_income'].iloc[-1] if 'net_income' in df.columns else None,
            'Net Margin': df['net_margin'].iloc[-1] if 'net_margin' in df.columns else None,
            'ROE': df['roe'].iloc[-1] if 'roe' in df.columns else None,
            'Current Ratio': df['current_ratio'].iloc[-1] if 'current_ratio' in df.columns else None,
            'Debt/Equity': df['debt_to_equity'].iloc[-1] if 'debt_to_equity' in df.columns else None
        }
        for metric, value in key_metrics.items():
            if value is not None and not pd.isna(value):
                if 'Ratio' in metric or 'Margin' in metric or metric == 'ROE':
                    print(f"  {metric}: {value:.2f}%")
                else:
                    print(f"  {metric}: ${value:,.0f}")
    
    return df


if __name__ == '__main__':
    base_dir = Path(__file__).parent.parent.parent
    metrics_dir = base_dir / 'data' / 'metrics'
    
    
    df_ratios = pd.read_csv(metrics_dir / 'quarterly' / 'financial_ratios.csv')
    
    df_timeseries = create_comprehensive_timeseries(df_ratios, str(metrics_dir))
    
    print(f"\n{'=' * 80}")
    print("TIME SERIES CREATION COMPLETE")
    print(f"{'=' * 80}\n")

