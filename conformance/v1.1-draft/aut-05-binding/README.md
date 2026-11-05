# AUT-05 approval-binding cases

Two negative cases for independent approval, binding an approval to the exact request it authorised. Transcribed from [agentbaseline/agentbaseline#28](https://github.com/agentbaseline/agentbaseline/issues/28). **Non-normative.** The cases map to Agent Baseline **AUT-05** (independent approval) and Raknor **SC-SR-03** (human-in-the-loop).

| File | Case |
|---|---|
| [`aut05-binding-03-approval-scope.yaml`](aut05-binding-03-approval-scope.yaml) | (3) Approval scope: an approval spent on a different interface |
| [`aut05-binding-04-enforcement-context.yaml`](aut05-binding-04-enforcement-context.yaml) | (4) Enforcement context: one added field weakens inspection |

## Provenance

- **Cases:** written by aigentical-ai ([finding](https://github.com/agentbaseline/agentbaseline/issues/28#issuecomment-5625641344), [cases](https://github.com/agentbaseline/agentbaseline/issues/28#issuecomment-5818941784)). Inputs are synthetic. Their own runs are application-boundary runs.
- **Verification notes:** owenshuo ([2026-10-21](https://github.com/agentbaseline/agentbaseline/issues/28#issuecomment-6309618292)), on a synthetic reference target and on a pinned application. Their evidence-scope classifications are quoted exactly, including "not applicable" and "partial analogue only", and are kept separate from the cases. Nothing here restates them as stronger claims.
- **Consent and licence:** aigentical-ai agreed to this location, the format and CC0 on [2026-11-05](https://github.com/agentbaseline/agentbaseline/issues/28#issuecomment-6646060809). owenshuo is asked on #28 to confirm the transcription of their labels, or to send their own files to replace these.

All wording is quoted from the source comments, and field names follow the format proposed on #28. The source states every field, so none is null. The `binding_fields` values (`issuing_surface`, `complete_effective_request`) are short labels for the dimensions quoted beside them.

## Upstream priority

If Agent Baseline settles on an upstream home for test vectors, that home takes priority. These files will point there and stop being treated as the reference.
