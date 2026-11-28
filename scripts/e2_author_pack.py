"""LABS-1.065: build the E2 author pack (benchmark/e2/author-pack/) from the approved sources.

The pack is what question authors and verifiers receive (authoring protocol §3). Implementation-derived material is
removed: every [D] discrepancy statement, every "Local items" block, the correction pointers (DI ids) that would reveal
known defects, and code citations. Then a leak scan lists any line still mentioning implementation material; the scan
result is written beside the pack and must be empty before the pack is frozen.

    uv run --offline python -I scripts/e2_author_pack.py            # build and scan
"""
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "benchmark" / "e2" / "author-pack"
LEAK = re.compile(r"\b(code|docstrings?|implementation|implemented|currently|current behaviour|reproduced|DYN|phys|"
                  r"_resolve|_describe|qualities\.py|model\.py|dynamics\.py|physical\.py|laboratory\.py|src/|tests/|"
                  r"probes/|DX-\d+|D-[A-Z]{2}-\d+|DI-\d+|diagnostic|expected to fail|E1 gold|LAB-\d+|ORG-\d+)\b",
                  re.I)


# lines of the verbatim ontology document reviewed by the coordinator: architectural statements about the design, not
# descriptions of how any reader behaves
REVIEWED = {
    ("world-ontology-v0.2.md", l.strip()) for l in (REPO / "docs/architecture/world-ontology-v0.2.md").read_text()
    .split("\n") if LEAK.search(l)}


def strip_d_fragments(line):
    """Remove '[D] ...' fragments from a kept line: inside a table cell up to the cell end; otherwise to the end."""
    if line.lstrip().startswith("|"):                    # also tables indented inside numbered lists (v1.1 fix)
        cells = line.split("|")
        new = []
        for c in cells:
            if "[D]" in c:
                c = re.sub(r";?\s*\(?[^;|()]*\[D\][^|]*", "", c).rstrip(" ;,(")
            new.append(c)
        return "|".join(new)
    # v1.1: a sentence interrupted by the removed fragment is closed, not left dangling
    return re.sub(r"\s*\(?\[D\].*$", " (not fixed by the contract).", line)


S012 = """### 0.12 Established rules restated (pack v1.1) [E]

These approved rules were stated inside entries this edition otherwise removes, so they are restated here. Each is
established; it overrides any other text in this edition that seems to differ.

| Reader | Rule | Source |
|---|---|---|
| `value_at` | A dispute keeps its conflicting relationship between rival values; polarity alone is not enough. | A0 F-4; SB Q-B2; P-VA-1 as qualified |
| every reader, incl. `value_at` | No reader reports content that is DISPUTED for the perspective as undisputed. Value readers apply declared slots only; an exclusive office whose holders conflict is never reported as undisputed by a value reader. | B-D §2, §3; DI19 report §1; D2 §3; v0.2 §5.3 |
| `transform_between` | A disputed transform on any route gives DISPUTED, with the disputed transform's attestations reported as conflicting evidence. | A2 "Outcomes"; v0.2 §5.3 |
| `transform_between` | Unreviewed transforms bearing on the answer are listed as alternatives. | v0.2 §6.2 |
| `where` | A derived candidate from a position disputed by an accepted denial is not INFERRED: the answer is not an undisputed INFERRED. | A2 "Provenance"; v0.2 §5.2 E6; common 0.7 |
| `where`, `poses` | The thing is judged with its established same-as group: asking by any member gives the same candidates. | ID-D 9, ID-8 |
| `poses` | Disputed entries cite both sides. | IB-D 4 |
| `frame_info` | Disputed transforms, anchors and positions are marked and cited on both sides. | IB-D 4 |
| `measurements` | An accepted denial is usable conflicting evidence. | v0.2 §6.2, §5.3; common §0.4 P-1 |
| `measurements` | Measurements of an alias are measurements of the bearer (selection by the whole identity class). | ID §3.8 ID-8 |
| `measurements` | `has-quality` content is reported in the SI unit. | D-C-1; v0.2 §3.3 |
| `compare_measurements` | An accepted assertion and an accepted denial of the measured content give DISPUTED, citing both, with or without `t`. | v0.2 §5.3; stage-c "Disputes" |
| `measurement_calibration` | The reference check "no certificate recorded" applies only when the instrument has no certificates. | d3 §3 |
| `causes_of` | A description-level claim answers an occurrence question only when both descriptions have usable describes links. | PLAN §9.3 "Lifting"; SB U-2 |
| `causes_of` | A lifted answer cites the describes links' attestations. | PLAN §9.3; SB "Lifting" |
| `causes_of` | A describes link whose judgement is DISPUTED is not accepted and does not lift. | SB U-2; V02 §3.2 |
| `explain` | Each initiating claim lists its attestations (required evidence may name them). | SB B0 |
| `changes` | An accepted "does not hold" side cites its deciding attestations. | SB Q-B1.2 |

"""


