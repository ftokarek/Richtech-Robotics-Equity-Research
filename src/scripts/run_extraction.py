
"""
Master script to run all SEC filing data extraction.

This script orchestrates the extraction of data from all SEC filing types:
- Form 4 (Insider Transactions)
- 10-Q (Quarterly Reports)
- 10-K (Annual Reports)
- 8-K (Current Reports)
- DEF 14A (Proxy Statements)
- S-1/424B4 (Registration Statements)

Usage:
    python run_extraction.py                    # Run all extractors
    python run_extraction.py --only form4       # Run only Form 4 extractor
    python run_extraction.py --skip 8k          # Run all except 8-K
    python run_extraction.py --verbose          # Detailed output
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
import json

# Add extraction modules to path
sys.path.append(str(Path(__file__).parent))

from extraction.extract_form4 import process_all_form4_files
from extraction.extract_10q import process_all_10q_files
from extraction.extract_10k import process_all_10k_files
from extraction.extract_8k import process_all_8k_files
from extraction.extract_def14a import process_all_def14a_files
from extraction.extract_registration import process_all_registration_files


# Configuration
BASE_DIR = Path(__file__).parent.parent.parent
RAW_DATA_DIR = BASE_DIR / 'data' / 'raw'
PROCESSED_DATA_DIR = BASE_DIR / 'data' / 'processed'

# Extractor definitions
EXTRACTORS = {
    'form4': {
        'name': 'Form 4 - Insider Transactions',
        'function': process_all_form4_files,
        'input_dir': RAW_DATA_DIR / 'insider transactions',
        'output_dir': PROCESSED_DATA_DIR / 'insider transactions',
        'enabled': True
    },
    '10q': {
        'name': '10-Q - Quarterly Reports',
        'function': process_all_10q_files,
        'input_dir': RAW_DATA_DIR / 'quarterly reports',
        'output_dir': PROCESSED_DATA_DIR / 'quarterly reports',
        'enabled': True
    },
    '10k': {
        'name': '10-K - Annual Reports',
        'function': process_all_10k_files,
        'input_dir': RAW_DATA_DIR / 'annual reports',
        'output_dir': PROCESSED_DATA_DIR / 'annual reports',
        'enabled': True
    },
    '8k': {
        'name': '8-K - Current Reports',
        'function': process_all_8k_files,
        'input_dir': RAW_DATA_DIR / '8-k related',
        'output_dir': PROCESSED_DATA_DIR / '8-k related',
        'enabled': True
    },
    'def14a': {
        'name': 'DEF 14A - Proxy Statements',
        'function': process_all_def14a_files,
        'input_dir': RAW_DATA_DIR / 'proxies and info statements',
        'output_dir': PROCESSED_DATA_DIR / 'proxies and info statements',
        'enabled': True
    },
    'registration': {
        'name': 'S-1/424B4 - Registration Statements',
        'function': process_all_registration_files,
        'input_dir': RAW_DATA_DIR / 'registration statements',
        'output_dir': PROCESSED_DATA_DIR / 'registration statements',
        'enabled': True
    }
}


def print_banner():
    """Print welcome banner."""
    print("\n" + "=" * 80)
    print("RICHTECH ROBOTICS - SEC FILINGS DATA EXTRACTION")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base directory: {BASE_DIR}")
    print("=" * 80 + "\n")


def print_summary(results: dict):
    """Print extraction summary."""
    print("\n" + "=" * 80)
    print("EXTRACTION SUMMARY")
    print("=" * 80)
    
    total_processed = 0
    total_successful = 0
    total_failed = 0
    
    for extractor_name, result in results.items():
        if result['status'] == 'skipped':
            print(f"\n{result['name']}: SKIPPED")
            continue
        
        processed = result.get('processed', 0)
        successful = result.get('successful', 0)
        failed = result.get('failed', 0)
        
        total_processed += processed
        total_successful += successful
        total_failed += failed
        
        status_symbol = "✓" if failed == 0 else "⚠"
        print(f"\n{status_symbol} {result['name']}:")
        print(f"  Processed: {processed}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        
        if result.get('files_created'):
            print(f"  Files created: {result['files_created']}")
    
    print(f"\n{'=' * 80}")
    print(f"TOTALS:")
    print(f"  Total files processed: {total_processed}")
    print(f"  Total successful: {total_successful}")
    print(f"  Total failed: {total_failed}")
    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")


def run_extractor(extractor_key: str, extractor_config: dict, verbose: bool = False) -> dict:
    """
    Run a single extractor.
    
    Args:
        extractor_key: Key identifying the extractor
        extractor_config: Configuration dict for the extractor
        verbose: Print verbose output
        
    Returns:
        Dict with extraction results
    """
    name = extractor_config['name']
    function = extractor_config['function']
    input_dir = str(extractor_config['input_dir'])
    output_dir = str(extractor_config['output_dir'])
    
    print(f"\n{'=' * 80}")
    print(f"Starting: {name}")
    print(f"Input: {input_dir}")
    print(f"Output: {output_dir}")
    print(f"{'=' * 80}")
    
    try:
        # Run the extraction function
        extraction_results = function(input_dir, output_dir)
        
        # Calculate statistics
        successful = sum(1 for r in extraction_results if r.get('status') == 'success')
        failed = sum(1 for r in extraction_results if r.get('status') == 'error')
        processed = len(extraction_results)
        
        # Count files created
        files_created = 0
        for r in extraction_results:
            if r.get('files_created'):
                files_created += len(r['files_created'])
            elif r.get('nonderivative_file') or r.get('derivative_file'):
                files_created += sum(1 for key in ['nonderivative_file', 'derivative_file'] 
                                   if r.get(key))
        
        return {
            'name': name,
            'status': 'completed',
            'processed': processed,
            'successful': successful,
            'failed': failed,
            'files_created': files_created,
            'details': extraction_results
        }
        
    except Exception as e:
        print(f"\n✗ ERROR: Failed to run {name}")
        print(f"  Error: {str(e)}")
        return {
            'name': name,
            'status': 'error',
            'error': str(e),
            'processed': 0,
            'successful': 0,
            'failed': 0
        }


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Extract data from Richtech Robotics SEC filings'
    )
    parser.add_argument(
        '--only',
        type=str,
        help='Run only specified extractor (form4, 10q, 10k, 8k, def14a, registration)'
    )
    parser.add_argument(
        '--skip',
        type=str,
        help='Skip specified extractor'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print verbose output'
    )
    parser.add_argument(
        '--save-report',
        action='store_true',
        help='Save extraction report to JSON file'
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Determine which extractors to run
    extractors_to_run = {}
    
    if args.only:
        # Run only specified extractor
        if args.only in EXTRACTORS:
            extractors_to_run[args.only] = EXTRACTORS[args.only]
            print(f"Running only: {EXTRACTORS[args.only]['name']}\n")
        else:
            print(f"ERROR: Unknown extractor '{args.only}'")
            print(f"Available: {', '.join(EXTRACTORS.keys())}")
            sys.exit(1)
    else:
        # Run all except skipped
        for key, config in EXTRACTORS.items():
            if args.skip and key == args.skip:
                print(f"Skipping: {config['name']}\n")
                continue
            extractors_to_run[key] = config
    
    # Run extractors
    results = {}
    
    for key, config in extractors_to_run.items():
        result = run_extractor(key, config, args.verbose)
        results[key] = result
    
    # Print summary
    print_summary(results)
    
    # Save report if requested
    if args.save_report:
        report_file = PROCESSED_DATA_DIR / f"extraction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Report saved to: {report_file}\n")
    
    # Return exit code based on results
    total_failed = sum(r.get('failed', 0) for r in results.values())
    sys.exit(0 if total_failed == 0 else 1)


if __name__ == '__main__':
    main()

