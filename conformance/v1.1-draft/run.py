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

def evaluate_verdict(verdict, policy=None):
    if isinstance(verdict, dict) and "raise" in verdict:
        raise RuntimeError("evaluator crashed")
    if isinstance(verdict, dict) and verdict.get("timeout"):
        raise TimeoutError("approver timed out")
    if isinstance(verdict, dict) and "value" in verdict:
        deadline = (policy or {}).get("approver_deadline_s")
        if deadline is not None and verdict.get("after_s", 0) > deadline:
            raise TimeoutError("no verdict by the declared approver deadline")
        return verdict["value"]
    return verdict

def recognised_entries(allow):
    # exact action ids (namespace:name) or the single wildcard "*"; other match-all spellings are unrecognised
    return all(e == "*" or ":" in e for e in allow)

def received_form(value, missing=False):
    if missing:
        return "missing"
    if value is None:
        return "null"
    if value == "" or value == []:
        return "empty"
    if isinstance(value, str):
        return "text"
    return "non_text"

def indeterminate(inp, value, missing=False):
    # the event carries the indeterminate input exactly as received (unnormalised) and its form
    # (value-as-received requirement from aigentical-ai, agentbaseline#49)
    return False, "policy_indeterminate", {"input": inp, "received_value": None if missing else value,
                                           "received_form": received_form(value, missing)}

def fc_conforming(policy, action, verdict):
    if policy.get("load_error") or policy.get("signature_valid") is False:
        return indeterminate("policy", policy)
    allow = policy.get("allowlist")
    if not allow or not recognised_entries(allow):
        return indeterminate("allowlist", allow)
    if "*" not in allow and action not in allow:
        return False, None, None
    try:
        v = evaluate_verdict(verdict, policy)
    except Exception:
        return indeterminate("verdict", None, missing=True)
    if v == ALLOW:
        return True, None, None
    if v == DENY:
        return False, None, None
    return indeterminate("verdict", v)

def fc_empty_means_all(policy, action, verdict):  # crewAI #7778 / legacy agent-airlock shape
    try:
        if policy.get("load_error") or policy.get("signature_valid") is False:
            return False, "policy_indeterminate"
        allow = policy.get("allowlist")
        if allow and "*" not in allow and action not in allow:
            return False, None
        v = evaluate_verdict(verdict, policy)
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
        v = evaluate_verdict(verdict, policy)
    except Exception:
        return True, None
    return (v == ALLOW, None) if v in (ALLOW, DENY) else (False, "policy_indeterminate")

def fc_silent_deny(policy, action, verdict):  # denies correctly, never reports
    return fc_conforming(policy, action, verdict)[0], None, None

def fc_alt_wildcard(policy, action, verdict):  # "all"/"any" accepted as match-all
    policy = dict(policy)
    if policy.get("allowlist"):
        policy["allowlist"] = ["*" if e in ("all", "any", ".*") else e for e in policy["allowlist"]]
    return fc_conforming(policy, action, verdict)

def fc_normalised_deny_log(policy, action, verdict):  # refuses correctly, logs every indeterminate case as a plain DENY
    executed, event, detail = fc_conforming(policy, action, verdict)
    if detail is not None:
        detail = {"input": detail["input"], "received_value": "DENY", "received_form": "text"}
    return executed, event, detail

def fc_passes(f, v):
    r = f(v["policy"], v["action"], v["verdict"])
    if (r[0], r[1]) != (v["expect"]["executed"], v["expect"]["event"]):
        return False
    if len(r) == 3 and "event_detail" in v["expect"]:
        return r[2] == v["expect"]["event_detail"]
    return True

def run_fail_closed():
    vs = json.load(open(os.path.join(HERE, "fail-closed", "vectors.json")))["vectors"]
    impls = {"conforming": fc_conforming, "empty-means-all": fc_empty_means_all,
             "execute-unless-DENY": fc_execute_unless_deny, "exception-allows": fc_exception_allows,
             "silent-deny": fc_silent_deny, "alt-wildcard-spelling": fc_alt_wildcard,
             "normalised-deny-log": fc_normalised_deny_log}
    return report("#3 fail-closed", vs, impls, fc_passes)

# ---------- #4 resource governance ----------

class Budget:
    def __init__(self, limit, fallback, ttl=None, lag=None, falsy_zero=False, reseed=False, silent=False,
                 cost_known="before", max_overshoot=None, window_s=None, unbounded_overshoot=False):
        self.limit, self.fallback = limit, fallback
        self.ttl, self.lag = ttl, lag
        self.falsy_zero, self.reseed, self.silent = falsy_zero, reseed, silent
        self.cost_known, self.max_overshoot, self.window_s = cost_known, max_overshoot, window_s
        self.unbounded_overshoot = unbounded_overshoot
        self.spent, self.exceeded, self.last_touch, self.writes = 0, False, 0, []
        self.window_start = 0

    def _current_spend(self, t):
        if self.reseed and self.ttl is not None and t - self.last_touch > self.ttl:
            # counter expired: reseed from the durable store, which only reflects writes older than `lag`
            self.spent = sum(c for (tw, c) in self.writes if t - tw >= self.lag)
            self.exceeded = False
        return self.spent

    def request(self, t, cost, max_cost=None):
        if self.window_s is not None and t >= self.window_start + self.window_s:
            # a scheduled window end is part of the configured limit: an explicit reset
            self.reset(t)
            self.window_start = t - (t % self.window_s)
        spent = self._current_spend(t)
        if self.cost_known == "after":
            # cost is known only once the call completes; admit a crossing request only within the declared bound
            bound = max_cost if max_cost is not None else cost
            if self.unbounded_overshoot:
                over = self.exceeded or spent >= self.limit
            else:
                over = (self.exceeded or spent >= self.limit or self.max_overshoot is None and spent + bound > self.limit
                        or self.max_overshoot is not None and spent + bound - self.limit > self.max_overshoot)
        else:
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
        got, ev, marker = b.request(s["t"], s["cost"], s.get("max_cost"))
        if got != s["expect"]:
            return False
        if "expect_event" in s and (ev != s["expect_event"] or marker != s.get("expect_caller_marker")):
            return False
    return True

def run_budget():
    vs = json.load(open(os.path.join(HERE, "resource-governance", "vectors.json")))["vectors"]
    def mk(**kw):
        return lambda v: Budget(v["limit"], v["fallback"], v.get("counter_ttl_s"), v.get("persist_lag_s"),
                                cost_known=v.get("cost_known", "before"), max_overshoot=v.get("max_overshoot"),
                                window_s=v.get("window_s"), **kw)
    impls = {"conforming": mk(), "falsy-zero": mk(falsy_zero=True), "ttl-reseed": mk(reseed=True),
             "silent-fallback": mk(silent=True), "unbounded-overshoot": mk(unbounded_overshoot=True)}
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
