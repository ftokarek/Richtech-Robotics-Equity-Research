

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional


def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.04) -> float:
    
    excess_returns = returns - (risk_free_rate / 252)  
    return (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)


def calculate_information_ratio(returns: pd.Series, benchmark_returns: pd.Series) -> float:
    
    active_returns = returns - benchmark_returns
    tracking_error = active_returns.std()
    
    if tracking_error == 0:
        return 0.0
    
    return (active_returns.mean() / tracking_error) * np.sqrt(252)


def calculate_pe_ratio(market_cap: float, net_income: float) -> Optional[float]:
    
    if net_income <= 0:
        return None
    return market_cap / net_income


def calculate_pb_ratio(market_cap: float, book_value: float) -> Optional[float]:
    
    if book_value <= 0:
        return None
    return market_cap / book_value


def calculate_ps_ratio(market_cap: float, revenue: float) -> Optional[float]:
    
    if revenue <= 0:
        return None
    return market_cap / revenue


def calculate_ev_ebitda(enterprise_value: float, ebitda: float) -> Optional[float]:
    
    if ebitda <= 0:
        return None
    return enterprise_value / ebitda


def calculate_peg_ratio(pe_ratio: float, growth_rate: float) -> Optional[float]:
    
    if growth_rate <= 0 or pe_ratio is None:
        return None
    return pe_ratio / growth_rate


