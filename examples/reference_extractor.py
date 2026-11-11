import json
import sys

PEOPLE = ["smith", "guard"]
STOP = {"does", "did", "the", "a", "when", "what", "need", "have", "see", "flour", "coal"}


def content_words(text):
    return [w.strip("?.,").lower() for w in text.split() if w.strip("?.,").lower() not in STOP]


def extract(inp):
    if isinstance(inp, dict):
        keys = set(content_words(inp["question"])) - {"arrive", "does"}
        known = any(keys & set(content_words(f)) for f in inp["facts"])
        return {"answer_known": known}
    words = [w.strip("?").lower() for w in inp.split()]
    people = [w for w in words if w in PEOPLE]
    if " see " in f" {inp.lower()} " and len(people) == 2:
        return {"intent": "ask_saw", "subject": people[0], "object": people[1]}
    intent = "ask_need" if "need" in words else "ask_has"
    obj = next((w for w in words if w not in STOP), None)
    return {"intent": intent, "object": obj}


if __name__ == "__main__":
    raw = sys.stdin.read()
    inp = json.loads(raw) if raw.lstrip().startswith("{") else raw.strip()
    print(json.dumps(extract(inp)))
