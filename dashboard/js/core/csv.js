/* CSV parser/serializer (UTF-8, ngoặc kép, BOM) */
window.FS = window.FS || {};
FS.csv = {
  parse(text) {
    text = text.replace(/^\uFEFF/, '');
    const rows = []; let row = [], f = '', q = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (q) { if (c === '"') { if (text[i + 1] === '"') { f += '"'; i++; } else q = false; } else f += c; }
      else if (c === '"') q = true;
      else if (c === ',') { row.push(f); f = ''; }
      else if (c === '\n') { row.push(f); rows.push(row); row = []; f = ''; }
      else if (c !== '\r') f += c;
    }
    if (f !== '' || row.length) { row.push(f); rows.push(row); }
    const headers = (rows.shift() || []).map(h => h.trim());
    return { headers, rows: rows.filter(r => r.length > 1 || r[0] !== '') };
  },
  toObjects(p, coerce = true) {
    return p.rows.map(r => { const o = {}; p.headers.forEach((h, i) => { o[h] = coerce ? FS.csv.coerce(h, r[i]) : (r[i] ?? ''); }); return o; });
  },
  coerce(h, v) {
    if (v === undefined || v === '') return null;
    if (/id$|_code$/i.test(h) || h === 'shift') return v;
    if (/^-?\d+(\.\d+)?$/.test(v)) return +v;
    if (v === 'True') return true; if (v === 'False') return false;
    return v;
  },
  stringify(rows, cols) {
    cols = cols || Object.keys(rows[0] || {});
    const e = v => { v = v == null ? '' : String(v); return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
    return '\uFEFF' + [cols.join(',')].concat(rows.map(r => cols.map(c => e(r[c])).join(','))).join('\n');
  },
  download(name, text, mime = 'text/csv;charset=utf-8') {
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([text], { type: mime })); a.download = name; a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 500);
  }
};
