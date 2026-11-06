# Scientific notebooks

English | [Bahasa Indonesia](README.id.md)

Run with Python 3.12 after `python -m pip install -e '.[notebooks,dev]'`.
Select that environment's kernel and execute all cells top to bottom.
Every notebook narrative is available in Bahasa Indonesia and English, with
shared equations/code and bilingual figure labels and explanatory outputs.

1. **01_superdense_coding.ipynb**: conventions, Bell preparation, circuit,
   four-symbol qsim verification, partial trace and phase/coherence diagrams.
2. **02_quantum_chat_protocol.ipynb**: architecture, real two-way frame
   delivery, overhead, lost-ACK control, 100-message ideal/noisy trials and
   descriptive Wilson intervals.
3. **03_observer_and_noise.ipynb**: ten observer stages, phase versus
   population, exact mixed ensembles, sampled histograms and purity.

Each includes primary references, fixed seed, version output, actual executed
results, assertions and limitations. The figures are also exported to
`docs/figures/` as PNG/SVG. No downloaded dataset, credentials or training
corpus is required during execution.

Global-state inspection is an observer privilege, never an input to the chat
receiver. The localhost control plane is classical. A must be transferred in
the model before joint decoding; no physical qubit transfer is performed.

Re-execute without modifying checked-in outputs:

```sh
python scripts/execute_notebooks.py --output work/executed-notebooks
```

Use `--in-place` only when intentionally refreshing the scientific outputs.
Read [theory](../docs/theory.md) and [methodology](../docs/reproducibility.md)
for the assumptions and scope of numerical results.
