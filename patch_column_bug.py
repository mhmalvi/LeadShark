#!/usr/bin/env python3
"""
Patch the column range bug in smart_column_enricher.py
"""

import re

file_path = "smart_column_enricher.py"

# Read file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add helper method after __init__ method
init_pattern = r'(        self\.logger = logging\.getLogger\(__name__\)\n    \n)'
helper_method = r'''\1    @staticmethod
    def _col_to_letter(n: int) -> str:
        """Convert column index (0-based) to Excel column letter (A, B, ..., Z, AA, AB, ...)"""
        result = ""
        while n >= 0:
            result = chr(65 + (n % 26)) + result
            n = n // 26 - 1
            if n < 0:
                break
        return result

'''

content = re.sub(init_pattern, helper_method, content)

# Fix the buggy line
old_pattern = r"                cell_range = f'A\{row_idx\}:\{chr\(65 \+ len\(row\) - 1\)\}\{row_idx\}'"
new_pattern = r"                last_col = self._col_to_letter(len(row) - 1)\n                cell_range = f'A{row_idx}:{last_col}{row_idx}'"

content = re.sub(old_pattern, new_pattern, content)

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Patched smart_column_enricher.py successfully!")
print("   - Added _col_to_letter() helper method")
print("   - Fixed cell_range calculation to handle columns beyond Z")