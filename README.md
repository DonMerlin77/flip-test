# flip-test

A small check for language models that turn text into structured data.

Ask a model "Does the furnace **need** supplies?" and it may answer as if you asked "Does the furnace **have** supplies?" Tested one question at a time, a model like that can look mostly fine. It gets some questions right by luck, because the word it ignores happens to match its default.

flip-test catches this with **pairs**: the same input twice, changed in one place, where that one change should change the answer. If the output does not change with it, the model is matching on familiar words, not reading the one that matters.

```
[STUCK] need-vs-has
  a: 'Does the furnace need supplies?'
  b: 'Does the furnace have supplies?'
  same answer on both sides for: intent
  a.intent: want 'ask_need', got 'ask_has'

0/4 pairs pass | 4 stuck (output did not flip) | 0 wrong
single questions right: 3/8 (what a one-at-a-time test would show)
```

That last line is the point. The same model scores 3 of 8 on single questions and 0 of 4 on pairs.

## Use it

Python 3.8+, no dependencies.

```bash
# your extractor is a command that reads one input on stdin and prints JSON
python3 flip_test.py pairs.jsonl --cmd "./my_extractor --schema npc.json"

# or a Python function
python3 flip_test.py pairs.jsonl --py my_module:extract
python3 flip_test.py pairs.jsonl --py path/to/file.py:extract
```

`--cmd` works with any language, so a C++ or Rust runtime can be tested without bindings. Text inputs are sent as plain text; object inputs (like a question plus facts) are sent as one line of JSON.

Exit code is 0 only if every pair passes, so it can gate a build or a fine-tune.

Add `--json` for the full results, including both raw outputs for every pair.

## Write pairs

One pair per line in a JSONL file. Each side has an `input` and the fields the output must match. Nested fields use dots (`question.type`).

```json
{"id": "need-vs-has", "a": {"input": "Does the furnace need supplies?", "expect": {"intent": "ask_need", "object": "furnace"}}, "b": {"input": "Does the furnace have supplies?", "expect": {"intent": "ask_has", "object": "furnace"}}}
```

Three verdicts:

- **PASS**: both sides right.
- **STUCK**: a field that should differ between the two sides came out the same. The model did not react to the change.
- **WRONG**: something is wrong, but the output did react to the change.

Pairs worth writing:

- **One word flips the meaning**: need / have, before / after, can / can't, all / some.
- **Swapped roles**: "Did the smith see the guard?" / "Did the guard see the smith?"
- **Answer present or missing**: the same question with the answer in the context and without it. A model that answers both the same way is copying a pattern (often a worked example from its prompt), not reading the context.

Tips:

- Change one thing per pair. If two things change, a pass doesn't tell you which one the model read.
- Write the first pairs from failures you have actually seen. Those are the shortcuts your model really takes.
- Pairs make good fine-tuning data too. Training on both sides of each pair gives the model no way to score well while skipping the word that changes.

## Check the checker

`examples/` has two extractors. The naive one only looks at keywords and should fail every pair. The reference one handles the example pairs and should pass. If the naive one ever passes, the pairs are too easy.

```bash
python3 flip_test.py examples/pairs.jsonl --py examples/naive_extractor.py:extract      # should fail
python3 flip_test.py examples/pairs.jsonl --py examples/reference_extractor.py:extract  # should pass
python3 -m unittest discover -s tests
```

## Background

The idea is not new. It comes from **contrast sets** (Gardner et al., 2020, "Evaluating Models' Local Decision Boundaries via Contrast Sets") and **counterfactually augmented data** (Kaushik et al., 2020, "Learning the Difference that Makes a Difference with Counterfactually-Augmented Data"). This repo is a small, practical version for extraction and NPC dialogue pipelines, where one misread word becomes a wrong game state.

## License

MIT
