"""Independent commitment_anchor checker, written from the README rule text, not from check.py.

Usage: python3 indep_check.py vectors.json [--drop RULE]
RULE in: tolerance, digest, undeclared, unsupported (mutation test: disable one rule).
"""
import hashlib, json, sys

def nip01_id(ev):
    # NIP-01: sha256 of the UTF-8 JSON array [0, pubkey, created_at, kind, tags, content], no whitespace.
    payload = [0, ev["pubkey"], ev["created_at"], ev["kind"], ev["tags"], ev["content"]]
    return hashlib.sha256(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()

RULES = {"nip01-event-id": lambda rec: nip01_id(rec["subject"])}

def judge(rec, drop=None):
    anc = rec["commitment_anchor"]
    covers = drop == "digest" or RULES[anc["digest_rule"]](rec) == anc["digest"]
    if not covers:
        return {"result": "ANCHOR_DOES_NOT_COVER_RECORD", "precedence_established": False}
    tol = 0 if drop == "tolerance" else anc["anchor_time_tolerance_s"]
    est = anc["anchor_time"] + tol < rec["outcome_time"]
    claims = bool(rec.get("asserts_precedence"))
    declared = "precedence_before_outcome" in (rec.get("does_not_assert") or [])
    if not est and claims and drop != "unsupported":
        return {"result": "NONCONFORMING_UNSUPPORTED_PRECEDENCE_CLAIM", "precedence_established": est}
    if not est and not declared and drop != "undeclared":
        return {"result": "NONCONFORMING_UNDECLARED_LIMITATION", "precedence_established": est}
    return {"result": "CONFORMING", "precedence_established": est}

if __name__ == "__main__":
    path = sys.argv[1]
    drop = sys.argv[sys.argv.index("--drop") + 1] if "--drop" in sys.argv else None
    vs = json.load(open(path))["vectors"]
    fails = [v["id"] for v in vs if judge(v["record"], drop) != v["expect"]]
    print(f"drop={drop or 'none':<12} {len(vs) - len(fails)}/{len(vs)} agree  failing: {', '.join(fails) or '-'}")
    sys.exit(1 if fails else 0)
