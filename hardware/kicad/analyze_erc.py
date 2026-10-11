with open('alarm_clock_v1-erc.rpt', 'r', encoding='utf-8') as f:
    text = f.read()

import re
errors = re.findall(r'\[([^\]]+)\]:[^\n]+\n\s+;\s+error', text)
warnings = re.findall(r'\[([^\]]+)\]:[^\n]+\n\s+;\s+warning', text)

from collections import Counter
print("ERRORS:", Counter(errors))
print("WARNINGS:", Counter(warnings))
