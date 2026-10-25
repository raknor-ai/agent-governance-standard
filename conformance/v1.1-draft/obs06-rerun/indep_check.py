"""Independent commitment_anchor checker, written from the upstream README rule text, not from check.py.

v2 follows the README at e12d3e9: three anchor_time_rule values, NIP-01 escaping, stated defaults, ordered results.
Usage: python3 indep_check.py vectors.json [--drop RULE]
RULE in: tolerance, digest, escaping, undeclared, unsupported (mutation test: disable one rule).
"""
import hashlib, json, sys

NIP01_ESC = {"\n": "\\n", '"': '\\"', "\\": "\\\\", "\r": "\\r", "\t": "\\t", "\b": "\\b", "\f": "\\f"}

def ser(x, json_default=False):
    if isinstance(x, str):
        if json_default:
            return json.dumps(x, ensure_ascii=False)
        return '"' + "".join(NIP01_ESC.get(c, c) for c in x) + '"'
    if isinstance(x, bool) or x is None:
        return json.dumps(x)
    if isinstance(x, int):
        return str(x)
    if isinstance(x, list):
        return "[" + ",".join(ser(i, json_default) for i in x) + "]"
    raise TypeError(f"unexpected type {type(x)} in NIP-01 event")

def nip01_id(ev, json_default=False):
    arr = [0, ev["pubkey"], ev["created_at"], ev["kind"], ev["tags"], ev["content"]]
    return hashlib.sha256(ser(arr, json_default).encode("utf-8")).hexdigest()

def covers(rec, drop):
    anc = rec.get("commitment_anchor")
    if not anc:
        return False
    if drop == "digest":
        return True
    if anc.get("digest_rule") != "nip01-event-id":
        return False
    return nip01_id(rec["subject"], json_default=(drop == "escaping")) == anc.get("digest")

def established(rec, drop):
    anc = rec["commitment_anchor"]
    rule = anc.get("anchor_time_rule", "header_time_plus_tolerance")
    if rule == "height":
        a, o = anc.get("anchor_height"), rec.get("outcome_height")
        return a is not None and o is not None and a < o
    o = rec.get("outcome_time")
    if o is None:
        return False
    if rule == "later_median":
        c = anc.get("anchor_ceiling_time")
        return c is not None and c < o
    if rule == "header_time_plus_tolerance":
        t, tol = anc.get("anchor_time"), anc.get("anchor_time_tolerance_s")
        if t is None or tol is None:
            return False
        return t + (0 if drop == "tolerance" else tol) < o
    return False

def judge(rec, drop=None):
    if not covers(rec, drop):
        return {"result": "ANCHOR_DOES_NOT_COVER_RECORD", "precedence_established": False}
    est = established(rec, drop)
    claims = rec.get("asserts_precedence") is True
    declared = "precedence_before_outcome" in (rec.get("does_not_assert") or [])
    if claims and not est and drop != "unsupported":
        return {"result": "NONCONFORMING_UNSUPPORTED_PRECEDENCE_CLAIM", "precedence_established": est}
    if not est and not claims and not declared and drop != "undeclared":
        return {"result": "NONCONFORMING_UNDECLARED_LIMITATION", "precedence_established": est}
    return {"result": "CONFORMING", "precedence_established": est}

if __name__ == "__main__":
    path = sys.argv[1]
    drop = sys.argv[sys.argv.index("--drop") + 1] if "--drop" in sys.argv else None
    vs = json.load(open(path))["vectors"]
    fails = [v["id"] for v in vs if judge(v["record"], drop) != v["expect"]]
    print(f"drop={drop or 'none':<12} {len(vs) - len(fails)}/{len(vs)} agree  failing: {', '.join(fails) or '-'}")
    sys.exit(1 if fails else 0)
