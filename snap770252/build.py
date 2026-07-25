#!/usr/bin/env python3
"""Downstream - static site generator.

Reads the JSON data layer in data/ and writes a complete static site to out/.
Every cross-link is derived from the data, so adding a condition once makes it
appear on every structure, node, and medication page it touches.
"""

import json, os, shutil, html
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
OUT = ROOT / "out"

SEV_LABEL = {"normal": "Compensating", "warn": "Decompensating", "crit": "Failing"}


def load(name):
    with open(DATA / name) as f:
        return json.load(f)


def load_all(prefix, key):
    """Merge every data/<prefix>*.json file, concatenating the given key."""
    items = []
    for p in sorted(DATA.glob(prefix + "*.json")):
        with open(p) as f:
            items.extend(json.load(f).get(key, []))
    return items


def esc(s):
    return html.escape(str(s), quote=False)


# ----------------------------------------------------------------- shell

TOPNAV = [
    ("signs.html", "Signs", "signs"),
    ("skills.html", "Skills", "skills"),
    ("nodes.html", "Nodes", "nodes"),
    ("meds.html", "Meds", "meds"),
    ("about.html", "About", "about"),
]


def topnav(base, active):
    """Reference links live in the top bar; systems are reached from home."""
    items = []
    for href, label, key in TOPNAV:
        cls = ' class="on"' if active == key else ""
        items.append(f'<a href="{base}{href}"{cls}>{label}</a>')
    return '<nav class="topnav">' + "".join(items) + "</nav>"


def ecg_path(complexes=3, span=200, base=100):
    """One ECG lead: P wave, QRS spike, T wave, repeated."""
    d = []
    for i in range(complexes):
        x = i * span
        d.append(
            f"M{x} {base} L{x+20} {base} "
            f"Q{x+30} {base-16} {x+40} {base} "
            f"L{x+56} {base} L{x+62} {base+10} L{x+70} {base-66} "
            f"L{x+78} {base+18} L{x+86} {base} "
            f"L{x+112} {base} Q{x+126} {base-26} {x+140} {base} "
            f"L{x+span} {base}")
    return " ".join(d)


ECG_D = ecg_path()

PRELOADER = f"""<div class="preload" id="preload">
<div class="preload-in">
<svg class="ecg" viewBox="0 0 600 200" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
<defs>
<linearGradient id="tail" x1="0" y1="0" x2="1" y2="0">
<stop offset="0" stop-color="#fff" stop-opacity="0"/>
<stop offset="0.55" stop-color="#fff" stop-opacity="0.35"/>
<stop offset="0.92" stop-color="#fff" stop-opacity="1"/>
<stop offset="1" stop-color="#fff" stop-opacity="1"/>
</linearGradient>
<linearGradient id="head" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="#DC2626" stop-opacity="0"/>
<stop offset="0.5" stop-color="#DC2626" stop-opacity="0.55"/>
<stop offset="1" stop-color="#DC2626" stop-opacity="0"/>
</linearGradient>
<mask id="sweep" maskUnits="userSpaceOnUse" x="0" y="0" width="600" height="200">
<rect x="-230" y="0" width="230" height="200" fill="url(#tail)">
<animate attributeName="x" from="-230" to="370" dur="2.4s" repeatCount="indefinite"/>
</rect>
</mask>
</defs>
<path class="ecg-base" d="{ECG_D}"/>
<g mask="url(#sweep)"><path class="ecg-live" d="{ECG_D}"/></g>
<rect class="ecg-head" x="-2.5" y="26" width="2.5" height="150" fill="url(#head)">
<animate attributeName="x" from="-2.5" to="597.5" dur="2.4s" repeatCount="indefinite"/>
</rect>
</svg>
<p class="preload-name">Downstream</p>
</div>
</div>
<noscript><style>.preload{{display:none}}</style></noscript>"""


SEARCH_ICON = ('<svg class="search-icon" viewBox="0 0 16 16" fill="none" '
               'xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
               '<circle cx="6.5" cy="6.5" r="4.25" stroke="currentColor" stroke-width="1.5"/>'
               '<line x1="9.7" y1="9.7" x2="13.5" y2="13.5" stroke="currentColor" '
               'stroke-width="1.5" stroke-linecap="round"/>'
               '</svg>')


def page(path, title, body, active="", base="", sysid=None, wide=False):
    wrapcls = "wrap wide" if wide else "wrap"
    bodycls = f' class="sys-{sysid}"' if sysid else ""
    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} &middot; Downstream</title>
