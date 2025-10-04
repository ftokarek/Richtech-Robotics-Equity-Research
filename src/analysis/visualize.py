"""
Visualization module for financial analysis.
Creates comprehensive charts and visualizations for equity research.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional, List
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10


def safe_plot_data(df: pd.DataFrame, columns: list) -> Optional[pd.DataFrame]:
    """
    Safely prepare data for plotting by filtering NaN and converting to numeric.
    
    Args:
        df: Input DataFrame
        columns: List of columns to check and clean
        
    Returns:
        Cleaned DataFrame or None if no valid data
    """
    df_clean = df.copy()
    
    # Filter out rows where ALL specified columns are NaN
    mask = df_clean[columns].notna().any(axis=1)
    df_clean = df_clean[mask]
    
    if len(df_clean) == 0:
        return None
    
    # Convert columns to numeric
    for col in columns:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    
    return df_clean


def plot_revenue_growth(df: pd.DataFrame, output_dir: str):
    """1. Revenue growth chart"""
    try:
        fig, ax = plt.subplots(figsize=(14, 7))
        
        if 'revenue' not in df.columns or 'year_quarter' not in df.columns:
            print("⚠ Skipped: revenue_growth_chart.png (missing columns)")
            plt.close()
            return
        
        # Clean data
        df_plot = safe_plot_data(df, ['revenue'])
        if df_plot is None:
            print("⚠ Skipped: revenue_growth_chart.png (no data)")
            plt.close()
            return
        
        # Bar chart for revenue
        ax.bar(df_plot['year_quarter'], df_plot['revenue'], alpha=0.7, color='steelblue', label='Revenue')
        
        # Line for YoY growth if available
        if 'revenue_yoy' in df_plot.columns:
            df_yoy = df_plot[df_plot['revenue_yoy'].notna()]
            if len(df_yoy) > 0:
                ax2 = ax.twinx()
                ax2.plot(df_yoy['year_quarter'], df_yoy['revenue_yoy'], color='red', marker='o', 
                        linewidth=2, label='YoY Growth %')
                ax2.set_ylabel('YoY Growth (%)', fontsize=12)
                ax2.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
                ax2.legend(loc='upper right')
        
        ax.set_xlabel('Quarter', fontsize=12)
        ax.set_ylabel('Revenue ($)', fontsize=12)
        ax.set_title('Revenue Growth Trend', fontsize=14, fontweight='bold')
        ax.legend(loc='upper left')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        plt.savefig(f"{output_dir}/revenue_growth_chart.png", dpi=300, bbox_inches='tight')
        print("✓ Generated: revenue_growth_chart.png")
    except Exception as e:
        print(f"⚠ Error generating revenue_growth_chart: {e}")
    finally:
        plt.close()


def plot_net_profit_margin(df: pd.DataFrame, output_dir: str):
    """2. Net profit margin trend"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    if 'net_margin' in df.columns and 'year_quarter' in df.columns:
        ax.plot(df['year_quarter'], df['net_margin'], marker='o', linewidth=2.5, 
               color='green', label='Net Profit Margin')
        ax.axhline(y=0, color='red', linestyle='--', alpha=0.5, label='Break-even')
        
        # Add trend line
        x_numeric = np.arange(len(df))
        mask = df['net_margin'].notna()
        if mask.sum() > 1:
            z = np.polyfit(x_numeric[mask], df['net_margin'][mask], 1)
            p = np.poly1d(z)
            ax.plot(df['year_quarter'], p(x_numeric), "--", color='gray', alpha=0.7, label='Trend')
        
        ax.set_xlabel('Quarter', fontsize=12)
        ax.set_ylabel('Net Profit Margin (%)', fontsize=12)
        ax.set_title('Net Profit Margin Trend', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        plt.savefig(f"{output_dir}/net_profit_margin_trend.png", dpi=300, bbox_inches='tight')
        print("✓ Generated: net_profit_margin_trend.png")
    plt.close()


def plot_ebitda_margin(df: pd.DataFrame, output_dir: str):
    """3. EBITDA margin trend"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    if 'ebitda_margin' in df.columns and 'year_quarter' in df.columns:
        ax.plot(df['year_quarter'], df['ebitda_margin'], marker='s', linewidth=2.5,
               color='purple', label='EBITDA Margin')
        ax.fill_between(df['year_quarter'], df['ebitda_margin'], alpha=0.3, color='purple')
        
        ax.set_xlabel('Quarter', fontsize=12)
        ax.set_ylabel('EBITDA Margin (%)', fontsize=12)
        ax.set_title('EBITDA Margin Trend', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        plt.savefig(f"{output_dir}/ebitda_margin_trend.png", dpi=300, bbox_inches='tight')
        print("✓ Generated: ebitda_margin_trend.png")
    plt.close()


def plot_operating_cash_flow(df: pd.DataFrame, output_dir: str):
    """4. Operating cash flow trend"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    if 'operating_cf' in df.columns and 'year_quarter' in df.columns:
        colors = ['green' if x >= 0 else 'red' for x in df['operating_cf']]
        ax.bar(df['year_quarter'], df['operating_cf'], color=colors, alpha=0.7, 
              label='Operating Cash Flow')
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        
        ax.set_xlabel('Quarter', fontsize=12)
        ax.set_ylabel('Operating Cash Flow ($)', fontsize=12)
        ax.set_title('Operating Cash Flow Trend', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        plt.savefig(f"{output_dir}/operating_cash_flow_trend.png", dpi=300, bbox_inches='tight')
        print("✓ Generated: operating_cash_flow_trend.png")
    plt.close()


def plot_debt_to_equity(df: pd.DataFrame, output_dir: str):
    """5. Debt to equity ratio over time"""
    try:
        fig, ax = plt.subplots(figsize=(12, 6))
        
        if 'debt_to_equity' not in df.columns or 'year_quarter' not in df.columns:
            print("⚠ Skipped: debt_to_equity_trend.png (missing columns)")
            plt.close()
            return
        
        # Clean data
        df_plot = safe_plot_data(df, ['debt_to_equity'])
        if df_plot is None:
            print("⚠ Skipped: debt_to_equity_trend.png (no data)")
            plt.close()
            return
        
        ax.plot(df_plot['year_quarter'], df_plot['debt_to_equity'], marker='D', linewidth=2.5,
               color='darkred', label='Debt/Equity Ratio')
        ax.axhline(y=1.0, color='orange', linestyle='--', alpha=0.7, label='1.0 Benchmark')
        ax.fill_between(df_plot['year_quarter'], df_plot['debt_to_equity'], alpha=0.2, color='darkred')
        
        ax.set_xlabel('Quarter', fontsize=12)
        ax.set_ylabel('Debt to Equity Ratio', fontsize=12)
        ax.set_title('Debt to Equity Ratio Over Time', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        plt.savefig(f"{output_dir}/debt_to_equity_trend.png", dpi=300, bbox_inches='tight')
        print("✓ Generated: debt_to_equity_trend.png")
    except Exception as e:
        print(f"⚠ Error generating debt_to_equity_trend: {e}")
    finally:
        plt.close()


def plot_roe_trend(df: pd.DataFrame, output_dir: str):
    """6. Return on equity (ROE) trend"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    if 'roe' in df.columns and 'year_quarter' in df.columns:
        ax.plot(df['year_quarter'], df['roe'], marker='o', linewidth=2.5,
               color='darkgreen', label='ROE')
        
        # Add ROA for comparison if available
        if 'roa' in df.columns:
            ax.plot(df['year_quarter'], df['roa'], marker='s', linewidth=2.5,
                   color='darkblue', alpha=0.7, label='ROA')
        
        ax.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        ax.axhline(y=15, color='green', linestyle='--', alpha=0.5, label='15% Benchmark')
        
        ax.set_xlabel('Quarter', fontsize=12)
        ax.set_ylabel('Return (%)', fontsize=12)
        ax.set_title('Return on Equity (ROE) Trend', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        plt.savefig(f"{output_dir}/roe_trend.png", dpi=300, bbox_inches='tight')
        print("✓ Generated: roe_trend.png")
    plt.close()


def plot_current_ratio(df: pd.DataFrame, output_dir: str):
    """7. Current ratio (liquidity) trend"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    if 'current_ratio' in df.columns and 'year_quarter' in df.columns:
        ax.plot(df['year_quarter'], df['current_ratio'], marker='o', linewidth=2.5,
               color='teal', label='Current Ratio')
        
        # Add quick ratio if available
        if 'quick_ratio' in df.columns:
            ax.plot(df['year_quarter'], df['quick_ratio'], marker='s', linewidth=2,
                   color='navy', alpha=0.7, label='Quick Ratio')
        
        ax.axhline(y=1.0, color='red', linestyle='--', alpha=0.7, label='1.0 (Minimum)')
        ax.axhline(y=2.0, color='green', linestyle='--', alpha=0.7, label='2.0 (Healthy)')
        
        ax.set_xlabel('Quarter', fontsize=12)
        ax.set_ylabel('Ratio', fontsize=12)
        ax.set_title('Current Ratio (Liquidity) Trend', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        plt.savefig(f"{output_dir}/current_ratio_trend.png", dpi=300, bbox_inches='tight')
        print("✓ Generated: current_ratio_trend.png")
    plt.close()


def plot_insider_transactions(insider_dir: str, output_dir: str):
    """8. Insider transactions overview"""
    insider_path = Path(insider_dir)
    
    if not insider_path.exists():
        print("⚠ Insider transactions data not found")
        return
    
    # Aggregate insider transactions
    files = list(insider_path.glob('form4_nonderivative_*.csv'))
    
    if not files:
        print("⚠ No insider transaction files found")
        return
    
    all_transactions = []
    for file in files:
        try:
            df = pd.read_csv(file)
            if 'filing_date' in df.columns:
                all_transactions.append(df)
        except:
            continue
    
    if not all_transactions:
        return
    
    df_insider = pd.concat(all_transactions, ignore_index=True)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Transaction count by date
    if 'filing_date' in df_insider.columns:
        df_insider['filing_date'] = pd.to_datetime(df_insider['filing_date'])
        tx_counts = df_insider.groupby(df_insider['filing_date'].dt.to_period('Q')).size()
        ax1.bar(range(len(tx_counts)), tx_counts.values, color='coral', alpha=0.7)
        ax1.set_xlabel('Quarter', fontsize=12)
        ax1.set_ylabel('Number of Transactions', fontsize=12)
        ax1.set_title('Insider Trading Activity by Quarter', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3, axis='y')
    
    # Transaction type distribution (if available)
    ax2.text(0.5, 0.5, 'Insider Transaction Details\n(See form4 CSV files)', 
            ha='center', va='center', fontsize=14)
    ax2.axis('off')
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/insider_transactions_overview.png", dpi=300, bbox_inches='tight')
    print("✓ Generated: insider_transactions_overview.png")
    plt.close()


def plot_quarterly_vs_annual(df: pd.DataFrame, output_dir: str):
    """9. Quarterly vs annual earnings comparison"""
    fig, ax = plt.subplots(figsize=(14, 7))
    
    if 'net_income' in df.columns and 'year_quarter' in df.columns:
        # Quarterly earnings
        ax.bar(df['year_quarter'], df['net_income'], alpha=0.6, color='skyblue', 
              label='Quarterly Net Income')
        
        # TTM earnings if available
        if 'net_income_ttm' in df.columns:
            ax.plot(df['year_quarter'], df['net_income_ttm'], color='darkblue', 
                   marker='o', linewidth=2.5, label='TTM (Trailing 12 Months)')
        
        ax.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        ax.set_xlabel('Quarter', fontsize=12)
        ax.set_ylabel('Net Income ($)', fontsize=12)
        ax.set_title('Quarterly vs Annual Earnings Comparison', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        plt.savefig(f"{output_dir}/quarterly_vs_annual_earnings.png", dpi=300, bbox_inches='tight')
        print("✓ Generated: quarterly_vs_annual_earnings.png")
    plt.close()


def plot_free_cash_flow(df: pd.DataFrame, output_dir: str):
    """10. Free cash flow trend"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    if 'free_cash_flow' in df.columns and 'year_quarter' in df.columns:
        colors = ['green' if x >= 0 else 'red' for x in df['free_cash_flow']]
        ax.bar(df['year_quarter'], df['free_cash_flow'], color=colors, alpha=0.7,
              label='Free Cash Flow')
        
        # Add cumulative FCF line
        cumulative_fcf = df['free_cash_flow'].cumsum()
        ax2 = ax.twinx()
        ax2.plot(df['year_quarter'], cumulative_fcf, color='purple', marker='o',
                linewidth=2, label='Cumulative FCF')
        ax2.set_ylabel('Cumulative FCF ($)', fontsize=12)
        ax2.legend(loc='upper right')
        
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        ax.set_xlabel('Quarter', fontsize=12)
        ax.set_ylabel('Free Cash Flow ($)', fontsize=12)
        ax.set_title('Free Cash Flow Trend', fontsize=14, fontweight='bold')
        ax.legend(loc='upper left')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        plt.savefig(f"{output_dir}/free_cash_flow_trend.png", dpi=300, bbox_inches='tight')
        print("✓ Generated: free_cash_flow_trend.png")
    plt.close()


def plot_eps_trend(df: pd.DataFrame, output_dir: str):
    """11. Earnings per share (EPS) trend"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    eps_col = 'eps_diluted' if 'eps_diluted' in df.columns else 'eps_basic' if 'eps_basic' in df.columns else None
    
    if eps_col and 'year_quarter' in df.columns:
        ax.plot(df['year_quarter'], df[eps_col], marker='o', linewidth=2.5,
               color='darkblue', label=f'EPS ({eps_col.replace("_", " ").title()})')
        ax.fill_between(df['year_quarter'], df[eps_col], alpha=0.3, color='darkblue')
        ax.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        
        ax.set_xlabel('Quarter', fontsize=12)
        ax.set_ylabel('EPS ($)', fontsize=12)
        ax.set_title('Earnings Per Share (EPS) Trend', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        plt.savefig(f"{output_dir}/eps_trend.png", dpi=300, bbox_inches='tight')
        print("✓ Generated: eps_trend.png")
    plt.close()


def plot_stock_price_vs_earnings(df_financial: pd.DataFrame, df_market: pd.DataFrame, output_dir: str):
    """12. Stock price vs earnings correlation"""
    fig, ax1 = plt.subplots(figsize=(14, 7))
    
    # Merge financial and market data by quarter
    if 'date' in df_financial.columns and 'date' in df_market.columns:
        df_financial['date'] = pd.to_datetime(df_financial['date'])
        df_market['date'] = pd.to_datetime(df_market['date'])
        
        # Aggregate market data by quarter
        df_market['year_quarter'] = df_market['date'].dt.to_period('Q').astype(str)
        market_quarterly = df_market.groupby('year_quarter')['close'].mean().reset_index()
        
        df_merged = pd.merge(df_financial, market_quarterly, on='year_quarter', how='inner')
        
        if len(df_merged) > 0 and 'close' in df_merged.columns and 'net_income' in df_merged.columns:
            # Plot stock price
            ax1.plot(df_merged['year_quarter'], df_merged['close'], color='blue', 
                    marker='o', linewidth=2.5, label='Stock Price')
            ax1.set_xlabel('Quarter', fontsize=12)
            ax1.set_ylabel('Stock Price ($)', color='blue', fontsize=12)
            ax1.tick_params(axis='y', labelcolor='blue')
            
            # Plot earnings on secondary axis
            ax2 = ax1.twinx()
            ax2.bar(df_merged['year_quarter'], df_merged['net_income'], alpha=0.3, 
                   color='green', label='Net Income')
            ax2.set_ylabel('Net Income ($)', color='green', fontsize=12)
            ax2.tick_params(axis='y', labelcolor='green')
            
            ax1.set_title('Stock Price vs Earnings Correlation', fontsize=14, fontweight='bold')
            ax1.legend(loc='upper left')
            ax2.legend(loc='upper right')
            ax1.grid(True, alpha=0.3)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            plt.savefig(f"{output_dir}/stock_price_vs_earnings.png", dpi=300, bbox_inches='tight')
            print("✓ Generated: stock_price_vs_earnings.png")
    plt.close()


def plot_key_events_timeline(events_dir: str, output_dir: str):
    """15. Key event impact timeline (from 8-K reports)"""
    events_path = Path(events_dir)
    
    if not events_path.exists():
        print("⚠ 8-K events data not found")
        return
    
    # Load 8-K metadata
    metadata_files = list(events_path.glob('8k_metadata_*.csv'))
    
    if not metadata_files:
        print("⚠ No 8-K metadata files found")
        return
    
    all_events = []
    for file in metadata_files:
        try:
            df = pd.read_csv(file)
            if 'filing_date' in df.columns:
                all_events.append(df)
        except:
            continue
    
    if not all_events:
        return
    
    df_events = pd.concat(all_events, ignore_index=True)
    df_events['filing_date'] = pd.to_datetime(df_events['filing_date'])
    df_events = df_events.sort_values('filing_date')
    
    fig, ax = plt.subplots(figsize=(16, 8))
    
    # Create timeline
    y_positions = range(len(df_events))
    ax.scatter(df_events['filing_date'], y_positions, s=100, color='red', alpha=0.7, zorder=3)
    
    for i, (idx, row) in enumerate(df_events.iterrows()):
        ax.text(row['filing_date'], i, f"  {row['filing_date'].strftime('%Y-%m-%d')}", 
               fontsize=8, va='center')
    
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('8-K Filing Events', fontsize=12)
    ax.set_title('Key Events Timeline (8-K Reports)', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='x')
    plt.yticks([])
    plt.tight_layout()
    
    plt.savefig(f"{output_dir}/key_events_timeline.png", dpi=300, bbox_inches='tight')
    print("✓ Generated: key_events_timeline.png")
    plt.close()


def generate_all_visualizations(
    df_timeseries: pd.DataFrame,
    df_market: pd.DataFrame,
    processed_dir: str,
    output_dir: str
):
    """
    Generate all visualizations.
    
    Args:
        df_timeseries: Time series DataFrame with all metrics
        df_market: Market data DataFrame
        processed_dir: Directory with processed data
        output_dir: Directory to save visualizations
    """
    print("\n" + "=" * 80)
    print("GENERATING VISUALIZATIONS")
    print("=" * 80 + "\n")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    trends_dir = output_path / 'trends'
    trends_dir.mkdir(exist_ok=True)
    
    ratios_dir = output_path / 'ratios'
    ratios_dir.mkdir(exist_ok=True)
    
    events_dir = output_path / 'events'
    events_dir.mkdir(exist_ok=True)
    
    # Generate all charts with error handling
    charts = [
        (plot_revenue_growth, (df_timeseries, str(trends_dir))),
        (plot_net_profit_margin, (df_timeseries, str(ratios_dir))),
        (plot_ebitda_margin, (df_timeseries, str(ratios_dir))),
        (plot_operating_cash_flow, (df_timeseries, str(trends_dir))),
        (plot_debt_to_equity, (df_timeseries, str(ratios_dir))),
        (plot_roe_trend, (df_timeseries, str(ratios_dir))),
        (plot_current_ratio, (df_timeseries, str(ratios_dir))),
        (plot_quarterly_vs_annual, (df_timeseries, str(trends_dir))),
        (plot_free_cash_flow, (df_timeseries, str(trends_dir))),
        (plot_eps_trend, (df_timeseries, str(trends_dir))),
    ]
    
    for chart_func, args in charts:
        try:
            chart_func(*args)
        except Exception as e:
            print(f"⚠ Error in {chart_func.__name__}: {e}")
    
    # Insider transactions
    try:
        insider_dir = Path(processed_dir) / 'insider transactions'
        plot_insider_transactions(str(insider_dir), str(events_dir))
    except Exception as e:
        print(f"⚠ Error in insider transactions chart: {e}")
    
    # Stock price vs earnings
    try:
        plot_stock_price_vs_earnings(df_timeseries, df_market, str(trends_dir))
    except Exception as e:
        print(f"⚠ Error in stock price vs earnings chart: {e}")
    
    # 8-K events
    try:
        events_data_dir = Path(processed_dir) / '8-k related'
        plot_key_events_timeline(str(events_data_dir), str(events_dir))
    except Exception as e:
        print(f"⚠ Error in events timeline chart: {e}")
    
    print(f"\n{'=' * 80}")
    print("VISUALIZATION COMPLETE")
    print(f"{'=' * 80}")
    print(f"\nVisualizations saved to:")
    print(f"  - Trends: {trends_dir}")
    print(f"  - Ratios: {ratios_dir}")
    print(f"  - Events: {events_dir}\n")


if __name__ == '__main__':
    base_dir = Path(__file__).parent.parent.parent
    metrics_dir = base_dir / 'data' / 'metrics'
    processed_dir = base_dir / 'data' / 'processed'
    output_dir = base_dir / 'data' / 'analysis' / 'visualizations'
    
    # Load data
    df_timeseries = pd.read_csv(metrics_dir / 'aggregated' / 'comprehensive_timeseries.csv')
    df_market = pd.read_csv(processed_dir / 'market_data' / 'stock_prices_daily.csv')
    
    generate_all_visualizations(df_timeseries, df_market, str(processed_dir), str(output_dir))