S01 = """### 0.1 Status of each statement
- **[E] Established:** an approved design text or semantic decision. The citation names it.
- **[P] Proposal (approved):** approved under LABS-1.063, some with qualifications (§0.10); part of the contract.
- A field, value, order or behaviour this edition does not fix is **not part of the contract**: a question must not
  expect it.

**E2 classes** (decided by the coordinator before you write gold; your assignment says which):
- **A/H (scored):** the approved semantics fixes the answer; write the gold from these contracts.
- **G (probe):** the capability is missing (a gap id), or approved but not provided (the §0.11 "G-unimpl" fields).
  A probe states its acceptable outcomes (UNKNOWN, NOT_YET_KNOWN, an established refusal, or the field `absent`) and
  what would be a fabricated answer.
- **Blocked:** ONT-SC-1 (self-causation). Never write a question, fixture or probe that depends on it.

Sources are cited by path and section; the cited documents are not part of the pack unless listed in its README.

"""


S011 = """All 25 semantic decisions are approved (LABS-1.064). Each statement below is established and overrides any other
text in this edition that seems to differ. **Consequence labels:** **eligible** (scored A/H); **G-unimpl** (the approved
field or capability is not provided yet: only a G probe may ask for it, accepting `absent`); **G-gap** (a gap probe);
**precondition** (never authored).

**SD-CAU-5 boundary examples (binding):**

| Case | Relation | Answer |
|---|---|---|
| a holds over `[10, 12)`, b over `[12, 14)`, exact bounds | `before(a, b)` | True (half-open: no shared instant) |
| a's end window `[11, 12]`, b's start window `[12, 13]`, both durative | `before(a, b)` | True |
| a and b instantaneous, both at exactly 12 | `before(a, b)`, `before(b, a)` | None both |
| a instantaneous with window `[10, 12]`, b instantaneous with window `[12, 14]` | `before(a, b)` | None |
| a instantaneous at 12, b durative starting at exactly 12 | `before(a, b)` | None |
| a durative ending at exactly 12, b instantaneous at 12 | `before(a, b)` | True |
| event start window `[9, 10]`, transition window with earliest possible instant 10 | B-time timing | consistent |
| event start window `[9, 11]`, transition window `[10, 12]` | B-time timing | unresolved |
| event start certainly after the transition's latest possible instant | B-time timing | excluded |
| explicit instantaneous measurement at 12, asked at t = 12 | `measurements(t=12)` | listed |
| attestation with an explicit empty interval `[12, 12)` (not a measurement instant) | any reader at t = 12 | holds at no instant |

**SD-MEA-6 in full:** calibration is established only when established throughout the entire possible activity-start
window; agreement at the earliest and latest bounds is insufficient; every internal validity and judgement transition
counts; no arbitrary instant is selected; where continuous establishment cannot be shown, the judgements found and any
dispute are kept and the answer is not "established".

**SD-CAU-1 in full:** an established outcome change, an accepted effect claim and an established causal attribution
are different things; none implies another. An accepted claim associated with an ambiguous transition does not
establish unique causation.

"""