<link rel="stylesheet" href="{base}assets/style.css">
</head>
<body data-base="{base}"{bodycls}>
{PRELOADER}
<header class="topbar">
<a class="brand" href="{base}index.html">
<span class="brand-name">Downstream</span>
</a>
<div class="search-wrap">
<label style="position:absolute;left:-9999px" for="q">Search</label>
{SEARCH_ICON}
<input class="searchbox" id="q" type="search" placeholder="Search conditions, drugs, anatomy&hellip;" autocomplete="off">
<ul id="results"></ul>
</div>
{topnav(base, active)}
</header>
<div class="shell">
<main class="main"><div class="{wrapcls}">
{body}
<div class="foot">
<p>Downstream is a study tool, not a field reference and not medical direction. Doses and protocols change; your service&rsquo;s medical control protocols are the authority of record. Scope tags reflect Alberta and should be verified against your own registration and service policy.</p>
</div>
</div></main>
</div>
<script src="{base}assets/search-index.js"></script>
<script src="{base}assets/app.js"></script>
</body>
</html>"""
    full = OUT / path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(doc)


# ----------------------------------------------------------------- helpers

def crumb(base, parts):
    bits = []
    for i, (label, href) in enumerate(parts):
        if href:
            bits.append(f'<a href="{base}{href}">{esc(label)}</a>')
        else:
            bits.append(f'<span>{esc(label)}</span>')
        if i < len(parts) - 1:
            bits.append('<span aria-hidden="true">&rsaquo;</span>')
    return '<p class="crumb">' + "".join(bits) + "</p>"


def badge(scope):
    s = (scope or "varies").lower()
    cls = s if s in ("emr", "pcp", "acp") else "varies"
    txt = scope if scope and scope != "varies" else "scope varies"
    return f'<span class="badge {cls}">{esc(txt)}</span>'


def ul(items, cls="plain"):
    lis = "".join(f"<li>{esc(i)}</li>" for i in items)
    return f'<ul class="{cls}">{lis}</ul>'


IMG_EXTS = (".svg", ".webp", ".png", ".jpg", ".jpeg")


def sys_image(sysid):
    """assets/img/<system id>.<ext> if it exists. Drop a file in, it appears."""
    for ext in IMG_EXTS:
        if (ROOT / "assets" / "img" / (sysid + ext)).exists():
            return f"assets/img/{sysid}{ext}"
    return None


def struct_groups(sysid, base):
    """Structure cards for one system: failure mode, condition chips, and an
    inline expander with the anatomy itself so you can drill down without
    leaving the page."""
    out = []
    for st in [s for s in STRUCTURES if s["system"] == sysid]:
        conds = [c for c in CONDITIONS if st["id"] in c.get("structures", [])]
        chips = []
        for c in conds:
            if c["status"] == "built":
                chips.append(f'<a class="chip" href="{base}condition/{c["id"]}.html">{esc(c["name"])}</a>')
            else:
                chips.append(f'<span class="chip soon" title="Not written yet">{esc(c["name"])}</span>')
        if not chips:
            chips.append('<span class="chip soon">Nothing mapped yet</span>')

        det = f'<p class="st-what">{esc(st["what_it_is"])}</p>'
        if st.get("normal_function"):
            det += (f'<p class="minihead">What it does when it works</p>'
                    f'{ul(st["normal_function"])}')
        if st.get("why_it_matters"):
            det += (f'<p class="minihead">Why this structure matters</p>'
                    f'<p>{esc(st["why_it_matters"])}</p>')
        if st.get("field_relevance"):
            det += (f'<p class="minihead">In the field</p>'
                    f'{ul(st["field_relevance"])}')
        det += (f'<a class="st-full" href="{base}structure/{st["id"]}.html">'
                f'Open {esc(st["name"].lower())} on its own page &rarr;</a>')

        out.append(f"""<div class="group" data-struct="{st['id']}">
<h3><a href="{base}structure/{st['id']}.html">{esc(st['name'])}</a></h3>
<p class="fm">Failure mode: {esc(st['failure_mode'])}</p>
<div class="chips">{''.join(chips)}</div>
<button class="st-more" type="button" aria-expanded="false"
aria-controls="d-{sysid}-{st['id']}"><span>What this part actually is</span></button>
<div class="st-detail" id="d-{sysid}-{st['id']}">{det}</div>
</div>""")
    return out


# ----------------------------------------------------------------- pages

def build_home():
    tiles, panels = [], []
    for s in SYSTEMS:
        sid = s["id"]
        structs = [x for x in STRUCTURES if x["system"] == sid]
        conds = [c for c in CONDITIONS
                 if any(x["id"] in c.get("structures", []) for x in structs)]
        nbuilt_c = sum(1 for c in conds if c["status"] == "built")
        img = sys_image(sid)
        art = (f'<img src="{img}" alt="" loading="lazy">' if img
               else f'<span class="noimg">{esc(s["name"][:1])}</span>')
        meta = (f'{len(structs)} structure{"s" if len(structs) != 1 else ""}'
                f' &middot; {nbuilt_c} condition{"s" if nbuilt_c != 1 else ""}')

        if s["status"] != "built":
            tiles.append(f"""<div class="tile soon sys-{sid}">
