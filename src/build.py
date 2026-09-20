#!/usr/bin/env python3
"""src/data/*.txt から カード形式・穴埋め形式のHTMLと index.html を生成する。

データ形式:
  @meta タイトル|パンくず|導入文
  @group グループ名|グループ説明
  用語|説明|例(省略可)
"""
import glob, html, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "src", "data")

import json
# 分野ID -> (slug, 表示名)。1-5 は「計測・制御に関する理論」の単独ページ
PAGES = [("1-5", "measure", "計測・制御理論編"), (2, "algo", "アルゴリズムとプログラミング編"), (3, "processor", "コンピュータ構成要素編"),
    (4, "sysconf", "システム構成要素編"), (5, "software", "ソフトウェア編"), (6, "hardware", "ハードウェア編"),
    (7, "ui", "ユーザーインタフェース編"), (8, "media", "情報メディア編"), (9, "database", "データベース編"),
    (10, "network", "ネットワーク編"), (11, "security", "セキュリティ編"), (12, "sysdev", "システム開発技術編"),
    (13, "swmgmt", "ソフトウェア開発管理技術編"), (14, "project", "プロジェクトマネジメント編"), (15, "service", "サービスマネジメント編"),
    (16, "audit", "システム監査編"), (17, "sys-strategy", "システム戦略編"), (18, "sys-planning", "システム企画編"),
    (19, "biz-strategy", "経営戦略マネジメント編"), (20, "tech-strategy", "技術戦略マネジメント編"),
    (21, "industry", "ビジネスインダストリ編"), (22, "corporate", "企業活動編"), (23, "legal", "法務編")]
GROUPS = [("基礎理論", ["discrete-math", "applied-math", "info-theory", "comm-theory", "measure"]),
    ("アルゴリズムとプログラミング", ["algo"]), ("コンピュータシステム", ["processor", "sysconf", "software", "hardware"]),
    ("技術要素", ["ui", "media", "database", "network", "security"]), ("開発技術", ["sysdev", "swmgmt"]),
    ("マネジメント", ["project", "service", "audit"]), ("ストラテジ", ["sys-strategy", "sys-planning", "biz-strategy", "tech-strategy", "industry", "corporate", "legal"])]
HAND_NAMES = {"discrete-math": "離散数学編", "applied-math": "応用数学編", "info-theory": "情報理論編", "comm-theory": "通信理論編"}
HAND_MADE = set(HAND_NAMES)
NAMES = dict(HAND_NAMES, **{s: n for _, s, n in PAGES})
CATEGORIES = [(c, [(s, NAMES[s]) for s in ss]) for c, ss in GROUPS]
ALL = [x for _, items in CATEGORIES for x in items]

def esc(s): return html.escape(s, quote=False)

def css(kind):
    src = open(os.path.join(ROOT, f"comm-theory-{kind}.html"), encoding="utf-8").read()
    return re.search(r"<style>.*?</style>", src, re.S).group(0)

ALIAS = re.compile(r"^(.*。)([^。]+?)とも(?:いう|呼ばれる|言う|称される)。$")

def split_alias(desc):
    """説明末尾の「Xともいう。」を取り除き、(説明, 別名)を返す。別名は用語名の後ろに「用語(別名)」と表示する。"""
    m = ALIAS.match(desc)
    return (m.group(1), m.group(2)) if m else (desc, None)

def load_desc():
    d = {}
    for f in sorted(glob.glob(os.path.join(DATA, "desc", "*.txt"))):
        for line in open(f, encoding="utf-8"):
            p = line.rstrip("\n").split("|")
            if len(p) >= 2 and p[0]:
                text, alias = split_alias(p[1])
                d[p[0]] = (text, p[2] if len(p) > 2 and p[2] else None, alias)
    return d

def build_page_data(pid, slug, desc, structure, missing):
    cat = next(c for c in structure if c["id"] == (1 if pid == "1-5" else pid))
    subs = [x for x in cat["subs"] if pid != "1-5" or x["id"] == "1-5"]
    groups, seen = [], set()
    for sub in subs:
        terms = []
        for t, _ in sub["terms"]:
            if t in seen: continue
            seen.add(t)
            if t not in desc: missing.append(f"{slug}: {t}"); continue
            text, ex, alias = desc[t]
            terms.append((f"{t}({alias})" if alias else t, text, ex))
        groups.append((sub["name"], "", terms))
    if pid == "1-5":
        meta = ["計測・制御理論編", "基礎理論 > 計測・制御に関する理論", "基本情報技術者試験「基礎理論」の中の計測・制御に関する理論分野の用語集です。"]
    else:
        names = "、".join(x["name"] for x in subs)
        meta = [NAMES[slug], cat["name"], f"基本情報技術者試験「{cat['name']}」分野の用語集です。{names}を含みます。"]
    return meta, groups

