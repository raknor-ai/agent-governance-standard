# SC-OB-01: `commitment_anchor` (draft clause, agreed placement)

**Status:** the placement was agreed with the contributor on [#2](https://github.com/raknor-ai/agent-governance-standard/issues/2) on 2026-10-25. Nothing in this file is normative. The proposal still goes through the v1.1 disposition process when the window closes on 2026-11-30, and [STANDARD.md](../../STANDARD.md) is unchanged until then.

## Why SC-OB-01

SC-OB-01 already requires that decision records "MUST NOT be modifiable after creation" and that each record carries a timestamp. As written, an assessor can check neither without trusting the operator. `commitment_anchor` is what makes both checkable from outside.

## Draft clause

> A decision record that asserts it existed before its outcome SHALL carry a [`commitment_anchor`](https://github.com/probityai/agent-evidence/blob/36056a3bcb09/packages/vocabulary/vocabulary.yaml#L333) and SHALL satisfy the precedence rule. A record that does not establish precedence SHALL declare `precedence_before_outcome` in `does_not_assert`.

**Added failure condition:** a record asserts precedence that its anchor does not establish.

The `height` rule (anchor height strictly below outcome height) is preferred wherever the outcome is ordered by the same chain. It is the only form where the ledger is not also the source of the outcome time.

## Pinned references

| What | Pinned at |
|---|---|
| Field definition (term `commitment_anchor`, with companion `anchor_time_rule`) | probityai/agent-evidence vocabulary v0.7.0, [`36056a3b` `vocabulary.yaml#L333`](https://github.com/probityai/agent-evidence/blob/36056a3bcb09/packages/vocabulary/vocabulary.yaml#L333), merged in [#59](https://github.com/probityai/agent-evidence/pull/59) |
| Rule text and conformance vectors (21, CC0) | [`babyblueviper1/preaction-governance-conformance@e12d3e9`](https://github.com/babyblueviper1/preaction-governance-conformance/tree/e12d3e9a7e10/examples/commitment-anchor-obs06) |
| Independent rerun (21/21, five rules load-bearing) | [`obs06-rerun/`](obs06-rerun/), rerun 2 in `results.txt` |

References are pinned to commits, not branches, so a later edit upstream can't change what this clause tests.

## Attribution

Field design, rule text and vectors: @babyblueviper1 (CC0), who also corrected our median-time-past figure to 3,559 s. Vocabulary registration: probityai/agent-evidence (@astrogilda). Independent blind readings: Toshikatsu Oga. Proposed placement and independent rerun: this repository, on #2.