<span class="tile-art">{art}</span>
<span class="tile-txt"><b>{esc(s["name"])}</b>
<span class="tile-job">{esc(s["job"])}</span>
<span class="tile-meta">Not written yet</span></span>
</div>""")
            continue

        tiles.append(f"""<button class="tile sys-{sid}" type="button" data-sys="{sid}"
aria-expanded="false" aria-controls="panel-{sid}">
<span class="tile-art">{art}</span>
<span class="tile-txt"><b>{esc(s["name"])}</b>
<span class="tile-job">{esc(s["job"])}</span>
<span class="tile-meta">{meta}</span></span>
<span class="tile-open" aria-hidden="true">Open</span>
</button>""")

        panels.append(f"""<section class="panel sys-{sid}" id="panel-{sid}" data-panel="{sid}">
<div class="panel-head">
<div>
<span class="eyebrow">Body system</span>
<h2>{esc(s["name"])}</h2>
<p class="panel-job">{esc(s["job"])}</p>
</div>
<a class="panel-full" href="system/{sid}.html">Full page &rarr;</a>
</div>
<p class="panel-note">Filed by the part that is physically damaged, not by diagnosis. The groups below are really a list of the ways this system fails.</p>
<div class="grouplist">{''.join(struct_groups(sid, ''))}</div>
</section>""")

    nstruct = len(STRUCTURES)
    nbuilt = sum(1 for c in CONDITIONS if c["status"] == "built")
    nnode = len(NODES)
    nmed = len(MEDS)
    nskill = len(SKILLS)
    nsign = len(SIGNS)
    body = f"""<div class="hero">
<h1 class="wordmark">Downstream</h1>
</div>

<div class="anatomy" id="anatomy">
<p class="pick">Pick an anatomy</p>
<div class="tiles">{''.join(tiles)}</div>
<div class="panels">{''.join(panels)}</div>
</div>

<p class="tally">{nstruct} structures &middot; {nbuilt} conditions &middot; {nnode} nodes &middot; {nmed} medications &middot; {nskill} skills &middot; {nsign} signs</p>"""
    page("index.html", "Anatomy first", body, active="", base="", wide=True)


def build_system(sys):
    groups = struct_groups(sys["id"], "../")
    img = sys_image(sys["id"])
    hero = (f'<div class="syshero"><img src="../{img}" alt="{esc(sys["name"])}"></div>'
            if img else "")

    body = f"""{crumb('../', [('Downstream', 'index.html'), (sys['name'], None)])}
<h1>{esc(sys['name'])}</h1>
<p class="lede">{esc(sys['job'])}</p>
{hero}
<h2>Where things go wrong</h2>
<p>Every condition below is filed under the part it physically damages. Read down the list and notice that the groups are really a list of the ways this system can fail &mdash; and that knowing which group you are in tells you most of what you need before you have a diagnosis.</p>
<div class="grouplist">{''.join(groups)}</div>"""
    page(f"system/{sys['id']}.html", sys["name"], body, active="sys-" + sys["id"], base="../", sysid=sys["id"])


def build_structure(st):
    sys = next(s for s in SYSTEMS if s["id"] == st["system"])
    conds = [c for c in CONDITIONS if st["id"] in c.get("structures", [])]
    chips = []
    for c in conds:
        if c["status"] == "built":
            chips.append(f'<a class="chip" href="../condition/{c["id"]}.html">{esc(c["name"])}</a>')
        else:
            chips.append(f'<span class="chip soon">{esc(c["name"])}</span>')

    fr = ""
    if st.get("field_relevance"):
        fr = f'<h2>Why it matters in the field</h2>{ul(st["field_relevance"])}'

    siblings = "".join(
        f'<a class="chip" href="../structure/{o["id"]}.html">{esc(o["name"])}</a>'
        for o in STRUCTURES if o["system"] == st["system"] and o["id"] != st["id"])
    siblings += f'<a class="chip" href="../system/{sys["id"]}.html">All of it &rarr;</a>'

    body = f"""{crumb('../', [('Downstream', 'index.html'), (sys['name'], f'system/{sys["id"]}.html'), (st['name'], None)])}
<span class="eyebrow">Anatomy</span>
<h1>{esc(st['name'])}</h1>
<p class="lede">{esc(st['what_it_is'])}</p>