def calculate_market_metrics(
    df_financial: pd.DataFrame,
    df_market: pd.DataFrame,
    output_dir: str,
    shares_outstanding: float = None
) -> pd.DataFrame:
    
    print("\n" + "=" * 80)
    print("CALCULATING VALUATION METRICS")
    print("=" * 80)
    
    df_fin = df_financial.copy()
    df_mkt = df_market.copy()
    
    
    df_fin['date'] = pd.to_datetime(df_fin['date'])
    df_mkt['date'] = pd.to_datetime(df_mkt['date'])
    
    
    if 'year_quarter' not in df_fin.columns:
        df_fin['year'] = df_fin['date'].dt.year
        df_fin['quarter'] = df_fin['date'].dt.quarter
        df_fin['year_quarter'] = df_fin['year'].astype(str) + '-Q' + df_fin['quarter'].astype(str)
    
    
    
    df_mkt['year'] = df_mkt['date'].dt.year
    df_mkt['quarter'] = df_mkt['date'].dt.quarter
    df_mkt['year_quarter'] = df_mkt['year'].astype(str) + '-Q' + df_mkt['quarter'].astype(str)
    
    market_quarterly = df_mkt.groupby('year_quarter').agg({
        'close': 'last',  
        'volume': 'sum',
        'daily_return': 'mean'
    }).reset_index()
    
    print(f"\nFinancial quarters: {sorted(df_fin['year_quarter'].unique())}")
    print(f"Market quarters: {sorted(market_quarterly['year_quarter'].unique())}")
    
    
    df_merged = pd.merge(df_fin, market_quarterly, on='year_quarter', how='inner')
    
    print(f"Merged {len(df_merged)} quarters of data")
    
    
    
    if shares_outstanding is None:
        
        if len(df_merged) > 0 and 'eps_diluted' in df_merged.columns and 'net_income' in df_merged.columns:
            eps_series = df_merged[df_merged['eps_diluted'].notna()]['eps_diluted']
            ni_series = df_merged[df_merged['net_income'].notna()]['net_income']
            
            if len(eps_series) > 0 and len(ni_series) > 0:
                eps_data = eps_series.iloc[-1]
                ni_data = ni_series.iloc[-1]
                if eps_data != 0:
                    shares_outstanding = abs(ni_data / eps_data)
                    print(f"Estimated shares outstanding: {shares_outstanding:,.0f}")
                else:
                    shares_outstanding = 100_000_000  
            else:
                print("⚠ Shares outstanding not provided, using default estimate")
                shares_outstanding = 100_000_000  
        else:
            print("⚠ Shares outstanding not provided, using default estimate")
            shares_outstanding = 100_000_000  
    
    df_merged['shares_outstanding'] = shares_outstanding
    df_merged['market_cap'] = df_merged['close'] * shares_outstanding
    
    
    if 'total_liabilities' in df_merged.columns and 'cash' in df_merged.columns:
        df_merged['enterprise_value'] = df_merged['market_cap'] + df_merged['total_liabilities'] - df_merged['cash']
    
    
    print("\nCalculating valuation ratios...")
    
    
    if 'market_cap' in df_merged.columns and 'net_income' in df_merged.columns:
        df_merged['pe_ratio'] = df_merged.apply(
            lambda row: calculate_pe_ratio(row['market_cap'], row['net_income'])
            if pd.notna(row['net_income']) else None, axis=1
        )
    
    
    if 'market_cap' in df_merged.columns and 'stockholders_equity' in df_merged.columns:
        df_merged['pb_ratio'] = df_merged.apply(
            lambda row: calculate_pb_ratio(row['market_cap'], row['stockholders_equity'])
            if pd.notna(row['stockholders_equity']) else None, axis=1
        )
    
    
    if 'market_cap' in df_merged.columns and 'revenue' in df_merged.columns:
        df_merged['ps_ratio'] = df_merged.apply(
            lambda row: calculate_ps_ratio(row['market_cap'], row['revenue'])
            if pd.notna(row['revenue']) else None, axis=1
        )
    
    
    if 'enterprise_value' in df_merged.columns and 'ebitda' in df_merged.columns:
        df_merged['ev_ebitda'] = df_merged.apply(
            lambda row: calculate_ev_ebitda(row['enterprise_value'], row['ebitda'])
            if pd.notna(row['ebitda']) else None, axis=1
        )
    
    
    if 'pe_ratio' in df_merged.columns and 'revenue_yoy' in df_merged.columns:
        df_merged['peg_ratio'] = df_merged.apply(
            lambda row: calculate_peg_ratio(row['pe_ratio'], row['revenue_yoy'])
            if pd.notna(row['pe_ratio']) and pd.notna(row['revenue_yoy']) else None, axis=1
        )
    
    
    print("\nCalculating risk-adjusted returns...")
    
    if 'daily_return' in df_mkt.columns:
        returns = df_mkt['daily_return'].dropna()
        if len(returns) > 20:
            sharpe = calculate_sharpe_ratio(returns)
            print(f"Sharpe Ratio: {sharpe:.3f}")
            df_merged['sharpe_ratio'] = sharpe
    
    
    
    df_merged['information_ratio'] = np.nan  
    
    
    
    df_merged['dividend_yield'] = np.nan
    
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    valuation_file = output_path / 'aggregated' / 'valuation_metrics.csv'
    valuation_file.parent.mkdir(parents=True, exist_ok=True)
    df_merged.to_csv(valuation_file, index=False)
    
    print(f"\n✓ Saved valuation metrics to: {valuation_file}")
    
    
    print(f"\n{'=' * 80}")
    print("VALUATION SUMMARY (Latest Quarter)")
    print(f"{'=' * 80}")
    
    if len(df_merged) > 0:
        latest = df_merged.iloc[-1]
        
        metrics_summary = {
            'Quarter': latest.get('year_quarter', 'N/A'),
            'Stock Price': f"${latest['close']:.2f}" if 'close' in latest and pd.notna(latest['close']) else 'N/A',
            'Market Cap': f"${latest['market_cap']:,.0f}" if 'market_cap' in latest and pd.notna(latest['market_cap']) else 'N/A',
            'P/E Ratio': f"{latest['pe_ratio']:.2f}" if 'pe_ratio' in latest and pd.notna(latest['pe_ratio']) else 'N/A',
            'P/B Ratio': f"{latest['pb_ratio']:.2f}" if 'pb_ratio' in latest and pd.notna(latest['pb_ratio']) else 'N/A',
            'P/S Ratio': f"{latest['ps_ratio']:.2f}" if 'ps_ratio' in latest and pd.notna(latest['ps_ratio']) else 'N/A',
            'EV/EBITDA': f"{latest['ev_ebitda']:.2f}" if 'ev_ebitda' in latest and pd.notna(latest['ev_ebitda']) else 'N/A',
            'Sharpe Ratio': f"{latest['sharpe_ratio']:.3f}" if 'sharpe_ratio' in latest and pd.notna(latest['sharpe_ratio']) else 'N/A',
        }
        
        for metric, value in metrics_summary.items():
            print(f"{metric:.<30} {value}")
    
    print(f"\n{'=' * 80}\n")
    
    return df_merged


