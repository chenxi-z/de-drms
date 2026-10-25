#!/usr/bin/env python3
"""import_bib_to_zotero.py — 把 paper/literature.bib 直写进 Zotero 本地库（须先退出 Zotero）
用法：
  python3 import_bib_to_zotero.py --only pavan2011   # 试写单条
  python3 import_bib_to_zotero.py                    # 全量（自动跳过已存在 DOI/题名）
建目录树：P1 论文文献 → H1..H6 六个子集；条目加标签 P1论文文献/P1-Hx/[本地PDF]。
"""
import sqlite3, re, sys, random, datetime, pathlib

BIB = '/media/anning/data/Project/DE-DRMS/paper/literature.bib'
DB = '/home/anning/Zotero/zotero.sqlite'
NOW = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
KEYCHARS = '23456789ABCDEFGHIJKLMNPQRSTUVWXYZ'
TYPEMAP = {'article': 'journalArticle', 'techreport': 'report', 'phdthesis': 'thesis',
           'manual': 'document', 'misc': 'document'}
AXIS_NAMES = {'H1': 'H1 ΣΔ-AAF', 'H2': 'H2 差分CMRR', 'H3': 'H3 CT-ΣΔ', 'H4': 'H4 选型方法学',
              'H5': 'H5 kickback', 'H6': 'H6 CNT-SHM'}

def parse_bib(path):
    axis, entries, cur = None, [], None
    for ln in pathlib.Path(path).read_text().splitlines():
        m = re.match(r'^%\s*\[(H\d)\]', ln)
        if m: axis = m.group(1)
        m = re.match(r'^%=\+\s*=*\s*(H\d)', ln)
        if ln.startswith('%') and '= ' in ln and not m:
            mm = re.search(r'(H\d)', ln)
            if mm and ('=====' in ln): axis = mm.group(1)
        if ln.startswith('@'):
            if cur: entries.append(cur)
            m = re.match(r'@(\w+)\{([^,]+),', ln)
            cur = {'type': m.group(1).lower(), 'key': m.group(2), 'axis': axis, 'f': {}}
            continue
        if cur is not None:
            m = re.match(r'^\s*(\w+)\s*=\s*(.*)$', ln)
            if m:
                val = m.group(2).strip().rstrip(',').strip()
                val = val[1:-1] if val.startswith('{') and val.endswith('}') else val
                cur['f'][m.group(1)] = val.replace('\\&', '&').replace('\\%', '%').replace('\\_', '_')
            elif ln.strip() == '}' or ln.strip() == '':
                if ln.strip() == '}':
                    entries.append(cur); cur = None
    if cur: entries.append(cur)
    return entries