<h2>What it does when it works</h2>
{ul(st['normal_function'])}

<h2>Why this structure matters</h2>
<p>{esc(st['why_it_matters'])}</p>

{fr}

<h2>What can break it</h2>
<div class="group">
<p class="fm">Failure mode: {esc(st['failure_mode'])}</p>
<div class="chips">{''.join(chips) if chips else '<span class="chip soon">Nothing mapped yet</span>'}</div>
</div>

<h2>Rest of the {esc(sys['name'].lower())}</h2>
<div class="chips">{siblings}</div>"""
    page(f"structure/{st['id']}.html", st["name"], body, active="st-" + st["id"], base="../", sysid=st["system"])


def build_condition(c):
    structs = [s for s in STRUCTURES if s["id"] in c.get("structures", [])]
    sys = next(s for s in SYSTEMS if s["id"] == structs[0]["system"]) if structs else None

    # map interventions onto cascade steps
    clamps = {}
    for iv in c.get("interventions", []):
        med = MED_BY_ID.get(iv["med"])
        if not med:
            continue
        link = (f'<a href="../med/{med["id"]}.html">{esc(med["name"])}</a>'
                if med["status"] == "built" else esc(med["name"]))
        sc = iv.get("scope", med.get("scope"))
        clamps.setdefault(iv["breaks_at"], []).append(
            (f'{link} {badge(sc)}', iv.get("note", ""), sc))
    for iv in c.get("non_drug_interventions", []):
        clamps.setdefault(iv["breaks_at"], []).append(
            (f'{esc(iv["name"])} {badge(iv.get("scope"))}', iv.get("note", ""), iv.get("scope")))

    steps = []
    for step in c["cascade"]:
        sev = step.get("severity", "normal")
        shared = ""
        if step.get("shared") and step["shared"] in NODE_BY_ID:
            shared = (f'<a class="sharedlink" href="../node/{step["shared"]}.html">'
                      f'shared node &rarr; {esc(NODE_BY_ID[step["shared"]]["name"])}</a>')
        struct = ""
        if step.get("structure") and step["structure"] in STRUCT_BY_ID:
            struct = (f'<a class="sharedlink" href="../structure/{step["structure"]}.html">'
                      f'anatomy &rarr; {esc(STRUCT_BY_ID[step["structure"]]["name"])}</a>')
        links = " &nbsp; ".join(x for x in [shared, struct] if x)

        cl = ""
        for title, note, scope in clamps.get(step["id"], []):
            out_cls = " out" if (scope or "").upper() not in ("EMR", "") else ""
            cl += (f'<div class="clamp{out_cls}"><p class="ct">{title}</p>'
                   f'<p class="cn">{esc(note)}</p></div>')

        steps.append(f"""<div class="step {sev}">
<div class="rail"><span class="dot"></span></div>
<div class="stepbody">
<div class="lbl">{esc(step['label'])}</div>
<div class="sub">{esc(step.get('sub',''))}</div>
<p class="det">{esc(step['detail'])}</p>
{links}
{cl}
</div></div>""")

    flags = ""
    if c.get("red_flags"):
        flags = (f'<div class="box flags"><span class="eyebrow">Stop and escalate</span>'
                 f'{ul(c["red_flags"])}</div>')

    diffs = ""
    if c.get("differentiators"):
        rows = "".join(
            f'<div class="diff"><b>Not {esc(d["vs"])}?</b><p>{esc(d["how"])}</p></div>'
            for d in c["differentiators"])
        diffs = f"<h2>Telling it apart</h2>{rows}"

    struct_links = ", ".join(
        f'<a href="../structure/{s["id"]}.html">{esc(s["name"])}</a>' for s in structs)

    crumbs = [("Downstream", "index.html")]
    if sys:
        crumbs.append((sys["name"], f'system/{sys["id"]}.html'))
    if structs:
        crumbs.append((structs[0]["name"], f'structure/{structs[0]["id"]}.html'))
    crumbs.append((c["name"], None))

    body = f"""{crumb('../', crumbs)}
<span class="eyebrow">Condition &middot; {struct_links}</span>
<h1>{esc(c['name'])}</h1>
<p class="lede">{esc(c['one_liner'])}</p>
<div class="box"><span class="eyebrow">In one breath</span><p>{esc(c['in_one_breath'])}</p></div>

<h2>The chain</h2>
<p>Each step causes the one below it. Interventions are attached to the link they break, and greyed where they sit outside EMR scope in Alberta.</p>
<div class="spine">{''.join(steps)}</div>

