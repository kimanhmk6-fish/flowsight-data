"""Gộp toàn bộ CSS/JS/dữ liệu vào 1 tệp flowsight.html (mở thẳng bằng trình duyệt, không cần thư mục kèm theo)."""
import re, os
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
rd = lambda p: open(os.path.join(root, p), encoding='utf-8').read()
h = rd('index.html')
h = h.replace('<link rel="stylesheet" href="css/styles.css">', '<style>' + rd('css/styles.css') + '</style>')
def inline_script(m):
    src = m.group(1)
    if src.startswith('http://') or src.startswith('https://') or src.startswith('//'):
        return m.group(0)  # giữ nguyên CDN external
    return '<script>' + rd(src).replace('</script', '<\\/script') + '</script>'
h = re.sub(r'<script src="([^"]+)"></script>', inline_script, h)
open(os.path.join(root, 'flowsight.html'), 'w', encoding='utf-8').write(h)
print('OK', len(h) // 1024, 'KB')