def main():
    only = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else None
    entries = parse_bib(BIB)
    if only:
        entries = [e for e in entries if e['key'] == only]
    print(f"bib 解析 {len(entries)} 条（axis 未知 {sum(1 for e in entries if not e['axis'])} 条）")
    db = sqlite3.connect(DB)
    c = db.cursor()
    # 归一化样例
    norm_val = c.execute("SELECT value, valueNormalized FROM itemDataValues WHERE valueNormalized!='' LIMIT 1").fetchone()
    print("valueNormalized 样例:", norm_val)
    typeids = dict(c.execute("SELECT typeName, itemTypeID FROM itemTypes"))
    allowed = {}  # typeName -> set(fieldID)
    for tn in set(TYPEMAP.values()):
        allowed[tn] = {r[0] for r in c.execute(
            "SELECT fieldID FROM itemTypeFields WHERE itemTypeID=?", (typeids[tn],))}
    fids = {}
    for fn in ('title', 'publicationTitle', 'date', 'DOI', 'url', 'volume', 'pages', 'extra',
               'institution', 'university', 'reportType'):
        r = c.execute("SELECT fieldID FROM fields WHERE fieldName=?", (fn,)).fetchone()
        if r: fids[fn] = r[0]
    # 已存在（DOI 与题名，防重）
    have_doi = {r[0].lower() for r in c.execute(
        "SELECT idv.value FROM itemData id JOIN itemDataValues idv USING(valueID) WHERE id.fieldID=?", (fids['DOI'],))}
    have_title = {r[0].strip().lower() for r in c.execute(
        "SELECT idv.value FROM itemData id JOIN itemDataValues idv USING(valueID) WHERE id.fieldID=?", (fids['title'],))}
    def newkey():
        while True:
            k = ''.join(random.choice(KEYCHARS) for _ in range(8))
            if not c.execute("SELECT 1 FROM items WHERE key=? UNION SELECT 1 FROM collections WHERE key=?", (k, k)).fetchone():
                return k
    def get_or_val(v):
        r = c.execute("SELECT valueID FROM itemDataValues WHERE value=?", (v,)).fetchone()
        if r: return r[0]
        cur = c.execute("INSERT INTO itemDataValues(value, valueNormalized) VALUES(?,?)", (v, v.strip().lower()))
        return cur.lastrowid
    def get_or_creator(first, last, mode):
        r = c.execute("SELECT creatorID FROM creators WHERE IFNULL(firstName,'')=? AND lastName=? AND fieldMode=?",
                      (first or '', last, mode)).fetchone()
        if r: return r[0]
        cur = c.execute("INSERT INTO creators(firstName, lastName, fieldMode, firstNameNormalized, lastNameNormalized) VALUES(?,?,?,?,?)",
                        (first or '', last, mode, (first or '').strip().lower(), last.strip().lower()))
        return cur.lastrowid
    def get_or_tag(name):
        r = c.execute("SELECT tagID FROM tags WHERE name=?", (name,)).fetchone()
        if r: return r[0]
        cur = c.execute("INSERT INTO tags(name, nameNormalized) VALUES(?,?)", (name, name.strip().lower()))
        return cur.lastrowid
    # 目录树
    coll_ids = {}
    r = c.execute("SELECT collectionID FROM collections WHERE collectionName='P1 论文文献' AND libraryID=1").fetchone()
    if r:
        root = r[0]
    else:
        cur = c.execute("INSERT INTO collections(collectionName, parentCollectionID, clientDateModified, libraryID, key, version, clientVersion, synced) VALUES(?,NULL,?,1,?,0,0,0)",
                  ('P1 论文文献', NOW, newkey()))
        root = cur.lastrowid
    for ax, nm in AXIS_NAMES.items():
        r = c.execute("SELECT collectionID FROM collections WHERE collectionName=? AND parentCollectionID=?", (nm, root)).fetchone()
        if r: coll_ids[ax] = r[0]
        else:
            cur = c.execute("INSERT INTO collections(collectionName, parentCollectionID, clientDateModified, libraryID, key, version, clientVersion, synced) VALUES(?,?,?,?,?,0,0,0)",
                      (nm, root, NOW, 1, newkey()))
            coll_ids[ax] = cur.lastrowid
    imported = skipped = 0
    for e in entries:
        tn = TYPEMAP.get(e['type'], 'journalArticle')
        f = e['f']
        doi = (f.get('doi') or '').strip()
        title = (f.get('title') or '').strip()
        if not title:
            print(f"跳过（无题名）{e['key']}"); continue
        if doi and doi.lower() in have_doi or title.strip().lower() in have_title:
            print(f"跳过（已存在）{e['key']}"); skipped += 1; continue
        cur = c.execute("INSERT INTO items(itemTypeID, dateAdded, dateModified, clientDateModified, libraryID, key, version, clientVersion, synced) VALUES(?,?,?,?,1,?,0,0,0)",
                  (typeids[tn], NOW, NOW, NOW, newkey()))
        iid = cur.lastrowid
        def setf(name, val):
            if not val: return
            fid = fids.get(name)
            if fid is None or fid not in allowed[tn]:  # 类型不支持的塞 extra
                if name in ('institution', 'university', 'reportType'):
                    f['extra'] = (f.get('extra', '') + f'\n{name}: {val}').strip()
                return
            c.execute("INSERT INTO itemData(itemID, fieldID, valueID) VALUES(?,?,?)", (iid, fid, get_or_val(val)))
        setf('title', title)
        setf('publicationTitle', f.get('journal'))
        setf('date', f.get('year') or '')
        setf('DOI', doi)
        setf('url', f.get('url'))
        setf('volume', f.get('volume'))
        setf('pages', f.get('pages'))
        if tn == 'report': setf('institution', f.get('institution'))
        if tn == 'thesis': setf('university', f.get('school') or f.get('institution'))
        if f.get('note'): f['extra'] = (f.get('extra', '') + f"\n{f['note']}").strip()
        if f.get('extra'): setf('extra', f['extra'])
        for i, au in enumerate([a.strip() for a in (f.get('author') or '').split(' and ') if a.strip()]):
            if au.startswith('{') and au.endswith('}'):
                cid = get_or_creator('', au[1:-1], 1)
            elif ',' in au:
                last, first = [x.strip() for x in au.split(',', 1)]
                cid = get_or_creator(first, last, 0)
            else:
                cid = get_or_creator('', au, 1)
            c.execute("INSERT INTO itemCreators(itemID, creatorID, creatorTypeID, orderIndex) VALUES(?,?,?,?)",
                      (iid, cid, 10, i))
        for tag in ['P1论文文献'] + ([f'P1-{e["axis"]}'] if e['axis'] else []) + (['本地PDF'] if '本地' in (f.get('note') or '') else []):
            c.execute("INSERT INTO itemTags(itemID, tagID, type) VALUES(?,?,0)", (iid, get_or_tag(tag)))
        ax = e['axis'] or 'H1'
        c.execute("INSERT INTO collectionItems(collectionID, itemID, orderIndex) VALUES(?,?,0)",
                  (coll_ids[ax], iid))
        imported += 1
    db.commit()
    print(f"完成：导入 {imported}，跳过 {skipped}；目录树 root={root} {coll_ids}")

if __name__ == '__main__':
    main()