{flags}
{diffs}"""
    page(f"condition/{c['id']}.html", c["name"], body, base="../", sysid=(sys["id"] if sys else None))


def build_node(n):
    used_in = []
    for c in CONDITIONS:
        if c["status"] != "built":
            continue
        for step in c.get("cascade", []):
            if step.get("shared") == n["id"]:
                used_in.append(c)
                break
    used = ""
    if used_in:
        chips = "".join(
            f'<a class="chip" href="../condition/{c["id"]}.html">{esc(c["name"])}</a>'
            for c in used_in)
        used = (f'<h2>Cascades that reach here</h2>'
                f'<p>Different starting points, identical endpoint. This is what makes the '
                f'node worth learning once instead of eleven times.</p>'
                f'<div class="chips">{chips}</div>')

    leads = ""
    if n.get("leads_to"):
        chips = "".join(
            f'<a class="chip" href="../node/{i}.html">{esc(NODE_BY_ID[i]["name"])}</a>'
            for i in n["leads_to"] if i in NODE_BY_ID)
        if chips:
            leads = f"<h2>What this leads to next</h2><div class=\"chips\">{chips}</div>"

    body = f"""{crumb('../', [('Downstream', 'index.html'), ('Node library', 'nodes.html'), (n['name'], None)])}
<span class="eyebrow">Shared node &middot; {esc(SEV_LABEL.get(n['severity'], ''))}</span>
<h1>{esc(n['name'])}</h1>
<p class="lede">{esc(n['one_liner'])}</p>

<h2>What is actually happening</h2>
<p>{esc(n['what_is_happening'])}</p>

<h2>Why it follows from almost anything</h2>
<p>{esc(n['why_it_follows'])}</p>

<h2>What you see</h2>
{ul(n['what_you_see'])}

<div class="box trap"><span class="eyebrow">The trap</span><p>{esc(n['the_trap'])}</p></div>

{leads}
{used}"""
    page(f"node/{n['id']}.html", n["name"], body, base="../")


def build_med(m):
    rows = "".join(
        f'<tr><td>{esc(d["route"])}</td><td class="dose">{esc(d["dose"])}</td>'
        f'<td class="note">{esc(d.get("notes",""))}</td></tr>'
        for d in m.get("dosing", []))
    table = (f'<table class="data"><thead><tr><th>Route</th><th>Dose</th><th>Notes</th></tr>'
             f'</thead><tbody>{rows}</tbody></table>') if rows else ""

    cautions = "".join(
        f'<div class="diff"><b>{esc(x["what"])}</b><p>{esc(x["why"])}</p></div>'
        for x in m.get("cautions", []))

    used = ""
    if m.get("used_in"):
        chips = "".join(
            f'<a class="chip" href="../condition/{i}.html">{esc(COND_BY_ID[i]["name"])}</a>'
            for i in m["used_in"] if i in COND_BY_ID and COND_BY_ID[i]["status"] == "built")
        if chips:
            used = f'<h2>Used in</h2><div class="chips">{chips}</div>'

    aka = f' <span style="font-weight:400;color:var(--text-3)">({esc(m["aka"])})</span>' if m.get("aka") else ""

    body = f"""{crumb('../', [('Downstream', 'index.html'), ('Medications', 'meds.html'), (m['name'], None)])}
<span class="eyebrow">Medication &middot; {esc(m['class'])}</span>
<h1>{esc(m['name'])}{aka}</h1>
<p class="lede">{esc(m['one_liner'])}</p>
<p>{badge(m.get('scope'))} &nbsp;<span style="font-size:13.5px;color:var(--text-2)">{esc(m.get('scope_note',''))}</span></p>

<div class="box"><span class="eyebrow">Breaks the chain at</span><p style="margin:0"><b>{esc(m['breaks_cascade_at'])}</b></p></div>

<h2>Mechanism</h2>
<p>{esc(m['mechanism'])}</p>

<h2>Why it works at that link and not another</h2>
<p>{esc(m['why_it_works_here'])}</p>

<h2>Dosing</h2>
{table}
<p style="font-size:14px;color:var(--text-2)"><b>Target:</b> {esc(m.get('targets',''))}</p>

<h2>Timing</h2>
<p>This is the part that tells you when to reassess, and it is the part most people never learn properly.</p>
<div class="timing">
<div><dt>Onset</dt><dd>{esc(m['onset'])}</dd></div>
<div><dt>Peak</dt><dd>{esc(m['peak'])}</dd></div>
<div><dt>Duration</dt><dd>{esc(m['duration'])}</dd></div>
</div>

<h2>What working looks like</h2>
{ul(m['working_looks_like'])}

<h2>What it means if nothing happens</h2>
<p>{esc(m['not_working_means'])}</p>

