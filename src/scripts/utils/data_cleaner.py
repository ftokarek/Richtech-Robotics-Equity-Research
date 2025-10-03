"""
Data cleaning utilities for extracted financial data.
Handles numeric conversions, date standardization, and data validation.
"""

import pandas as pd
import numpy as np
import re
from datetime import datetime
from typing import Any, Union, Optional


def clean_numeric_value(value: Any, handle_negatives: bool = True) -> Optional[float]:
    """
    Clean and convert a value to numeric, handling various formats.
    
    Handles:
    - Parentheses for negatives: (123) -> -123
    - Currency symbols: $1,234.56 -> 1234.56
    - Percentage signs: 45% -> 0.45
    - Dashes/hyphens as zero: - -> 0
    - Text like 'None', 'N/A', etc. -> None
    
    Args:
        value: Value to clean
        handle_negatives: If True, convert (123) format to negative
        
    Returns:
        Float value or None if not convertible
    """
    if pd.isna(value) or value is None:
        return None
    
    # Already numeric
    if isinstance(value, (int, float)):
        return float(value)
    
    # Convert to string for processing
    value_str = str(value).strip()
    
    # Handle common text representations of missing values
    if value_str.lower() in ['', '-', '—', 'n/a', 'na', 'none', 'nil', 'not applicable']:
        return None
    
    # Check if value is in parentheses (negative)
    is_negative = False
    if handle_negatives and value_str.startswith('(') and value_str.endswith(')'):
        is_negative = True
        value_str = value_str[1:-1]
    
    # Remove currency symbols and common formatting
    value_str = re.sub(r'[$€£¥,\s]', '', value_str)
    
    # Handle percentage
    is_percentage = value_str.endswith('%')
    if is_percentage:
        value_str = value_str[:-1]
    
    try:
        numeric_value = float(value_str)
        
        if is_percentage:
            numeric_value = numeric_value / 100
        
        if is_negative:
            numeric_value = -numeric_value
        
        return numeric_value
    except (ValueError, TypeError):
        return None


def clean_numeric_column(series: pd.Series, handle_negatives: bool = True) -> pd.Series:
    """
    Clean an entire column of numeric values.
    
    Args:
        series: Pandas Series to clean
        handle_negatives: If True, convert (123) format to negative
        
    Returns:
        Cleaned Series with numeric values
    """
    return series.apply(lambda x: clean_numeric_value(x, handle_negatives))


def standardize_date(value: Any, output_format: str = '%Y-%m-%d') -> Optional[str]:
    """
    Convert various date formats to standardized format.
    
    Args:
        value: Date value (string, datetime, or pandas Timestamp)
        output_format: Desired output format (default: ISO format YYYY-MM-DD)
        
    Returns:
        Standardized date string or None if not convertible
    """
    if pd.isna(value) or value is None:
        return None
    
    # Already a datetime object
    if isinstance(value, (datetime, pd.Timestamp)):
        return value.strftime(output_format)
    
    # Try to parse string
    value_str = str(value).strip()
    
    if not value_str or value_str.lower() in ['n/a', 'na', 'none']:
        return None
    
    # Common date formats to try
    date_formats = [
        '%Y-%m-%d',           # 2024-01-15
        '%m/%d/%Y',           # 01/15/2024
        '%d/%m/%Y',           # 15/01/2024
        '%B %d, %Y',          # January 15, 2024
        '%b %d, %Y',          # Jan 15, 2024
        '%Y/%m/%d',           # 2024/01/15
        '%d-%m-%Y',           # 15-01-2024
        '%Y%m%d',             # 20240115
    ]
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(value_str, fmt)
            return dt.strftime(output_format)
        except ValueError:
            continue
    
    # Try pandas to_datetime as fallback
    try:
        dt = pd.to_datetime(value_str)
        return dt.strftime(output_format)
    except:
        return None


def handle_thousands_notation(value: float, in_thousands: bool = True) -> float:
    """
    Adjust values that are reported in thousands or millions.
    
    Args:
        value: Numeric value
        in_thousands: If True, multiply by 1000; if False, no change
        
    Returns:
        Adjusted value
    """
    if pd.isna(value):
        return value
    
    if in_thousands:
        return value * 1000
    
    return value


def remove_empty_rows_cols(df: pd.DataFrame, 
                          how: str = 'all',
                          threshold: Optional[int] = None) -> pd.DataFrame:
    """
    Remove empty or mostly empty rows and columns.
    
    Args:
        df: Input DataFrame
        how: 'all' to drop if all values are NaN, 'any' to drop if any NaN
        threshold: Minimum number of non-NaN values required to keep row/col
        
    Returns:
        Cleaned DataFrame
    """
    if df.empty:
        return df
    
    # Remove empty rows (use either how or thresh, not both)
    if threshold is not None:
        df = df.dropna(axis=0, thresh=threshold)
    else:
        df = df.dropna(axis=0, how=how)
    
    # Remove empty columns (use either how or thresh, not both)
    if threshold is not None:
        df = df.dropna(axis=1, thresh=threshold)
    else:
        df = df.dropna(axis=1, how=how)
    
    return df.reset_index(drop=True)


