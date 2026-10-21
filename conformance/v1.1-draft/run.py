"""Discrimination check for the draft Raknor #3 / #4 vectors (stdlib only).

Runs each vector set against a conforming reference and against fail-open variants modelled on the
failures cited in the proposals. Vectors are useful only if the conforming reference passes all of them
and every variant fails at least one.
Usage: python3 run.py
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ALLOW, DENY = "ALLOW", "DENY"

# ---------- #3 fail-closed policy evaluation ----------

def evaluate_verdict(verdict):
    if isinstance(verdict, dict) and "raise" in verdict:
        raise RuntimeError("evaluator crashed")
    if isinstance(verdict, dict) and verdict.get("timeout"):
        raise TimeoutError("approver timed out")
    return verdict

def fc_conforming(policy, action, verdict):
    try:
        if policy.get("load_error") or policy.get("signature_valid") is False:
            return False, "policy_indeterminate"
        allow = policy.get("allowlist")
        if not allow:
            return False, "policy_indeterminate"
        if "*" not in allow and action not in allow:
            return False, None
        v = evaluate_verdict(verdict)
        if v == ALLOW:
            return True, None
        if v == DENY:
            return False, None
        return False, "policy_indeterminate"
    except Exception:
        return False, "policy_indeterminate"

def fc_empty_means_all(policy, action, verdict):  # crewAI #7778 / legacy agent-airlock shape
    try:
        if policy.get("load_error") or policy.get("signature_valid") is False:
            return False, "policy_indeterminate"
        allow = policy.get("allowlist")
        if allow and "*" not in allow and action not in allow:
            return False, None
        v = evaluate_verdict(verdict)
        return (v == ALLOW, None) if v in (ALLOW, DENY) else (False, "policy_indeterminate")
    except Exception:
        return False, "policy_indeterminate"

def fc_execute_unless_deny(policy, action, verdict):  # AutoGen #8301 shape
    r = fc_conforming(policy, action, ALLOW if verdict != DENY and not isinstance(verdict, dict) else verdict)
    return r

def fc_exception_allows(policy, action, verdict):  # evaluator error swallowed, unsigned policy accepted
    if policy.get("load_error"):
        return True, None
    allow = policy.get("allowlist") or []
    if not allow:
        return False, "policy_indeterminate"
    if "*" not in allow and action not in allow:
        return False, None
    try:
        v = evaluate_verdict(verdict)
    except Exception:
        return True, None
    return (v == ALLOW, None) if v in (ALLOW, DENY) else (False, "policy_indeterminate")

def fc_silent_deny(policy, action, verdict):  # denies correctly, never reports
    return fc_conforming(policy, action, verdict)[0], None

def run_fail_closed():
    vs = json.load(open(os.path.join(HERE, "fail-closed", "vectors.json")))["vectors"]
    impls = {"conforming": fc_conforming, "empty-means-all": fc_empty_means_all,
             "execute-unless-DENY": fc_execute_unless_deny, "exception-allows": fc_exception_allows,
             "silent-deny": fc_silent_deny}
    return report("#3 fail-closed", vs, impls,
                  lambda f, v: dict(zip(("executed", "event"), f(v["policy"], v["action"], v["verdict"]))) == v["expect"])

# ---------- #4 resource governance ----------

class Budget:
    def __init__(self, limit, fallback, ttl=None, lag=None, falsy_zero=False, reseed=False, silent=False):
        self.limit, self.fallback = limit, fallback
        self.ttl, self.lag = ttl, lag
        self.falsy_zero, self.reseed, self.silent = falsy_zero, reseed, silent
        self.spent, self.exceeded, self.last_touch, self.writes = 0, False, 0, []

    def _current_spend(self, t):
        if self.reseed and self.ttl is not None and t - self.last_touch > self.ttl:
            # counter expired: reseed from the durable store, which only reflects writes older than `lag`
            self.spent = sum(c for (tw, c) in self.writes if t - tw >= self.lag)
            self.exceeded = False
        return self.spent

    def request(self, t, cost):
        spent = self._current_spend(t)
        over = (self.exceeded or spent + cost > self.limit)
        if self.falsy_zero and not self.limit:
            over = False
        self.last_touch = t
        if over:
            self.exceeded = True
            if self.fallback:
                return ("degraded", None, None) if self.silent else ("degraded", "resource_degraded", self.fallback)
            return ("blocked", None, None)
        self.spent += cost
        self.writes.append((t, cost))
        if self.spent >= self.limit:
            self.exceeded = True
        return ("executed", None, None)

    def reset(self, t):
        self.spent, self.exceeded, self.writes, self.last_touch = 0, False, [], t

def budget_ok(make, v):
    b = make(v)
    for s in v["steps"]:
        if s.get("reset"):
            b.reset(s["t"])
            continue
        got, ev, marker = b.request(s["t"], s["cost"])
        if got != s["expect"]:
            return False
        if "expect_event" in s and (ev != s["expect_event"] or marker != s.get("expect_caller_marker")):
            return False
    return True

def run_budget():
    vs = json.load(open(os.path.join(HERE, "resource-governance", "vectors.json")))["vectors"]
    def mk(**kw):
        return lambda v: Budget(v["limit"], v["fallback"], v.get("counter_ttl_s"), v.get("persist_lag_s"), **kw)
    impls = {"conforming": mk(), "falsy-zero": mk(falsy_zero=True), "ttl-reseed": mk(reseed=True),
             "silent-fallback": mk(silent=True)}
    return report("#4 resource governance", vs, impls, lambda make, v: budget_ok(make, v))

# ---------- shared ----------

def report(title, vectors, impls, passes):
    print(f"== {title}: {len(vectors)} vectors")
    good = True
    for name, impl in impls.items():
        failing = [v["id"] for v in vectors if not passes(impl, v)]
        want_fail = name != "conforming"
        good &= bool(failing) == want_fail
        print(f"  {name:<20} {len(vectors) - len(failing)}/{len(vectors)}  failing: {', '.join(failing) or '-'}")
    return good

if __name__ == "__main__":
    ok = run_fail_closed() & run_budget()
    print("discriminates:", ok)
    raise SystemExit(0 if ok else 1)
