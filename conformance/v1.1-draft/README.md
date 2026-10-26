# v1.1 draft conformance material

Test material for proposals in the v1.1 window, which closes 2026-11-30. **Nothing here is normative.** These files test proposed text so the proposals can be evaluated. They do not change [STANDARD.md](../../STANDARD.md), and they don't signal that any proposal will be accepted.

**License:** the files in this directory are dedicated to the public domain under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/), so any implementation or test suite can use them without attribution. This is a deliberate exception to the repository's CC BY 4.0 default.

## Contents

| Path | Proposal | What it is |
|---|---|---|
| [`fail-closed/vectors.json`](fail-closed/vectors.json) | [#3 SC-AG-07 Fail-closed policy evaluation](https://github.com/raknor-ai/agent-governance-standard/issues/3) | 14 black-box vectors for clauses (a)–(d), including 4 positive controls |
| [`resource-governance/vectors.json`](resource-governance/vectors.json) | [#4 SC-AG-05 resource limits and declared degradation](https://github.com/raknor-ai/agent-governance-standard/issues/4) | 6 timed vectors for clauses 1–3, including 2 positive controls |
| [`run.py`](run.py) | #3, #4 | Checks that the vectors tell a conforming reference apart from fail-open variants |
| [`sc-ob-01-commitment-anchor.md`](sc-ob-01-commitment-anchor.md) | [#2 evidence field set](https://github.com/raknor-ai/agent-governance-standard/issues/2) | Draft SC-OB-01 clause with the placement agreed with the contributor; references pinned to commits |
| [`obs06-rerun/`](obs06-rerun/) | [#2 evidence field set](https://github.com/raknor-ai/agent-governance-standard/issues/2) | Independent rerun of the contributed `commitment_anchor` vectors |

## Vector format

Each vector describes a system state and a stimulus, plus the outcome expected through the system's API: whether the action ran, and which governance event (SC-OB-03) was emitted, if any. Vectors marked `positive_control` must pass. They stop a system from scoring well just by denying everything.

## Discrimination check

```
python3 run.py
```

This runs each vector set against a conforming reference implementation and against fail-open variants modelled on the failures cited in the proposals. The check passes only if the reference passes every vector and every variant fails at least one.

The reference implementations are models of the cited failure mechanisms. They are **not** reproductions of crewAI, AutoGen, LiteLLM or agent-airlock. Runtime reproductions against those projects are still outstanding.

## OBS-06 rerun

`obs06-rerun/` reruns [babyblueviper1's `commitment_anchor` vectors](https://github.com/babyblueviper1/preaction-governance-conformance/tree/e12d3e9/examples/commitment-anchor-obs06). Rerun 1 (2026-10-21) used commit `a2949a7` (6 vectors). Rerun 2 (2026-10-25) used `e12d3e9` (21 vectors, three `anchor_time_rule` values, NIP-01 escaping), with the checker rewritten from that README. Both are recorded in `results.txt`, along with a correction to rerun 1's median-time-past figure:

- `indep_check.py` is a checker written from the upstream README's rule text, without reference to the upstream `check.py`. `--drop RULE` disables one rule, to test whether each rule is load-bearing.
- `verify_ots.py` replays the OpenTimestamps proof to its Bitcoin attestation and compares the merkle root with block headers from two public explorers. It uses no local node and doesn't rely on the ledger operator. It requires `pip install opentimestamps`.
- `results.txt` holds the recorded output, with sha256 hashes of the upstream inputs.

To reproduce:

```
git clone https://github.com/babyblueviper1/preaction-governance-conformance && cd preaction-governance-conformance && git checkout e12d3e9
cd examples/commitment-anchor-obs06
python3 <this-dir>/obs06-rerun/indep_check.py vectors.json
python3 <this-dir>/obs06-rerun/verify_ots.py 38.ots a42205d7e39c684f0aa43f80fe7ea1aa8e180df93ff46e82b5bff95b70c663e9
```

**Not verified by this rerun:** the real vector's outcome time, which is asserted by the ledger; the NIP-01 event signature; and block data independent of the two explorers.
