# -*- coding: utf-8 -*-
# 修复脚本：把 s5 的 -20 改成 -50
with open('/workspace/skills/astock-report/scripts/send_evening_report.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('elif delta >= -20: s5, d5 = 5,  f"两融较上日{delta:.1f}亿，轻微缩减"', 'elif delta >= -50: s5, d5 = 5,  f"两融较上日{delta:.1f}亿，轻微缩减"')
with open('/workspace/skills/astock-report/scripts/send_evening_report.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('done')