def nav(slug, kind):
    i = [s for s, _ in ALL].index(slug)
    prev = ALL[i - 1] if i > 0 else None
    nxt = ALL[i + 1] if i + 1 < len(ALL) else None
    def cur(k): return ' aria-current="page"' if k == kind else ""
    out = ['    <nav class="page-nav" aria-label="ページ切り替え">',
           '      <div class="nav-group"><a href="index.html">目次</a></div>',
           '      <span class="nav-sep">|</span>',
           '      <div class="nav-group">',
           f'        <span class="nav-label">{esc(dict(ALL)[slug])}</span>',
           f'        <a href="{slug}-cards.html"{cur("cards")}>カード</a>',
           '        <span class="nav-sep">/</span>',
           f'        <a href="{slug}-quiz.html"{cur("quiz")}>穴埋め</a>', '      </div>']
    for lab, t in (("← 前", prev), ("次 →", nxt)):
        if t:
            out += ['      <span class="nav-sep">|</span>',
                    f'      <div class="nav-group"><a href="{t[0]}-{"cards" if kind=="cards" else "quiz"}.html">{lab}: {esc(t[1])}</a></div>']
    out.append('    </nav>')
    return "\n".join(out)

FOOT = '  <footer class="page-footer">出典: fe-siken.com「基本情報技術者試験ドットコム」の用語集構成(シラバスVer9.2)を参考に、説明文を平易な表現で独自に書き下ろして作成。</footer>'

def page(slug, kind, meta, groups):
    title, crumb, intro = meta
    n = sum(len(g[2]) for g in groups)
    q = kind == "quiz"
    h = [f'<title>{esc(title)}{"(穴埋め)" if q else ""} — 基本情報技術者試験 用語集</title>', css(kind), '<div class="page">',
         nav(slug, kind), '  <header class="masthead">',
         f'    <p class="breadcrumb">{esc(crumb)}{" &gt; 穴埋め問題" if q else ""}</p>',
         f'    <h1>{esc(title)}{"(穴埋め)" if q else ""}</h1>', '    <div class="meta-row">',
         f'      <span class="count-badge">{n} 語</span>',
         '      <span class="source-note">fe-siken.com 用語集(シラバスVer9.2)をもとに作成</span>', '    </div>']
    if not q: h.append(f'    <p class="intro">{esc(intro)}</p>')
    h.append('  </header>')
    for gn, gd, terms in groups:
        h += ['  <section class="group">', f'    <p class="group-label">{esc(gn)}</p>']
        if not q and gd: h.append(f'    <p class="group-desc">{esc(gd)}</p>')
        h.append('    <hr class="group-divider" />')
        h.append('    <div class="term-list">' if q else '    <dl class="term-list">')
        for t, d, e in terms:
            if q:
                h.append(f'      <p class="term-line"><span class="bullet">・</span>(　　　　　　　　) <span class="arrow">→</span>{esc(d)}{esc(e) if e else ""}</p>')
            else:
                h += ['      <div class="term-entry">',
                      f'        <dt class="term"><span class="arrow">・</span>{esc(t)}</dt>',
                      f'        <dd class="desc">{esc(d)}</dd>']
                if e: h.append(f'        <p class="example"><span class="ex-label">例</span>{esc(e)}</p>')
                h.append('      </div>')
        h += ['    </div>' if q else '    </dl>', '  </section>']
    h += [FOOT, '</div>']
    return "\n".join(h) + "\n"

PENTEST_DATA = os.path.join(ROOT, "src", "data", "pentest")
PENTEST_PAGES = [
    ("recon", "偵察・情報収集編"), ("web-attack", "Web攻撃編"), ("exploit-tools", "攻撃ツール・権限昇格編"),
    ("network", "ネットワーク・プロトコル編"), ("windows", "Windows/AD編"), ("macos", "macOS編"),
    ("forensics", "デジタルフォレンジック編"), ("malware", "マルウェア解析編"), ("crypto", "暗号・ハッシュ編"),
    ("social", "ソーシャルエンジニアリング編"), ("ai-security", "AIセキュリティ編"), ("framework", "標準・組織・資格編"),
]