<h2>Cautions</h2>
{cautions}

<h2>Side effects are the drug doing its job elsewhere</h2>
<p>{esc(m['side_effects_as_overshoot'])}</p>

{used}"""
    page(f"med/{m['id']}.html", m["name"], body, base="../")


def build_skill(sk):
    steps = "".join(
        f'<div class="step normal"><div class="rail"><span class="dot"></span></div>'
        f'<div class="stepbody"><div class="lbl">{esc(s["do"])}</div>'
        f'<p class="det">{esc(s["why"])}</p></div></div>'
        for s in sk["steps"])

    adj = ""
    if sk.get("adjuncts"):
        adj = "<h2>Adjuncts</h2>" + "".join(
            f'<div class="diff"><b>{esc(a["name"])}</b><p>{esc(a["note"])}</p></div>'
            for a in sk["adjuncts"])

    rel = ""
    if sk.get("related_conditions"):
        chips = "".join(
            f'<a class="chip" href="../condition/{i}.html">{esc(COND_BY_ID[i]["name"])}</a>'
            for i in sk["related_conditions"]
            if i in COND_BY_ID and COND_BY_ID[i]["status"] == "built")
        if chips:
            rel = f'<h2>Where you use it</h2><div class="chips">{chips}</div>'

    body = f"""{crumb('../', [('Downstream', 'index.html'), ('Skills', 'skills.html'), (sk['name'], None)])}
<span class="eyebrow">Skill</span>
<h1>{esc(sk['name'])}</h1>
<p class="lede">{esc(sk['one_liner'])}</p>
<p>{badge(sk.get('scope'))}</p>

<h2>Why it works</h2>
<p>{esc(sk['why_it_works'])}</p>

<h2>How to do it, and why each step exists</h2>
<p>Every step below has a reason. If you know the reason, you can adapt when the situation does not match the textbook.</p>
<div class="spine">{steps}</div>

{adj}

<div class="box flags"><span class="eyebrow">Common errors</span>{ul(sk['errors'])}</div>

{rel}"""
    page(f"skill/{sk['id']}.html", sk["name"], body, base="../")


def build_sign(sg):
    rows = ""
    for c in sg["causes"]:
        cid = c["condition"]
        if c.get("no_page") or cid not in COND_BY_ID or COND_BY_ID[cid]["status"] != "built":
            name = esc(cid.replace("-", " ").capitalize())
            rows += f'<div class="diff"><b>{name}</b><p>{esc(c["clue"])}</p></div>'
        else:
            rows += (f'<div class="diff"><b><a href="../condition/{cid}.html">'
                     f'{esc(COND_BY_ID[cid]["name"])}</a></b><p>{esc(c["clue"])}</p></div>')

    body = f"""{crumb('../', [('Downstream', 'index.html'), ('Start from a sign', 'signs.html'), (sg['name'], None)])}
<span class="eyebrow">Reverse lookup</span>
<h1>{esc(sg['name'])}</h1>
<p class="lede">{esc(sg['one_liner'])}</p>

<h2>What this sign actually means</h2>
<p>{esc(sg['what_it_means'])}</p>

<div class="box"><span class="eyebrow">First moves</span>{ul(sg['first_moves'])}</div>

<h2>What produces it, and how to tell them apart</h2>
<p>Ordered roughly by how quickly each will kill. The clue column is what separates it from the others on this list.</p>
{rows}"""
    page(f"sign/{sg['id']}.html", sg["name"], body, active="signs", base="../")


def build_skill_sign_indexes():
    cards = "".join(
        f'<a class="card" href="skill/{s["id"]}.html"><b>{esc(s["name"])}</b>'
        f'<span>{esc(s["one_liner"])}</span></a>' for s in SKILLS)
    body = f"""{crumb('', [('Downstream', 'index.html'), ('Skills', None)])}
<h1>Skills</h1>
<p class="lede">Procedures rather than cascades, so they get a different format: every step carries the reason it exists.</p>
<p>Knowing why a step is there is what lets you adapt when the real situation does not match the way you were taught it. It is also the difference between performing a skill and understanding one.</p>
<div class="cards">{cards}</div>"""
    page("skills.html", "Skills", body, active="skills", base="")

    cards = "".join(
        f'<a class="card" href="sign/{s["id"]}.html"><b>{esc(s["name"])}</b>'
        f'<span>{esc(s["one_liner"])}</span></a>' for s in SIGNS)
    body = f"""{crumb('', [('Downstream', 'index.html'), ('Start from a sign', None)])}