def standardize_column_names(df: pd.DataFrame, 
                             lowercase: bool = True,
                             replace_spaces: str = '_') -> pd.DataFrame:
    """
    Standardize column names for consistency.
    
    Args:
        df: Input DataFrame
        lowercase: Convert to lowercase
        replace_spaces: Character to replace spaces with (default: underscore)
        
    Returns:
        DataFrame with standardized column names
    """
    new_columns = []
    for col in df.columns:
        col_str = str(col).strip()
        
        if lowercase:
            col_str = col_str.lower()
        
        # Replace spaces
        if replace_spaces:
            col_str = col_str.replace(' ', replace_spaces)
        
        # Remove special characters
        col_str = re.sub(r'[^\w\s_-]', '', col_str)
        
        # Remove multiple underscores
        col_str = re.sub(r'_+', '_', col_str)
        
        # Remove leading/trailing underscores
        col_str = col_str.strip('_')
        
        new_columns.append(col_str)
    
    df.columns = new_columns
    return df


def flatten_multi_index_columns(df: pd.DataFrame, separator: str = '_') -> pd.DataFrame:
    """
    Flatten multi-index columns into single-level with combined names.
    
    Args:
        df: DataFrame with multi-index columns
        separator: Separator for combining index levels
        
    Returns:
        DataFrame with flattened columns
    """
    if not isinstance(df.columns, pd.MultiIndex):
        return df
    
    new_columns = []
    for col in df.columns:
        # Join non-empty parts of the multi-index
        parts = [str(part) for part in col if str(part) != '' and str(part) != 'nan']
        new_col = separator.join(parts)
        new_columns.append(new_col)
    
    df.columns = new_columns
    return df


def clean_whitespace(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean whitespace from string columns.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with cleaned strings
    """
    for col in df.columns:
        # Check if column contains strings
        if pd.api.types.is_object_dtype(df[col]):
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
    
    return df


def identify_header_row(df: pd.DataFrame, 
                       min_non_null_ratio: float = 0.5) -> Optional[int]:
    """
    Try to identify which row is the header in a messy table.
    
    Args:
        df: Input DataFrame
        min_non_null_ratio: Minimum ratio of non-null values for a row to be header
        
    Returns:
        Index of likely header row, or None if can't determine
    """
    for idx in range(min(10, len(df))):  # Check first 10 rows
        row = df.iloc[idx]
        non_null_ratio = row.notna().sum() / len(row)
        
        if non_null_ratio >= min_non_null_ratio:
            # Check if values are mostly strings (typical for headers)
            string_count = sum(isinstance(val, str) for val in row if pd.notna(val))
            if string_count / row.notna().sum() > 0.7:
                return idx
    
    return None


def merge_duplicate_columns(df: pd.DataFrame, suffix: str = '_dup') -> pd.DataFrame:
    """
    Handle duplicate column names by merging or renaming.
    
    Args:
        df: Input DataFrame
        suffix: Suffix to add to duplicate column names
        
    Returns:
        DataFrame with handled duplicates
    """
    # Find duplicate column names
    cols = pd.Series(df.columns)
    
    for dup in cols[cols.duplicated()].unique():
        # Find all columns with this name
        dup_indices = [i for i, col in enumerate(df.columns) if col == dup]
        
        # Rename subsequent duplicates
        for i, idx in enumerate(dup_indices[1:], 1):
            df.columns.values[idx] = f"{dup}{suffix}{i}"
    
    return df


def convert_to_proper_types(df: pd.DataFrame, 
                           numeric_cols: Optional[list] = None,
                           date_cols: Optional[list] = None) -> pd.DataFrame:
    """
    Convert DataFrame columns to appropriate data types.
    
    Args:
        df: Input DataFrame
        numeric_cols: List of columns to convert to numeric
        date_cols: List of columns to convert to datetime
        
    Returns:
        DataFrame with converted types
    """
    if numeric_cols:
        for col in numeric_cols:
            if col in df.columns:
                df[col] = clean_numeric_column(df[col])
    
    if date_cols:
        for col in date_cols:
            if col in df.columns:
                df[col] = df[col].apply(standardize_date)
    
    return df


def clean_financial_table(df: pd.DataFrame,
                         numeric_cols: Optional[list] = None,
                         in_thousands: bool = False) -> pd.DataFrame:
    """
    Apply common cleaning operations for financial tables.
    
    Args:
        df: Input DataFrame
        numeric_cols: List of columns that should be numeric
        in_thousands: If True, multiply numeric values by 1000
        
    Returns:
        Cleaned DataFrame
    """
    # Remove empty rows and columns
    df = remove_empty_rows_cols(df)
    
    # Clean whitespace
    df = clean_whitespace(df)
    
    # Standardize column names
    df = standardize_column_names(df)
    
    # Handle duplicate columns
    df = merge_duplicate_columns(df)
    
    # Convert numeric columns
    if numeric_cols:
        for col in numeric_cols:
            if col in df.columns:
                df[col] = clean_numeric_column(df[col])
                if in_thousands:
                    df[col] = df[col].apply(lambda x: handle_thousands_notation(x, True))
    else:
        # Try to auto-detect numeric columns
        for col in df.columns:
            # Sample first non-null value
            sample = df[col].dropna().head(1)
            if len(sample) > 0:
                val = sample.iloc[0]
                if isinstance(val, (int, float)) or (isinstance(val, str) and 
                    any(c.isdigit() for c in str(val))):
                    df[col] = clean_numeric_column(df[col])
    
    return df

