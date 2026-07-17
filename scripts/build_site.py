#!/usr/bin/env python3
"""Build a corporate-quality static GitHub Pages site for the Engineering Doctrine
from the DESIGNATED SOURCE (.Doctrine/ playbooks + roles + skills + README), with
fail-closed gates -- a reference instance of the Web Designer role + skills/web-
design.md + skills/web-publishing.md applied to this repo itself.

    python scripts/build_site.py <out_dir>

Design (per web-design): a full-width landing (sticky header, hero + logo,
features grid, stats, CTA, footer) plus a docs section (sidebar) for every role,
skill, and playbook. Self-contained -- embedded CSS, an inline dark-mode toggle,
no CDN; renders offline. Copies repo `images/` so the real logo resolves.
Publishes a DESIGNED source only; the secret-scan looks for credential PATTERNS,
not the word "secret"; exits non-zero if the gate blocks. Writes `.nojekyll`.
ASCII-only console output.
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

import markdown

CSS = """
:root{--bg:#ffffff;--fg:#1f2430;--soft:#5b6472;--navy:#1a2b5e;--accent:#e8642c;
--line:#e4e7ee;--card:#fbfcfe;--code:#f4f5f9;--hero:linear-gradient(160deg,#f3f6fd,#fff 60%)}
:root[data-theme=dark]{--bg:#0f1420;--fg:#e6e9f0;--soft:#9aa4b8;--navy:#9fb4f0;--line:#26304a;--card:#161d2e;--code:#131a2a;--hero:linear-gradient(160deg,#141c2e,#0f1420 60%)}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0f1420;--fg:#e6e9f0;--soft:#9aa4b8;--navy:#9fb4f0;--line:#26304a;--card:#161d2e;--code:#131a2a;--hero:linear-gradient(160deg,#141c2e,#0f1420 60%)}}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--fg);background:var(--bg)}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
/* header */
header.top{position:sticky;top:0;z-index:20;display:flex;align-items:center;gap:1rem;padding:.7rem 1.5rem;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
header.top .brand{display:flex;align-items:center;gap:.5rem;font-weight:800;color:var(--navy);font-size:1.02rem}
header.top .brand .dot{width:12px;height:12px;border-radius:3px;background:var(--accent)}
header.top nav{margin-left:auto;display:flex;gap:1.1rem;align-items:center}
header.top nav a{color:var(--fg);font-size:.9rem;font-weight:500}
header.top .tg{cursor:pointer;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:8px;padding:.25rem .55rem;font-size:.9rem}
/* hero */
.hero{background:var(--hero);border-bottom:1px solid var(--line);text-align:center;padding:3.2rem 1.5rem 2.6rem}
.hero img{max-width:300px;height:auto}
.hero .wordmark{font-size:2.4rem;font-weight:800;color:var(--navy)}
.hero .tag{font-size:1.2rem;color:var(--soft);max-width:600px;margin:1rem auto 0}
.hero .cta{margin-top:1.5rem;display:flex;gap:.7rem;justify-content:center;flex-wrap:wrap}
.btn{display:inline-block;padding:.6rem 1.2rem;border-radius:9px;font-weight:600;font-size:.92rem}
.btn.p{background:var(--navy);color:#fff}.btn.p:hover{text-decoration:none;opacity:.92}
.btn.s{border:1px solid var(--line);color:var(--fg);background:var(--card)}.btn.s:hover{text-decoration:none;border-color:var(--navy)}
.ver{display:inline-block;margin-top:1rem;font-size:.76rem;color:#fff;background:var(--accent);padding:.2rem .7rem;border-radius:20px}
/* sections */
.section{max-width:1040px;margin:0 auto;padding:2.6rem 1.5rem}
.section h2{color:var(--navy);text-align:center;font-size:1.6rem;margin:0 0 .3rem}
.section .sub{color:var(--soft);text-align:center;margin:0 auto 1.8rem;max-width:560px}
.stats{display:flex;gap:1rem;justify-content:center;flex-wrap:wrap}
.stat{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:1rem 1.4rem;text-align:center;min-width:120px}
.stat b{display:block;font-size:1.8rem;color:var(--navy);line-height:1.1}
.stat span{font-size:.74rem;color:var(--soft);text-transform:uppercase;letter-spacing:.05em}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:1rem}
.feat{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:1.2rem}
.feat b{color:var(--navy);display:block;margin-bottom:.35rem;font-size:1.02rem}
.feat span{color:var(--soft);font-size:.92rem}
.card{display:block;border:1px solid var(--line);border-radius:10px;padding:.8rem 1rem;background:var(--card);color:var(--fg);transition:.15s}
.card:hover{border-color:var(--navy);box-shadow:0 4px 14px rgba(26,43,94,.1);transform:translateY(-1px);text-decoration:none}
.card b{color:var(--navy);display:block}
footer.ft{border-top:1px solid var(--line);text-align:center;padding:2rem 1.5rem;color:var(--soft);font-size:.86rem}
footer.ft a{color:var(--soft)}
/* docs layout */
.wrap{display:flex;max-width:1180px;margin:0 auto}
aside{width:250px;flex:0 0 250px;border-right:1px solid var(--line);padding:1.4rem 1rem 3rem;position:sticky;top:56px;height:calc(100vh - 56px);overflow:auto}
aside h3{font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;color:var(--soft);margin:1.2rem 0 .35rem}
aside a{display:block;color:var(--fg);padding:.1rem .4rem;font-size:.85rem;border-radius:5px}
aside a:hover{background:var(--code);text-decoration:none}
main.doc{flex:1;padding:2rem 3rem 4rem;max-width:860px;overflow:auto}
main.doc h1{color:var(--navy);font-size:1.9rem;border-bottom:2px solid var(--line);padding-bottom:.35rem;margin-top:0}
main.doc h2{color:var(--navy);margin-top:2.2rem}main.doc h3{color:var(--navy)}
main.doc a{color:var(--accent)}
code{background:var(--code);padding:.12rem .35rem;border-radius:4px;font-size:.87em}
pre{background:var(--code);padding:1rem 1.1rem;border-radius:8px;overflow:auto;border:1px solid var(--line);line-height:1.5}
pre code{background:none;padding:0}
main.doc table{border-collapse:collapse;width:100%;margin:1rem 0;font-size:.92em}
main.doc th,main.doc td{border:1px solid var(--line);padding:.45rem .7rem;text-align:left}
main.doc th{background:var(--code);color:var(--navy)}
main.doc blockquote{border-left:3px solid var(--accent);margin:1rem 0;padding:.3rem 1rem;color:var(--soft)}
@media(max-width:820px){.wrap{flex-direction:column}aside{width:auto;height:auto;position:static;border-right:0;border-bottom:1px solid var(--line)}main.doc{padding:1.5rem}header.top nav a:not(.tg){display:none}}
"""

THEME_JS = (
    "<script>(function(){var k='dtheme',s=localStorage.getItem(k);"
    "if(s)document.documentElement.dataset.theme=s;"
    "window.__t=function(){var d=document.documentElement,"
    "n=(d.dataset.theme==='dark'?'light':'dark');"
    "d.dataset.theme=n;localStorage.setItem(k,n)};})();</script>")

REPO = "https://github.com/aroora-ai-labs/doctrine"

SECRET_PATTERNS = [
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "private-key"),
    (r"AKIA[0-9A-Z]{16}", "aws-access-key"),
    (r"gh[pousr]_[A-Za-z0-9]{36,}", "github-token"),
    (r"xox[baprs]-[A-Za-z0-9-]{10,}", "slack-token"),
]


def render(md_text: str) -> str:
    return markdown.markdown(
        md_text, extensions=["fenced_code", "tables", "toc", "sane_lists"])


def pretty(stem: str) -> str:
    return re.sub(r"^\d+-", "", stem).replace("-", " ").title()


def version(src: Path) -> str:
    law = src / ".Doctrine.md"
    if law.exists():
        m = re.search(r"Doctrine v([\d.]+)", law.read_text("utf-8"))
        if m:
            return m.group(1)
    return ""


def header() -> str:
    return (
        '<header class="top"><span class="brand"><span class="dot"></span>'
        "Engineering Doctrine</span><nav>"
        '<a href="index.html">Home</a>'
        '<a href="doc-01-workflow.html">Docs</a>'
        f'<a href="{REPO}">GitHub</a>'
        "<button class=\"tg\" onclick=\"__t()\" title=\"Toggle theme\">"
        "&#9681;</button></nav></header>")


def footer(ver: str) -> str:
    v = f" &middot; v{ver}" if ver else ""
    return (
        f'<footer class="ft">Engineering Doctrine{v} &middot; '
        f'<a href="{REPO}">GitHub</a> &middot; MIT &middot; '
        "built with the web-design skill</footer>")


def shell(title: str, inner: str, ver: str) -> str:
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{title} - Engineering Doctrine</title>{THEME_JS}"
        f"<style>{CSS}</style></head><body>{header()}{inner}"
        f"{footer(ver)}</body></html>\n")


def features(src: Path) -> str:
    readme = src / "README.md"
    if not readme.exists():
        return ""
    cards = []
    for m in re.finditer(r"^- \*\*(.+?)\*\*[\s—-]*(.*)$",
                         readme.read_text("utf-8"), re.M):
        title, desc = m.group(1).strip(), m.group(2).strip()
        cards.append(f'<div class="feat"><b>{title}</b><span>{desc}</span></div>')
        if len(cards) >= 6:
            break
    return "".join(cards)


def landing(src: Path, playbooks: list[Path], roles: list[Path],
            skills: list[Path], ver: str) -> str:
    logo = "images/doctrine_logo.png"
    mark = (f'<img src="{logo}" alt="Engineering Doctrine">'
            if (src / logo).exists()
            else '<div class="wordmark">Engineering Doctrine</div>')
    stat = "".join(
        f'<div class="stat"><b>{n}</b><span>{label}</span></div>'
        for n, label in [(len(roles), "roles"), (len(skills), "skills"),
                         ("G0-G7", "gates"), (len(playbooks), "playbooks")])
    feat = features(src)
    doc_cards = "".join(
        f'<a class="card" href="doc-{f.stem}.html"><b>{pretty(f.stem)}</b></a>'
        for f in playbooks)
    ver_pill = f'<div class="ver">v{ver}</div>' if ver else ""
    return (
        f'<section class="hero">{mark}'
        '<p class="tag">A gated engineering operating system for AI coding '
        f'agents.</p><div class="cta">'
        '<a class="btn p" href="doc-00-charter.html">Read the charter</a>'
        f'<a class="btn s" href="{REPO}">View on GitHub</a></div>'
        f'{ver_pill}</section>'
        '<section class="section"><div class="stats">' + stat + "</div></section>"
        + (f'<section class="section"><h2>What it gives you</h2>'
           f'<p class="sub">The full-SDLC discipline, enforced by tooling.</p>'
           f'<div class="grid">{feat}</div></section>' if feat else "")
        + '<section class="section"><h2>Start here</h2>'
        '<p class="sub">The playbooks that run the company.</p>'
        f'<div class="grid">{doc_cards}</div></section>'
        '<section class="section"><h2>Reference</h2>'
        f'<p class="sub">{len(roles)} roles and {len(skills)} skills, each a page '
        "in the sidebar of any doc.</p></section>")


def build(src: Path, out: Path) -> list[str]:
    out.mkdir(parents=True, exist_ok=True)
    (out / ".nojekyll").write_text("", "utf-8")
    if (src / "images").is_dir():
        shutil.copytree(src / "images", out / "images", dirs_exist_ok=True)
    playbooks = sorted((src / ".Doctrine").glob("*.md"))
    roles = sorted((src / ".Doctrine" / "roles").glob("*.md"))
    skills = sorted((src / ".Doctrine" / "skills").glob("*.md"))
    ver = version(src)

    def sidelinks(items: list[Path], prefix: str) -> str:
        return "".join(
            f'<a href="{prefix}-{f.stem}.html">{pretty(f.stem)}</a>'
            for f in items)

    aside = ('<aside><h3>Playbooks</h3>' + sidelinks(playbooks, "doc")
             + "<h3>Roles</h3>" + sidelinks(roles, "role")
             + "<h3>Skills</h3>" + sidelinks(skills, "skill") + "</aside>")

    pages: list[str] = []

    def doc(fname: str, title: str, md_text: str) -> None:
        inner = f'<div class="wrap">{aside}<main class="doc">{render(md_text)}</main></div>'
        (out / fname).write_text(shell(title, inner, ver), "utf-8")
        pages.append(fname)

    for f in playbooks:
        doc(f"doc-{f.stem}.html", pretty(f.stem), f.read_text("utf-8"))
    for f in roles:
        doc(f"role-{f.stem}.html", pretty(f.stem), f.read_text("utf-8"))
    for f in skills:
        doc(f"skill-{f.stem}.html", pretty(f.stem), f.read_text("utf-8"))
    (out / "index.html").write_text(
        shell("Home", landing(src, playbooks, roles, skills, ver), ver), "utf-8")
    pages.append("index.html")
    return pages


def gate(src: Path, out: Path) -> list[str]:
    findings: list[str] = []
    for f in (src / ".Doctrine").rglob("*.md"):
        text = f.read_text("utf-8")
        for pat, label in SECRET_PATTERNS:
            if re.search(pat, text):
                findings.append(f"secret ({label}) in {f.relative_to(src).as_posix()}")
    for p in out.glob("*.html"):
        h = p.read_text("utf-8")
        if "</body>" not in h or len(h) < 400:
            findings.append(f"thin/broken page: {p.name}")
    if not (out / "index.html").exists():
        findings.append("no index.html")
    return findings


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("usage: build_site.py <out_dir>", file=sys.stderr)
        return 2
    src = Path(__file__).resolve().parents[1]
    out = Path(argv[0])
    pages = build(src, out)
    findings = gate(src, out)
    logo = "yes" if (out / "images" / "doctrine_logo.png").exists() else "no"
    print(f"built: {len(pages)} pages -> {out} (logo: {logo}, dark-mode: yes)")
    if findings:
        print(f"FAIL-CLOSED GATE: BLOCK -- {len(findings)} finding(s)")
        for finding in findings[:20]:
            print(f"  - {finding}")
        return 1
    print("FAIL-CLOSED GATE: PASS -- safe to deploy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
