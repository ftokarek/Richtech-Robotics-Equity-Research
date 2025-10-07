

import pandas as pd
import numpy as np
import re
from datetime import datetime
from typing import Any, Union, Optional


def clean_numeric_value(value: Any, handle_negatives: bool = True) -> Optional[float]:
    
    if pd.isna(value) or value is None:
        return None
    
    
    if isinstance(value, (int, float)):
        return float(value)
    
    
    value_str = str(value).strip()
    
    
    if value_str.lower() in ['', '-', '—', 'n/a', 'na', 'none', 'nil', 'not applicable']:
        return None
    
    
    is_negative = False
    if handle_negatives and value_str.startswith('(') and value_str.endswith(')'):
        is_negative = True
        value_str = value_str[1:-1]
    
    
    value_str = re.sub(r'[$€£¥,\s]', '', value_str)
    
    
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
    
    return series.apply(lambda x: clean_numeric_value(x, handle_negatives))


def standardize_date(value: Any, output_format: str = '%Y-%m-%d') -> Optional[str]:
    
    if pd.isna(value) or value is None:
        return None
    
    
    if isinstance(value, (datetime, pd.Timestamp)):
        return value.strftime(output_format)
    
    
    value_str = str(value).strip()
    
    if not value_str or value_str.lower() in ['n/a', 'na', 'none']:
        return None
    
    
    date_formats = [
        '%Y-%m-%d',           
        '%m/%d/%Y',           
        '%d/%m/%Y',           
        '%B %d, %Y',          
        '%b %d, %Y',          
        '%Y/%m/%d',           
        '%d-%m-%Y',           
        '%Y%m%d',             
    ]
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(value_str, fmt)
            return dt.strftime(output_format)
        except ValueError:
            continue
    
    
    try:
        dt = pd.to_datetime(value_str)
        return dt.strftime(output_format)
    except:
        return None


def handle_thousands_notation(value: float, in_thousands: bool = True) -> float:
    
    if pd.isna(value):
        return value
    
    if in_thousands:
        return value * 1000
    
    return value


def remove_empty_rows_cols(df: pd.DataFrame, 
                          how: str = 'all',
                          threshold: Optional[int] = None) -> pd.DataFrame:
    
    if df.empty:
        return df
    
    
    if threshold is not None:
        df = df.dropna(axis=0, thresh=threshold)
    else:
        df = df.dropna(axis=0, how=how)
    
    
    if threshold is not None:
        df = df.dropna(axis=1, thresh=threshold)
    else:
        df = df.dropna(axis=1, how=how)
    
    return df.reset_index(drop=True)


def standardize_column_names(df: pd.DataFrame, 
                             lowercase: bool = True,
                             replace_spaces: str = '_') -> pd.DataFrame:
    
    new_columns = []
    for col in df.columns:
        col_str = str(col).strip()
        
        if lowercase:
            col_str = col_str.lower()
        
        
        if replace_spaces:
            col_str = col_str.replace(' ', replace_spaces)
        
        
        col_str = re.sub(r'[^\w\s_-]', '', col_str)
        
        
        col_str = re.sub(r'_+', '_', col_str)
        
        
        col_str = col_str.strip('_')
        
        new_columns.append(col_str)
    
    df.columns = new_columns
    return df


def flatten_multi_index_columns(df: pd.DataFrame, separator: str = '_') -> pd.DataFrame:
    
    if not isinstance(df.columns, pd.MultiIndex):
        return df
    
    new_columns = []
    for col in df.columns:
        
        parts = [str(part) for part in col if str(part) != '' and str(part) != 'nan']
        new_col = separator.join(parts)
        new_columns.append(new_col)
    
    df.columns = new_columns
    return df


def clean_whitespace(df: pd.DataFrame) -> pd.DataFrame:
    
    for col in df.columns:
        
        if pd.api.types.is_object_dtype(df[col]):
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
    
    return df


def identify_header_row(df: pd.DataFrame, 
                       min_non_null_ratio: float = 0.5) -> Optional[int]:
    
    for idx in range(min(10, len(df))):  
        row = df.iloc[idx]
        non_null_ratio = row.notna().sum() / len(row)
        
        if non_null_ratio >= min_non_null_ratio:
            
            string_count = sum(isinstance(val, str) for val in row if pd.notna(val))
            if string_count / row.notna().sum() > 0.7:
                return idx
    
    return None


def merge_duplicate_columns(df: pd.DataFrame, suffix: str = '_dup') -> pd.DataFrame:
    
    
    cols = pd.Series(df.columns)
    
    for dup in cols[cols.duplicated()].unique():
        
        dup_indices = [i for i, col in enumerate(df.columns) if col == dup]
        
        
        for i, idx in enumerate(dup_indices[1:], 1):
            df.columns.values[idx] = f"{dup}{suffix}{i}"
    
    return df


def convert_to_proper_types(df: pd.DataFrame, 
                           numeric_cols: Optional[list] = None,
                           date_cols: Optional[list] = None) -> pd.DataFrame:
    
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
    
    
    df = remove_empty_rows_cols(df)
    
    
    df = clean_whitespace(df)
    
    
    df = standardize_column_names(df)
    
    
    df = merge_duplicate_columns(df)
    
    
    if numeric_cols:
        for col in numeric_cols:
            if col in df.columns:
                df[col] = clean_numeric_column(df[col])
                if in_thousands:
                    df[col] = df[col].apply(lambda x: handle_thousands_notation(x, True))
    else:
        
        for col in df.columns:
            
            sample = df[col].dropna().head(1)
            if len(sample) > 0:
                val = sample.iloc[0]
                if isinstance(val, (int, float)) or (isinstance(val, str) and 
                    any(c.isdigit() for c in str(val))):
                    df[col] = clean_numeric_column(df[col])
    
    return df

