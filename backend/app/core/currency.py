import re
from typing import Any, Union
from decimal import Decimal

def to_indian_format(val_str: str) -> str:
    """
    Converts a raw or standard comma number string to Indian grouping (e.g. 15,00,000.00).
    """
    clean = val_str.replace(',', '').strip()
    try:
        parts = clean.split('.')
        int_part = parts[0]
        dec_part = '.' + parts[1] if len(parts) > 1 else ''
        if len(int_part) <= 3:
            return int_part + dec_part
        last_three = int_part[-3:]
        remaining = int_part[:-3]
        groups = []
        while len(remaining) > 2:
            groups.append(remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.append(remaining)
        groups.reverse()
        return ','.join(groups) + ',' + last_three + dec_part
    except Exception:
        return val_str

def format_inr(val: Union[float, int, Decimal, str, None], include_decimals: bool = True) -> str:
    """
    Formats a numeric value into the Indian Numbering System with Rupee symbol (e.g. ₹15,00,000.00).
    """
    if val is None:
        return '₹0.00' if include_decimals else '₹0'
    try:
        num = float(val)
    except (ValueError, TypeError):
        return '₹0.00' if include_decimals else '₹0'

    is_negative = num < 0
    num = abs(num)

    if include_decimals:
        formatted_dec = f'{num:.2f}'
        int_part, dec_part = formatted_dec.split('.')
    else:
        int_part = str(int(round(num)))
        dec_part = ''

    if len(int_part) <= 3:
        res = int_part
    else:
        last_three = int_part[-3:]
        remaining = int_part[:-3]
        groups = []
        while len(remaining) > 2:
            groups.append(remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.append(remaining)
        groups.reverse()
        res = ','.join(groups) + ',' + last_three

    if include_decimals:
        res = f'{res}.{dec_part}'

    prefix = '-₹' if is_negative else '₹'
    return f'{prefix}{res}'

def sanitize_indian_currency_in_text(text: str) -> str:
    """
    Post-processes natural language LLM output and tables to ensure all currency
    and Rupee figures strictly adhere to the Indian Numbering System.
    """
    if not text:
        return text

    def replacer(match):
        prefix = match.group(1)
        number = match.group(2)
        return f'{prefix}{to_indian_format(number)}'

    # Match ₹1,500,000 or ₹ 1500000 or Rs. 1,500,000 or INR 1,500,000
    pattern = r'([₹]|Rs\.?\s*|INR\s*)([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)'
    return re.sub(pattern, replacer, text)
