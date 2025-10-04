"""
Extract and process market data from ChartData.xlsx.
Converts OHLCV data to clean CSV format.
"""

import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent))
from utils.data_cleaner import standardize_date, clean_numeric_column


def process_market_data(input_file: str, output_dir: str) -> dict:
    """
    Process market data from Excel to CSV.
    
    Args:
        input_file: Path to ChartData.xlsx
        output_dir: Directory to save processed CSV
        
    Returns:
        Dict with processing status and output file path
    """
    print(f"Processing market data: {input_file}")
    
    # Read the Excel file
    df = pd.read_excel(input_file, sheet_name=0)
    
    # Rename columns to standard names
    df.columns = df.columns.str.lower().str.replace('/', '_').str.replace(' ', '_')
    
    # Standardize column names
    column_mapping = {
        'close_price': 'close',
        'date': 'date'
    }
    df.rename(columns=column_mapping, inplace=True)
    
    # Convert date to standard format
    df['date'] = pd.to_datetime(df['date'])
    df['date_str'] = df['date'].dt.strftime('%Y-%m-%d')
    
    # Clean numeric columns
    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = clean_numeric_column(df[col])
    
    # Sort by date ascending
    df = df.sort_values('date').reset_index(drop=True)
    
    # Calculate additional metrics
    df['daily_return'] = df['close'].pct_change()
    df['daily_volatility'] = df['daily_return'].rolling(window=20).std()
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()
    
    # Calculate volume moving average
    df['volume_ma_20'] = df['volume'].rolling(window=20).mean()
    
    # Save to CSV
    output_file = Path(output_dir) / 'stock_prices_daily.csv'
    df.to_csv(output_file, index=False)
    
    print(f"  ✓ Saved to: {output_file}")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"  Total days: {len(df)}")
    print(f"  Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
    
    # Create monthly aggregated data
    df_monthly = df.copy()
    df_monthly['year_month'] = df_monthly['date'].dt.to_period('M')
    
    monthly_agg = df_monthly.groupby('year_month').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum',
        'daily_return': 'sum'
    }).reset_index()
    
    monthly_agg['year_month'] = monthly_agg['year_month'].astype(str)
    monthly_agg.rename(columns={'daily_return': 'monthly_return'}, inplace=True)
    
    output_file_monthly = Path(output_dir) / 'stock_prices_monthly.csv'
    monthly_agg.to_csv(output_file_monthly, index=False)
    
    print(f"  ✓ Saved monthly data to: {output_file_monthly}")
    
    return {
        'status': 'success',
        'daily_file': str(output_file),
        'monthly_file': str(output_file_monthly),
        'records': len(df),
        'date_range': (str(df['date'].min()), str(df['date'].max()))
    }


if __name__ == '__main__':
    base_dir = Path(__file__).parent.parent.parent
    input_file = base_dir / 'data' / 'raw' / 'market_data' / 'ChartData.xlsx'
    output_dir = base_dir / 'data' / 'processed' / 'market_data'
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    result = process_market_data(str(input_file), str(output_dir))
    print(f"\n✓ Market data processing complete")