<h1>Start from a sign</h1>
<p class="lede">In the field you do not start with a diagnosis. You start with a patient who is confused, or breathless, or grey, and you work backwards.</p>
<p>The rest of this site runs forward: anatomy, then what breaks it, then what happens next. These pages run the same chains in reverse. Pick what you can see, and every cascade that produces it is listed with the feature that separates it from the others.</p>
<div class="cards">{cards}</div>"""
    page("signs.html", "Start from a sign", body, active="signs", base="")


def build_indexes():
    # node library
    order = {"normal": 0, "warn": 1, "crit": 2}
    cards = "".join(
        f'<a class="card" href="node/{n["id"]}.html"><b>{esc(n["name"])}</b>'
        f'<span>{esc(n["one_liner"])}</span></a>'
        for n in sorted(NODES, key=lambda x: order.get(x["severity"], 9)))
    body = f"""{crumb('', [('Downstream', 'index.html'), ('Node library', None)])}
<h1>Node library</h1>
<p class="lede">Physiological states that sit downstream of many different conditions. Written once here, linked from every cascade that reaches them.</p>
<p>These are ordered roughly by how deep into a deterioration they appear. If you learn nothing else on this site, learn these &mdash; they are the vocabulary every cascade is written in.</p>
<div class="cards">{cards}</div>"""
    page("nodes.html", "Node library", body, active="nodes", base="")

    # meds
    built, planned = [], []
    for m in MEDS:
        if m["status"] == "built":
            built.append(
                f'<a class="card" href="med/{m["id"]}.html"><b>{esc(m["name"])}</b>'
                f'<span>{esc(m["one_liner"])}</span></a>')
        else:
            planned.append(
                f'<div class="card soon"><b>{esc(m["name"])}</b>'
                f'<span>{esc(m["one_liner"])}</span></div>')
    body = f"""{crumb('', [('Downstream', 'index.html'), ('Medications', None)])}
<h1>Medications</h1>
<p class="lede">Every drug is filed by the link in the chain it interrupts. Side effects are treated as the same mechanism acting somewhere you did not want it, because that is what they are.</p>
<div class="cards">{''.join(built)}</div>
<h2>Not written yet</h2>
<div class="cards">{''.join(planned)}</div>"""
    page("meds.html", "Medications", body, active="meds", base="")

    # about
    body = f"""{crumb('', [('Downstream', 'index.html'), ('About', None)])}
<h1>About &amp; sources</h1>
<p class="lede">A study tool built around one idea: physiology is a chain of consequences, and it is far easier to learn as a chain than as a list.</p>

<h2>What this is not</h2>
<div class="disclaim">Not a field reference. Not medical direction. Not a substitute for your protocols, your medical director, or your instructor. Doses drift and protocols get revised &mdash; treat your service&rsquo;s medical control protocols as the authority of record, and this site as a way of understanding why they say what they say.</div>

<h2>Scope tags</h2>
<p>Interventions carry an Alberta scope tag: <span class="badge emr">EMR</span> <span class="badge pcp">PCP</span> <span class="badge acp">ACP</span>. The pharmacology is taught in full regardless of scope, because understanding why a paramedic reaches for a different drug makes you better at the part that is yours. Scope varies by province, by service, and by medical direction &mdash; verify against your own registration.</p>