def pentest_counts():
    counts = {}
    for slug, _ in PENTEST_PAGES:
        p = os.path.join(PENTEST_DATA, f"{slug}.txt")
        counts[slug] = sum(1 for l in open(p, encoding="utf-8") if l.strip()) if os.path.exists(p) else 0
    return counts

def index(counts):
    total = sum(counts.values())
    rows = []
    for cat, items in CATEGORIES:
        rows.append(f'  <section class="group"><p class="group-label">{esc(cat)}</p><hr class="group-divider" /><div class="term-list">')
        for s, name in items:
            rows.append(f'    <p class="term-line"><span class="bullet">・</span><strong>{esc(name)}</strong>({counts[s]}語) <span class="arrow">→</span>'
                        f'<a href="{s}-cards.html">カード</a> / <a href="{s}-quiz.html">穴埋め</a></p>')
        rows.append('  </div></section>')
    rows.append('  <section class="group"><p class="group-label">計算問題</p><hr class="group-divider" /><div class="term-list"><p class="term-line"><span class="bullet">・</span><strong>計算のやり方</strong> <span class="arrow">→</span><a href="calc-methods.html">公式と例題</a> / <a href="formulas.html">公式の早見表</a></p></div></section>')
    pcounts = pentest_counts()
    ptotal = sum(pcounts.values())
    rows.append(f'  <section class="group"><p class="group-label">セキュリティ実践編({ptotal}語)</p>'
                 '<p class="group-desc">基本情報技術者試験のシラバスとは別に、利用者が学習用にまとめたメモをもとに作成した用語集です。</p>'
                 '<hr class="group-divider" /><div class="term-list">')
    for s, name in PENTEST_PAGES:
        rows.append(f'    <p class="term-line"><span class="bullet">・</span><strong>{esc(name)}</strong>({pcounts[s]}語) <span class="arrow">→</span>'
                    f'<a href="pentest-{s}-cards.html">カード</a> / <a href="pentest-{s}-quiz.html">穴埋め</a></p>')
    rows.append('  </div></section>')
    total += ptotal
    for slug, title, note in (("git", "Git編", ""), ("docker", "Docker編", "")):
        gpath = os.path.join(ROOT, "src", "data", slug, f"{slug}.txt")
        gcount = sum(1 for l in open(gpath, encoding="utf-8") if l.strip())
        rows.append(f'  <section class="group"><p class="group-label">{title}({gcount}語)</p>'
                    '<p class="group-desc">こちらも利用者が学習用にまとめたメモをもとにした用語集で、基本情報技術者試験のシラバスとは別です。</p>'
                    '<hr class="group-divider" /><div class="term-list">'
                    f'<p class="term-line"><span class="bullet">・</span><strong>{title}</strong>({gcount}語) <span class="arrow">→</span>'
                    f'<a href="{slug}-cards.html">カード</a> / <a href="{slug}-quiz.html">穴埋め</a></p></div></section>')
        total += gcount
    style = css("quiz").replace("</style>", "  a { color: var(--accent); }\n</style>")
    return (f'<title>目次 — 基本情報技術者試験 用語集</title>\n{style}\n<div class="page">\n  <header class="masthead">\n'
            f'    <p class="breadcrumb">fe-exam-glossary</p>\n    <h1>基本情報技術者試験 用語集</h1>\n    <div class="meta-row">'
            f'<span class="count-badge">{total} 語</span><span class="source-note">カード形式・穴埋め形式の2種類</span></div>\n  </header>\n'
            + "\n".join(rows) + f'\n{FOOT}\n</div>\n')

def main():
    structure = json.load(open(os.path.join(DATA, "..", "site", "structure.json"), encoding="utf-8"))
    desc, missing, counts = load_desc(), [], {}
    for s in HAND_MADE:
        src = open(os.path.join(ROOT, f"{s}-cards.html"), encoding="utf-8").read()
        counts[s] = int(re.search(r'count-badge">(\d+)', src).group(1))
    for pid, slug, _ in PAGES:
        meta, groups = build_page_data(pid, slug, desc, structure, missing)
        counts[slug] = sum(len(g[2]) for g in groups)
        if missing: continue
        for kind in ("cards", "quiz"):
            open(os.path.join(ROOT, f"{slug}-{kind}.html"), "w", encoding="utf-8").write(page(slug, kind, meta, groups))
    if missing:
        open(os.path.join(ROOT, "src", "missing.txt"), "w", encoding="utf-8").write("\n".join(missing) + "\n")
        sys.exit(f"説明が未作成の用語が {len(missing)} 件あります(src/missing.txt)")
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(index(counts))
    print(counts, sum(counts.values()))

main()