def plot_valuation_ratios(df_valuation: pd.DataFrame, output_dir: str):
    
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd
    
    if len(df_valuation) == 0:
        print("⚠ No valuation data to plot")
        return
    
    sns.set_style("whitegrid")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    
    if 'pe_ratio' in df_valuation.columns and 'year_quarter' in df_valuation.columns:
        df_pe = df_valuation[df_valuation['pe_ratio'].notna()]
        if len(df_pe) > 0:
            axes[0, 0].plot(df_pe['year_quarter'], df_pe['pe_ratio'], 
                           marker='o', linewidth=2, color='darkblue')
            axes[0, 0].set_title('P/E Ratio Over Time', fontweight='bold')
        else:
            axes[0, 0].text(0.5, 0.5, 'N/A\n(Negative Earnings)', 
                          ha='center', va='center', fontsize=14, transform=axes[0, 0].transAxes)
            axes[0, 0].set_title('P/E Ratio Over Time', fontweight='bold')
        axes[0, 0].set_xlabel('Quarter')
        axes[0, 0].set_ylabel('P/E Ratio')
        axes[0, 0].grid(True, alpha=0.3)
    
    
    if 'pb_ratio' in df_valuation.columns:
        df_pb = df_valuation[df_valuation['pb_ratio'].notna()]
        if len(df_pb) > 0:
            axes[0, 1].plot(df_pb['year_quarter'], df_pb['pb_ratio'],
                           marker='s', linewidth=2, color='darkgreen')
            axes[0, 1].axhline(y=1.0, color='orange', linestyle='--', alpha=0.5, label='Book Value')
            axes[0, 1].legend()
        else:
            axes[0, 1].text(0.5, 0.5, 'No Data', ha='center', va='center', 
                          fontsize=14, transform=axes[0, 1].transAxes)
        axes[0, 1].set_title('P/B Ratio Over Time', fontweight='bold')
        axes[0, 1].set_xlabel('Quarter')
        axes[0, 1].set_ylabel('P/B Ratio')
        axes[0, 1].grid(True, alpha=0.3)
        plt.setp(axes[0, 1].xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    
    if 'ev_ebitda' in df_valuation.columns:
        df_ev = df_valuation[df_valuation['ev_ebitda'].notna()]
        if len(df_ev) > 0:
            axes[1, 0].plot(df_ev['year_quarter'], df_ev['ev_ebitda'],
                           marker='D', linewidth=2, color='darkred')
        else:
            axes[1, 0].text(0.5, 0.5, 'N/A\n(Negative EBITDA)', 
                          ha='center', va='center', fontsize=14, transform=axes[1, 0].transAxes)
        axes[1, 0].set_title('EV/EBITDA Over Time', fontweight='bold')
        axes[1, 0].set_xlabel('Quarter')
        axes[1, 0].set_ylabel('EV/EBITDA')
        axes[1, 0].grid(True, alpha=0.3)
    
    
    if 'ps_ratio' in df_valuation.columns:
        df_ps = df_valuation[df_valuation['ps_ratio'].notna()]
        if len(df_ps) > 0:
            axes[1, 1].plot(df_ps['year_quarter'], df_ps['ps_ratio'],
                           marker='^', linewidth=2.5, color='purple')
            axes[1, 1].fill_between(df_ps['year_quarter'], df_ps['ps_ratio'], alpha=0.2, color='purple')
        else:
            axes[1, 1].text(0.5, 0.5, 'No Data', ha='center', va='center', 
                          fontsize=14, transform=axes[1, 1].transAxes)
        axes[1, 1].set_title('P/S Ratio Over Time', fontweight='bold')
        axes[1, 1].set_xlabel('Quarter')
        axes[1, 1].set_ylabel('P/S Ratio')
        axes[1, 1].grid(True, alpha=0.3)
        plt.setp(axes[1, 1].xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    plt.savefig(f"{output_path}/valuation_ratios_trends.png", dpi=300, bbox_inches='tight')
    print("✓ Generated: valuation_ratios_trends.png")
    plt.close()


if __name__ == '__main__':
    base_dir = Path(__file__).parent.parent.parent
    metrics_dir = base_dir / 'data' / 'metrics'
    processed_dir = base_dir / 'data' / 'processed'
    output_dir = base_dir / 'data' / 'analysis' / 'visualizations' / 'ratios'
    
    
    df_financial = pd.read_csv(metrics_dir / 'aggregated' / 'comprehensive_timeseries.csv')
    df_market = pd.read_csv(processed_dir / 'market_data' / 'stock_prices_daily.csv')
    
    
    df_valuation = calculate_market_metrics(df_financial, df_market, str(metrics_dir))
    
    
    plot_valuation_ratios(df_valuation, str(output_dir))
    
    print(f"\n{'=' * 80}")
    print("VALUATION ANALYSIS COMPLETE")
    print(f"{'=' * 80}\n")

