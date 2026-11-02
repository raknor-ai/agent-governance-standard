# SC-OB-01: `commitment_anchor` (draft clause, agreed placement)

**Status:** the placement was agreed with the contributor on [#2](https://github.com/raknor-ai/agent-governance-standard/issues/2) on 2026-10-25. Nothing in this file is normative. The proposal still goes through the v1.1 disposition process when the window closes on 2026-11-30, and [STANDARD.md](../../STANDARD.md) is unchanged until then.

## Why SC-OB-01

SC-OB-01 already requires that decision records "MUST NOT be modifiable after creation" and that each record carries a timestamp. As written, an assessor can check neither without trusting the operator. `commitment_anchor` is what makes both checkable from outside.

## Draft clause

> A decision record that asserts it existed before its outcome SHALL carry a [`commitment_anchor`](https://github.com/probityai/agent-evidence/blob/36056a3bcb09/packages/vocabulary/vocabulary.yaml#L333), SHALL state the [`anchor_time_rule`](https://github.com/probityai/agent-evidence/blob/36056a3bcb09/packages/vocabulary/vocabulary.yaml#L363) under which precedence is evaluated (`header_time_plus_tolerance`, `later_median` or `height`), and SHALL satisfy the precedence rule under that stated rule. A record that does not establish precedence SHALL declare `precedence_before_outcome` in `does_not_assert`.

**Added failure condition:** a record asserts precedence that its anchor does not establish under its stated `anchor_time_rule`, or asserts precedence without stating one.

The `height` rule (anchor height strictly below outcome height) is preferred wherever the outcome is ordered by the same chain. It is the only form where the ledger is not also the source of the outcome time.

**Revision (2026-11-01):** the clause now requires the record to state its `anchor_time_rule`. The vocabulary proves a ceiling only under the rule the record states, so without it an assessor could not check precedence from the clause alone. Raised by @astrogilda on [#2](https://github.com/raknor-ai/agent-governance-standard/issues/2#issuecomment-6445413844).

**Open item:** the pinned vector `default-anchor-time-rule-absent` (at `e12d3e9`) asserts precedence with no stated rule and expects CONFORMING under the vocabulary's default. It conflicts with this revision until the contributor either keeps the default for records predating the field, or re-pins the vector as nonconforming ([#2](https://github.com/raknor-ai/agent-governance-standard/issues/2#issuecomment-6568609446)).

## Pinned references

| What | Pinned at |
|---|---|
| Field definition (term `commitment_anchor`, with companion `anchor_time_rule`) | probityai/agent-evidence vocabulary v0.7.0, [`36056a3b` `vocabulary.yaml#L333`](https://github.com/probityai/agent-evidence/blob/36056a3bcb09/packages/vocabulary/vocabulary.yaml#L333), merged in [#59](https://github.com/probityai/agent-evidence/pull/59) |
| Rule text and conformance vectors (21, CC0) | [`babyblueviper1/preaction-governance-conformance@e12d3e9`](https://github.com/babyblueviper1/preaction-governance-conformance/tree/e12d3e9a7e10/examples/commitment-anchor-obs06) |
| Vocabulary crosswalk mapping this clause | probityai/agent-evidence [#92](https://github.com/probityai/agent-evidence/pull/92) (merged 2026-10-29) |
| Independent rerun (21/21, five rules load-bearing) | [`obs06-rerun/`](obs06-rerun/), rerun 2 in `results.txt` |

References are pinned to commits, not branches, so a later edit upstream can't change what this clause tests.

## Attribution

Field design, rule text and vectors: @babyblueviper1 (CC0), who also corrected our median-time-past figure to 3,559 s. Vocabulary registration and crosswalk, and the `anchor_time_rule` revision: probityai/agent-evidence (@astrogilda). Independent blind readings: Toshikatsu Oga. Proposed placement and independent rerun: this repository, on #2.
