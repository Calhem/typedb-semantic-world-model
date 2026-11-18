# DI-16 clarification: identity merges on a disputed same-as (LABS-1.046)

**Status:** open. Not implemented and not closed; for review. Correction designed in
[pre-e-identity-design.md](pre-e-identity-design.md) (decisions ID-2, ID-5, ID-6).

## 1. Register entry (exact, as merged at `bf60c1f`)
From [deferred-issues.md](deferred-issues.md), the table row:

> | DI-16 | identity merges on a same-as whose canonical judgement is DISPUTED (accepted denials are ignored) | consolidation (LABS-1.045) | proposed: decide before Stage E | open (decision needed) |

and its section:

> ## DI-16: identity merges on a disputed same-as
> **What happens** (`probes/pre_e_consolidation.py`). `same-as(bea, b-smith)` is asserted and accepted, then denied by
> an accepted denial. Its canonical judgement is DISPUTED, but `Identity` unions every usable same-as assertion and
> ignores denials, so `identity()` still merges bea and b-smith, and an official act naming bea in one account and
> b-smith in another is **established**, not DISPUTED.
>
> **Classification.** Predates increment D and satisfies the Core 0.3 rule as written ("only accepted ones merge"), but
> since increment B every other content is judged by its canonical record; identity is the exception. Options: (a) merge
> only on an ESTABLISHED same-as, from the denial's recording time on (earlier views stay reproducible); (b) keep, and
> report the dispute beside merged answers; (c) keep and document. **Recommended:** decide before Stage E (a core
> semantic change, with its own design gate).

## 2. Reproduction
`uv run python -I probes/pre_e_di16_repro.py` (output `probes/pre_e_di16_repro.out.txt`): one throwaway database,
the core and the organisation profile, the code unchanged.
1. hr asserts `same-as(bea, b-smith)`; the system accepts it.
2. clerk denies it; the system accepts the denial as well.
3. Two accepted official acts describe one occurrence `o-2`: hr's names bea, clerk's names b-smith. Organisation 0.2
   declares the official single-valued (ER-6).

| Context | same-as judgement | Identity merges | Official of `o-2` | Correct? |
|---|---|---|---|---|
| system, now | DISPUTED (polarity) | **yes** | established: {bea, b-smith} as one player | **no**: the evidence is split on whether they are one person, so two accounts naming them are not agreement |
| system, as known before step 2 | established | yes | established: one player | yes (and must stay reproducible) |
| hr (accepts its own assertion; has not reviewed the denial) | established | yes | established: bea (hr has not accepted clerk's account) | yes |
| clerk (accepts its own denial; has not reviewed the assertion) | NOT_HOLDING (denied) | no | established: b-smith (clerk has not accepted hr's account) | yes |

Only a perspective that accepts both the assertion and the denial is affected, and only from the denial's recording
time on. The same defect appears in `probes/pre_e_identity_cases.out.txt` as I3 and I9, and in two forms the
register did not name: a chain merging two names whose own link is denied (I16, I18), and a hypothetical world whose
stipulated denial of an inherited link is ignored (I12).

A related finding made while reproducing it (F-1 in the identity design): the canonical judgement of a same-as content
is itself taken through identity, so a neighbouring link's dispute can make an established link read "disputed" (I18),
and a link with no record of its own can read "established" (I15). DI-16 and F-1 have one remedy: judge each link by
its stated names (ID-1), then merge only on established links (ID-2).

## 3. Impact
- **Reference worlds:** none. They hold no same-as content (0 in the rebuilt reference database), so neither baseline
  is affected.
- **Semantics:** wherever it applies, an answer that compares players or values under identity (role judgements,
  functional slots, `holds`, `value_at`) can be **established where it should be DISPUTED**, because two names are
  treated as one thing against accepted evidence. The answer cites its own support, not the identity it relied on, so
  the reader cannot see why.

## 4. Proposed decision
Adopt option **(a)**, as specified by the identity design:
- ID-2: two names are one thing only where their link is ESTABLISHED in the context (a DISPUTED or denied link joins
  nothing);
- ID-5: a group of names linked by established links that contains a pair whose own link is disputed or denied is not
  merged at all, and the conflict is reported;
- ID-6: the nearest world decides each link (a plan's denial applies in the plan);
- reproducibility as option (a) states: views at a knowledge time before the denial are unchanged.

LABS-1.046 item 2 already requires that disputed, denied, pending or contextually inapplicable same-as evidence must not
establish identity; option (a) is that requirement. Options (b) and (c) would leave the reproduction's first row as it
is. DI-16 stays **open** until this clarification and the identity design are reviewed; it would be closed only by the
merged identity increment, with the reproduction above as a permanent test (first row: the official DISPUTED, both
accounts cited; the other three rows unchanged).
