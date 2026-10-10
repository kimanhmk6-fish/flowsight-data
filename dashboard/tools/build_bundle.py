"""Đóng gói CSV/JSON từ repo flowsight-data thành data/bundle.js (chạy offline qua file://).
Dùng: python tools/build_bundle.py <repo>/data"""
import sys, json, glob, os
src = sys.argv[1] if len(sys.argv) > 1 else '../flowsight-data/data'
out = {'csv': {}, 'json': {}}
for f in glob.glob(os.path.join(src, '*', '*')):
    n = os.path.splitext(os.path.basename(f))[0]
    if f.endswith('.csv'): out['csv'][n] = open(f, encoding='utf-8-sig').read()
    elif f.endswith('.json'): out['json'][n] = json.load(open(f, encoding='utf-8'))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'bundle.js'), 'w', encoding='utf-8').write('window.FS_BUNDLE=' + json.dumps(out, ensure_ascii=False) + ';')
print('OK', len(out['csv']), 'csv', len(out['json']), 'json')
