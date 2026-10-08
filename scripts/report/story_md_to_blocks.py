"""docs/story.md -> list of blocks for the Word builder."""
import json, re, sys
src = open(sys.argv[1]).read().split("\n")

def runs(t):
    out = []
    for part in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\))", t):
        if not part: continue
        if part.startswith("**"): out.append({"t": part[2:-2], "b": True})
        elif part.startswith("`"): out.append({"t": part[1:-1], "code": True})
        elif part.startswith("["): out.append({"t": re.match(r"\[([^\]]+)\]", part).group(1)})
        elif part.startswith("*") and part.endswith("*") and len(part) > 2: out.append({"t": part[1:-1], "i": True})
        else: out.append({"t": part})
    return out

blocks, i = [], 0
while i < len(src):
    line = src[i]
    if not line.strip(): i += 1; continue
    if line.startswith("#"):
        lvl = len(line) - len(line.lstrip("#")); blocks.append({"type": "h", "level": lvl, "text": line.lstrip("# ").strip()}); i += 1; continue
    if line.startswith("|"):
        rows = []
        while i < len(src) and src[i].startswith("|"):
            cells = [c.strip() for c in src[i].strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-+:?", c) for c in cells): rows.append([runs(c) for c in cells])
            i += 1
        blocks.append({"type": "table", "rows": rows}); continue
    m = re.match(r"^(\s*)(-|\d+\.) (.*)", line)
    if m:
        kind = "bullets" if m.group(2) == "-" else "numbered"; items = []
        while i < len(src) and re.match(r"^(-|\d+\.) ", src[i]):
            txt = re.sub(r"^(-|\d+\.) ", "", src[i]); i += 1
            while i < len(src) and src[i].startswith("   ") and src[i].strip(): txt += " " + src[i].strip(); i += 1
            while i < len(src) and src[i].startswith("  ") and src[i].strip() and not re.match(r"^(-|\d+\.) ", src[i]): txt += " " + src[i].strip(); i += 1
            items.append(runs(txt))
            if i < len(src) and not src[i].strip(): break
        blocks.append({"type": kind, "items": items}); continue
    txt = line.strip(); i += 1
    while i < len(src) and src[i].strip() and not src[i].startswith(("#", "|", "- ")) and not re.match(r"^\d+\. ", src[i]):
        txt += " " + src[i].strip(); i += 1
    blocks.append({"type": "p", "runs": runs(txt), "plain": re.sub(r"[*`]", "", txt)})
json.dump(blocks, open(sys.argv[2], "w"), indent=0)
print(len(blocks), [b["type"] for b in blocks])
