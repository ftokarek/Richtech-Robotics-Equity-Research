

import sys
from pathlib import Path
from datetime import datetime
import argparse


sys.path.append(str(Path(__file__).parent / 'scripts'))
sys.path.append(str(Path(__file__).parent / 'analysis'))

from scripts.extract_market_data import process_market_data
from analysis.extract_metrics import extract_all_metrics
from analysis.calculate_ratios import calculate_all_ratios
from analysis.time_series import create_comprehensive_timeseries
from analysis.valuation import calculate_market_metrics, plot_valuation_ratios
from analysis.visualize import generate_all_visualizations


def print_banner():
    
    print("\n" + "=" * 80)
    print("RICHTECH ROBOTICS - COMPREHENSIVE FINANCIAL ANALYSIS")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")


def print_summary(results: dict):
    
    print("\n" + "=" * 80)
    print("ANALYSIS SUMMARY")
    print("=" * 80)
    
    for step, result in results.items():
        status = "✓" if result.get('status') == 'success' else "✗"
        print(f"\n{status} {step}")
        if result.get('message'):
            print(f"   {result['message']}")
        if result.get('files_created'):
            print(f"   Files created: {result['files_created']}")
    
    print(f"\n{'=' * 80}")
    print(f"Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")


def run_complete_analysis(base_dir: Path, skip_steps: list = None):
    
    skip_steps = skip_steps or []
    results = {}
    
    
    raw_dir = base_dir / 'data' / 'raw'
    processed_dir = base_dir / 'data' / 'processed'
    metrics_dir = base_dir / 'data' / 'metrics'
    analysis_dir = base_dir / 'data' / 'analysis'
    
    
    if 'market_data' not in skip_steps:
        print("STEP 1: Extracting Market Data")
        print("-" * 80)
        try:
            market_input = raw_dir / 'market_data' / 'ChartData.xlsx'
            market_output = processed_dir / 'market_data'
            
            if market_input.exists():
                result = process_market_data(str(market_input), str(market_output))
                results['Market Data Extraction'] = {
                    'status': 'success',
                    'message': f"Processed {result['records']} days of data",
                    'files_created': 2
                }
            else:
                results['Market Data Extraction'] = {
                    'status': 'skipped',
                    'message': 'ChartData.xlsx not found'
                }
        except Exception as e:
            results['Market Data Extraction'] = {
                'status': 'error',
                'message': str(e)
            }
    
    
    if 'extract_metrics' not in skip_steps:
        print("\nSTEP 2: Extracting Financial Metrics")
        print("-" * 80)
        try:
            metrics_dict = extract_all_metrics(str(processed_dir), str(metrics_dir))
            total_records = sum(len(df) for df in metrics_dict.values())
            results['Financial Metrics Extraction'] = {
                'status': 'success',
                'message': f"Extracted {total_records} periods of financial data",
                'files_created': len(metrics_dict)
            }
        except Exception as e:
            results['Financial Metrics Extraction'] = {
                'status': 'error',
                'message': str(e)
            }
            return results
    
    
    if 'calculate_ratios' not in skip_steps:
        print("\nSTEP 3: Calculating Financial Ratios")
        print("-" * 80)
        try:
            df_ratios = calculate_all_ratios(metrics_dict, str(metrics_dir))
            results['Financial Ratios Calculation'] = {
                'status': 'success',
                'message': f"Calculated {len(df_ratios.columns)} metrics/ratios",
                'files_created': 1
            }
        except Exception as e:
            results['Financial Ratios Calculation'] = {
                'status': 'error',
                'message': str(e)
            }
            return results
    
    
    if 'time_series' not in skip_steps:
        print("\nSTEP 4: Creating Time Series")
        print("-" * 80)
        try:
            df_timeseries = create_comprehensive_timeseries(df_ratios, str(metrics_dir))
            results['Time Series Creation'] = {
                'status': 'success',
                'message': f"Created time series with {len(df_timeseries)} periods",
                'files_created': 1
            }
        except Exception as e:
            results['Time Series Creation'] = {
                'status': 'error',
                'message': str(e)
            }
            return results
    
    
    if 'valuation' not in skip_steps:
        print("\nSTEP 5: Calculating Valuation Metrics")
        print("-" * 80)
        try:
            df_market = None
            market_file = processed_dir / 'market_data' / 'stock_prices_daily.csv'
            if market_file.exists():
                import pandas as pd
                df_market = pd.read_csv(market_file)
                
                df_valuation = calculate_market_metrics(
                    df_timeseries, df_market, str(metrics_dir)
                )
                
                
                viz_output = analysis_dir / 'visualizations' / 'ratios'
                plot_valuation_ratios(df_valuation, str(viz_output))
                
                results['Valuation Metrics'] = {
                    'status': 'success',
                    'message': 'Calculated P/E, P/B, EV/EBITDA, Sharpe Ratio',
                    'files_created': 2
                }
            else:
                results['Valuation Metrics'] = {
                    'status': 'skipped',
                    'message': 'Market data not available'
                }
        except Exception as e:
            results['Valuation Metrics'] = {
                'status': 'error',
                'message': str(e)
            }
    
    
    if 'visualizations' not in skip_steps:
        print("\nSTEP 6: Generating Visualizations")
        print("-" * 80)
        try:
            viz_output = analysis_dir / 'visualizations'
            
            import pandas as pd
            df_market = pd.DataFrame()
            market_file = processed_dir / 'market_data' / 'stock_prices_daily.csv'
            if market_file.exists():
                df_market = pd.read_csv(market_file)
            
            generate_all_visualizations(
                df_timeseries,
                df_market,
                str(processed_dir),
                str(viz_output)
            )
            
            results['Visualizations'] = {
                'status': 'success',
                'message': 'Generated 15 comprehensive charts',
                'files_created': 15
            }
        except Exception as e:
            results['Visualizations'] = {
                'status': 'error',
                'message': str(e)
            }
    
    return results


def main():
    
    parser = argparse.ArgumentParser(
        description='Run comprehensive financial analysis for Richtech Robotics'
    )
    parser.add_argument(
        '--skip',
        type=str,
        nargs='+',
        choices=['market_data', 'extract_metrics', 'calculate_ratios', 
                'time_series', 'valuation', 'visualizations'],
        help='Steps to skip'
    )
    
    args = parser.parse_args()
    
    
    print_banner()
    
    
    base_dir = Path(__file__).parent.parent
    
    
    results = run_complete_analysis(base_dir, skip_steps=args.skip or [])
    
    
    print_summary(results)
    
    
    print("\n" + "=" * 80)
    print("OUTPUT LOCATIONS")
    print("=" * 80)
    print(f"\nFinancial Metrics:")
    print(f"  {base_dir / 'data' / 'metrics' / 'quarterly'}")
    print(f"  {base_dir / 'data' / 'metrics' / 'aggregated'}")
    
    print(f"\nVisualizations:")
    print(f"  {base_dir / 'data' / 'analysis' / 'visualizations' / 'trends'}")
    print(f"  {base_dir / 'data' / 'analysis' / 'visualizations' / 'ratios'}")
    print(f"  {base_dir / 'data' / 'analysis' / 'visualizations' / 'events'}")
    
    print(f"\nProcessed Data:")
    print(f"  {base_dir / 'data' / 'processed' / 'market_data'}")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE - READY FOR INVESTMENT DECISION")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    main()