<h2>Sources</h2>
<ul class="plain">
<li><b>Emergency Medical Responder</b>, WisTech Open (2025), edited by Suzanne Martens MD &mdash; licensed CC BY 4.0.</li>
<li><b>Anatomy and Physiology 2e</b>, OpenStax &mdash; Betts, Young, Wise et al., openly licensed.</li>
<li><b>Oregon EMS Psychomotor Skills Lab Manual</b> &mdash; Hamper, Curtz, Edwins, Kennel; CC BY-NC-SA.</li>
<li><b>Alberta Health Services EMS Medical Control Protocols</b> &mdash; published at protocols.ahsems.com.</li>
<li><b>Alberta Medical First Response Program protocols</b> &mdash; albertamfr.ca.</li>
<li><b>Alberta College of Paramedics</b> standards of practice and competency profile.</li>
</ul>
<p>All prose on this site is written fresh rather than reproduced. Openly licensed sources above were used for coverage, structure, and verification.</p>"""
    page("about.html", "About", body, active="about", base="")


def build_search_index():
    items = []
    for s in SYSTEMS:
        if s["status"] == "built":
            items.append({"kind": "system", "name": s["name"], "url": f'system/{s["id"]}.html'})
    for s in STRUCTURES:
        items.append({"kind": "anatomy", "name": s["name"], "url": f'structure/{s["id"]}.html',
                      "alt": s["failure_mode"]})
    for c in CONDITIONS:
        if c["status"] == "built":
            items.append({"kind": "condition", "name": c["name"], "url": f'condition/{c["id"]}.html',
                          "alt": c["one_liner"]})
    for n in NODES:
        items.append({"kind": "node", "name": n["name"], "url": f'node/{n["id"]}.html',
                      "alt": n["one_liner"]})
    for m in MEDS:
        if m["status"] == "built":
            items.append({"kind": "drug", "name": m["name"], "url": f'med/{m["id"]}.html',
                          "alt": m.get("aka", "")})
    for s_ in SKILLS:
        items.append({"kind": "skill", "name": s_["name"], "url": f'skill/{s_["id"]}.html'})
    for s_ in SIGNS:
        items.append({"kind": "sign", "name": s_["name"], "url": f'sign/{s_["id"]}.html',
                      "alt": s_["one_liner"]})
    (OUT / "assets").mkdir(parents=True, exist_ok=True)
    (OUT / "assets" / "search-index.js").write_text(
        "window.INDEX = " + json.dumps(items, indent=0) + ";\n")


# ----------------------------------------------------------------- run

def validate():
    """Fail loudly on broken cross-references rather than emitting dead links."""
    errs = []
    steps_by_cond = {c["id"]: {s["id"] for s in c.get("cascade", [])} for c in CONDITIONS}
    for c in CONDITIONS:
        for s in c.get("structures", []):
            if s not in STRUCT_BY_ID:
                errs.append(f"{c['id']}: unknown structure '{s}'")
        for st in c.get("cascade", []):
            if st.get("shared") and st["shared"] not in NODE_BY_ID:
                errs.append(f"{c['id']}: unknown node '{st['shared']}'")
            if st.get("structure") and st["structure"] not in STRUCT_BY_ID:
                errs.append(f"{c['id']}: unknown structure ref '{st['structure']}'")
        for iv in c.get("interventions", []) + c.get("non_drug_interventions", []):
            if iv["breaks_at"] not in steps_by_cond[c["id"]]:
                errs.append(f"{c['id']}: intervention targets missing step '{iv['breaks_at']}'")
            if iv.get("med") and iv["med"] not in MED_BY_ID:
                errs.append(f"{c['id']}: unknown med '{iv['med']}'")
    for n in NODES:
        for l in n.get("leads_to", []):
            if l not in NODE_BY_ID:
                errs.append(f"node {n['id']}: unknown leads_to '{l}'")
    for s in STRUCTURES:
        if s["system"] not in {x["id"] for x in SYSTEMS}:
            errs.append(f"structure {s['id']}: unknown system '{s['system']}'")
    for sk in SKILLS:
        for i in sk.get("related_conditions", []):
            if i not in COND_BY_ID:
                errs.append(f"skill {sk['id']}: unknown condition '{i}'")
    for sg in SIGNS:
        for c in sg.get("causes", []):
            if not c.get("no_page") and c["condition"] not in COND_BY_ID:
                errs.append(f"sign {sg['id']}: unknown condition '{c['condition']}'")
    seen = set()
    for c in CONDITIONS:
        if c["id"] in seen:
            errs.append(f"duplicate condition id '{c['id']}'")
        seen.add(c["id"])
    if errs:
        raise SystemExit("Broken references:\n" + "\n".join("  - " + e for e in errs))


if __name__ == "__main__":
    s = load("structures.json")
    SYSTEMS = s["systems"]
    STRUCTURES = load_all("structures", "structures")
    CONDITIONS = load_all("conditions", "conditions")
    NODES = load_all("nodes", "nodes")
    MEDS = load_all("meds", "meds")
    SKILLS = load("skills.json")["skills"]
    SIGNS = load("signs.json")["signs"]

    STRUCT_BY_ID = {x["id"]: x for x in STRUCTURES}
    COND_BY_ID = {x["id"]: x for x in CONDITIONS}
    NODE_BY_ID = {x["id"]: x for x in NODES}
    MED_BY_ID = {x["id"]: x for x in MEDS}

    validate()

    OUT.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "assets", OUT / "assets", dirs_exist_ok=True)

    build_home()
    for sy in SYSTEMS:
        if sy["status"] == "built":
            build_system(sy)
    for st in STRUCTURES:
        build_structure(st)
    for c in CONDITIONS:
        if c["status"] == "built":
            build_condition(c)
    for n in NODES:
        build_node(n)
    for m in MEDS:
        if m["status"] == "built":
            build_med(m)
    build_indexes()
    for sk in SKILLS:
        build_skill(sk)
    for sg in SIGNS:
        build_sign(sg)
    build_skill_sign_indexes()
    build_search_index()

    n_files = sum(1 for _ in OUT.rglob("*") if _.is_file())
    print(f"built {n_files} files -> {OUT}")