def contracts():
    lines = (REPO / "benchmark/e2/spec/reader-contracts.md").read_text().split("\n")
    start = next(i for i, l in enumerate(lines) if l.startswith("## 0. Rules shared"))
    out, skip_block, skip_cont = [], False, None
    for l in lines[start:]:
        if skip_block:
            if l.startswith("---") or l.startswith("### ") or l.startswith("## "):
                skip_block = False
            else:
                continue
        if re.match(r"^\*\*Local items", l):
            skip_block = True
            continue
        if skip_cont is not None:                          # continuation lines of a dropped bullet
            if l.strip() and (len(l) - len(l.lstrip())) > skip_cont and not l.lstrip().startswith(("- ", "|")):
                continue
            skip_cont = None
        m = re.match(r"^(\s*)(- |\d+\. )(.*)$", l)
        if m and (re.match(r"^(\*\*)?([A-Z]{2}-\d+ )?\[D\]", m.group(3))
                  or re.match(r"^\[E\] (DI-\d+|ID-10|Performance)", m.group(3))
                  or re.match(r"^[A-Z]{2}-\d+\s*$", m.group(3))):
            skip_cont = len(m.group(1))
            continue
        if l.lstrip().startswith("|"):
            label_cells = l.split("|")
            if "[D]" in l and not re.search(r"\[(E|P)[^\]]*\]|\[P-", l):
                continue                                   # a row resting only on a discrepancy
        if "[D]" in l:
            l = strip_d_fragments(l)
        l = re.sub(r"\s*Corrections?: DI-\d+(, DI-\d+)*\.?", "", l)
        l = re.sub(r"\s*\([^()]*\b(DI-\d+|D-[A-Z]{2}-\d+|phys|DYN)\b[^()]*\)", "", l)   # cited defects / code
        l = re.sub(r"\s*See D-[A-Z]{2}-\d+\.?", "", l)
        l = re.sub(r";?\s*\bREG DI-\d+\b", "", l)
        l = re.sub(r"\|\s*D-[A-Z]{2}-\d+\s*\|", "| — |", l)
        l = re.sub(r"\*\*(RD|phys|spat|DYN|QUAL|LABM|ORGM|MOD|SEM)\*\*\s*`[^`]*`(\s*\(supplementary\))?[,;.]?", "", l)
        l = re.sub(r"\s*\(the harness passes both roles\)", "", l)
        out.append(l)
    text = "\n".join(out)
    s01 = text.index("### 0.1 Status of each statement"); s02 = text.index("### 0.2 Common inputs")
    text = text[:s01] + S01 + text[s02:]
    # section 0.11: drop the DI column
    text = text.replace("| Decision | Contract statement [E] | Consequence | DI |", "| Decision | Contract statement [E] | Consequence |")
    a = text.index("Every decision of the adjudication register")
    b = text.index("| Decision | Contract statement [E] | Consequence |")
    text = text[:a] + S011 + text[b:]
    k = text.index("\n## Part A.")
    text = text[:k + 1] + S012 + text[k + 1:]
    i = text.index("| Decision | Contract statement [E] | Consequence |")
    j = text.index("\n", i)
    text = text[:j + 1] + text[j + 1:].replace("|---|---|---|---|", "|---|---|---|", 1)
    return text


SUBST = [(r"\bDI-19\b", "the approved `constraint_support` rule"),
         (r"\bDI-7\b(, deferred)?", "no derivation record exists (deferred)"),
         (r"\bDI-1\b", "increment B"), (r"\bDI-11\b", "increment B"),
         (r"\(stage-c \"As implemented\"[^)]*\)", "(stage-c)"), (r"stage-c \"As implemented\"", "stage-c"),
         (r"\bD-A2-7 confirmed\b", "as confirmed in LABS-1.064")]


def final_filter(text):
    """Substitute the references that carry meaning; then drop every line the leak scan still flags, with the
    continuation lines of a dropped bullet. Section 0.11 rows lose their DI column instead."""
    out, cont = [], None
    for l in text.split("\n"):
        if re.match(r"^\| SD-[A-Z]+-\d+ \|", l):
            cells = l.split(" | ")
            l = " | ".join(cells[:-1]) + " |" if len(cells) == 4 else l
        for pat, rep in SUBST:
            l = re.sub(pat, rep, l)
        indent = len(l) - len(l.lstrip())
        if cont is not None:
            if l.strip() and indent > cont and not l.lstrip().startswith(("- ", "|", "1.", "2.", "3.")):
                continue
            cont = None
        if LEAK.search(l) or re.search(r"Blocked pending|not part of the E2 eligible|BLOCKED", l):
            if l.lstrip().startswith("- ") or re.match(r"^\s*\d+\. ", l):
                cont = indent
            continue
        out.append(l)
    return "\n".join(out)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "reader-contracts-author-edition.md").write_text(
        "# E2 reader contracts: author edition\n\n**Generated for the E2 author pack (LABS-1.065)** from "
        "`benchmark/e2/spec/reader-contracts.md` by `scripts/e2_author_pack.py`. Statements about how any program "
        "behaves have been removed; what remains is the approved semantics. Where a field or value is not fixed here, "
        "a question must not expect it.\n\n" + final_filter(contracts()) + "\n")
    hits, allowed = [], []
    for f in sorted(OUT.glob("*.md")):
        for n, l in enumerate(f.read_text().split("\n"), 1):
            if LEAK.search(l):
                (allowed if (f.name, l.strip()) in REVIEWED else hits).append(f"{f.name}:{n}: {l.strip()[:200]}")
    scan = ["# Author-pack leak scan (scripts/e2_author_pack.py)", f"unreviewed hits: {len(hits)}"] + hits + \
        [f"reviewed and kept (architectural statements, no reader behaviour): {len(allowed)}"] + allowed
    (OUT.parent / "author-pack-leak-scan.txt").write_text("\n".join(scan) + "\n")
    manifest = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(OUT.glob("*")) if f.is_file()
                and f.name != "MANIFEST.json"}
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print(f"{len(hits)} unreviewed leak-scan hits; {len(allowed)} reviewed; {len(manifest)} files hashed")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
