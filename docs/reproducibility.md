# Reproducibility

English | [Bahasa Indonesia](reproducibility.id.md)

Use Python 3.12 and pinned runtime versions from `requirements.txt`. Jupyter
and build tools are optional extras. No private data, model training, API keys
or network downloads are used during notebook computation.

```sh
python -m unittest discover -s tests -v
python verify_chat.py --output work/acceptance
python scripts/execute_notebooks.py --output work/executed-notebooks
```

The execution script clears code outputs, starts a clean kernel per notebook,
executes every code cell, validates format and rejects error outputs. Figures
under `docs/figures/` are regenerated. `--in-place` refreshes checked-in outputs.
Runtime cell timestamps are removed to reduce irrelevant notebook diffs.

Notebook setup cells report versions, not personal paths. Seeds and all noise,
message and retry parameters are explicit. Different backend versions/platforms
can produce different random sequences even with equal seeds.

Check that four ideal symbols decode correctly; every encoded Bell state has
rho_B=I/2; accepted UTF-8 text equals what was sent; corrupt frames do not
produce guessed messages; every retry consumes fresh pairs and counts ACK cost.
Compare noisy samples with the ensemble and finite-sample uncertainty, keeping
receiver acceptance separate from sender confirmation.

Notebook 02 defines synthetic messages as transport fixtures. It does not
train a language model. Wilson intervals describe the chosen simulation, not
hardware performance or proof of no-signalling.

The source distribution includes docs/notebooks/tests. The wheel contains
the runtime and observer module. GitHub release artifacts include SHA-256
checksums. No PyPI publication or software DOI is implied.

Private mirroring copies Git branches/tags. GitHub issues, Actions logs and
release-asset metadata are not Git refs and are not copied by `push --mirror`.
