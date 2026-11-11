import argparse
import importlib
import importlib.util
import json
import shlex
import subprocess
import sys
from pathlib import Path


def load_pairs(path):
    pairs = []
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        rec = json.loads(line)
        for side in ("a", "b"):
            if "input" not in rec[side] or "expect" not in rec[side]:
                raise ValueError(f"{path}:{n} side '{side}' needs 'input' and 'expect'")
        rec.setdefault("id", f"line{n}")
        pairs.append(rec)
    return pairs


def get_field(obj, dotted):
    for key in dotted.split("."):
        if not isinstance(obj, dict) or key not in obj:
            return None
        obj = obj[key]
    return obj


def command_extractor(cmd):
    argv = shlex.split(cmd)

    def run(inp):
        payload = inp if isinstance(inp, str) else json.dumps(inp)
        out = subprocess.run(argv, input=payload, capture_output=True, text=True, check=True).stdout
        return json.loads(out)

    return run


def python_extractor(spec):
    target, func = spec.rsplit(":", 1)
    if target.endswith(".py"):
        module_spec = importlib.util.spec_from_file_location("extractor_module", target)
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
    else:
        module = importlib.import_module(target)
    return getattr(module, func)


def judge_pair(pair, out_a, out_b):
    exp_a, exp_b = pair["a"]["expect"], pair["b"]["expect"]
    wrong = []
    for side, exp, out in (("a", exp_a, out_a), ("b", exp_b, out_b)):
        for field, want in exp.items():
            got = get_field(out, field)
            if got != want:
                wrong.append({"side": side, "field": field, "want": want, "got": got})
    flip_fields = [f for f in exp_a if f in exp_b and exp_a[f] != exp_b[f]]
    stuck = [f for f in flip_fields if get_field(out_a, f) == get_field(out_b, f)]
    if not wrong:
        verdict = "PASS"
    elif stuck:
        verdict = "STUCK"
    else:
        verdict = "WRONG"
    return {"id": pair["id"], "verdict": verdict, "stuck_fields": stuck, "wrong": wrong,
            "out_a": out_a, "out_b": out_b}


def run_pairs(pairs, extract):
    return [judge_pair(p, extract(p["a"]["input"]), extract(p["b"]["input"])) for p in pairs]


def summarize(results):
    counts = {"PASS": 0, "STUCK": 0, "WRONG": 0}
    for r in results:
        counts[r["verdict"]] += 1
    sides_wrong = sum(len({w["side"] for w in r["wrong"]}) for r in results)
    counts["single_correct"] = 2 * len(results) - sides_wrong
    return counts


def print_report(pairs, results):
    by_id = {p["id"]: p for p in pairs}
    for r in results:
        if r["verdict"] == "PASS":
            continue
        p = by_id[r["id"]]
        print(f"[{r['verdict']}] {r['id']}")
        print(f"  a: {p['a']['input']!r}")
        print(f"  b: {p['b']['input']!r}")
        if r["stuck_fields"]:
            print(f"  same answer on both sides for: {', '.join(r['stuck_fields'])}")
        for w in r["wrong"]:
            print(f"  {w['side']}.{w['field']}: want {w['want']!r}, got {w['got']!r}")
    c = summarize(results)
    total = len(results)
    print(f"\n{c['PASS']}/{total} pairs pass | {c['STUCK']} stuck (output did not flip) | {c['WRONG']} wrong")
    print(f"single questions right: {c['single_correct']}/{2 * total} (what a one-at-a-time test would show)")


def main():
    ap = argparse.ArgumentParser(description="Check that an extractor's output flips when one word of the input flips.")
    ap.add_argument("pairs", help="JSONL file of pairs")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--cmd", help="command that reads one input on stdin and prints JSON")
    src.add_argument("--py", help="python function, as module:func or path/to/file.py:func")
    ap.add_argument("--json", action="store_true", help="print full results as JSON")
    args = ap.parse_args()

    pairs = load_pairs(args.pairs)
    extract = command_extractor(args.cmd) if args.cmd else python_extractor(args.py)
    results = run_pairs(pairs, extract)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_report(pairs, results)
    sys.exit(0 if all(r["verdict"] == "PASS" for r in results) else 1)


if __name__ == "__main__":
    main()
