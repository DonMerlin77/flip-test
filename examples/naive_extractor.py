import json
import sys

NOUNS = ["furnace", "forge", "smith", "guard", "cart", "supplies", "coal"]


def extract(inp):
    if isinstance(inp, dict):
        return {"answer_known": True}
    words = inp.lower().strip("?").split()
    found = sorted(w for w in words if w in NOUNS)
    out = {"intent": "ask_has", "object": found[0] if found else None}
    if len(found) > 1:
        out["subject"] = found[-1]
    return out


if __name__ == "__main__":
    raw = sys.stdin.read()
    inp = json.loads(raw) if raw.lstrip().startswith("{") else raw.strip()
    print(json.dumps(extract(inp)))
