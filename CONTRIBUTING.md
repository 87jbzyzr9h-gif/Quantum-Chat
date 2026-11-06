# Contributing

English | [Bahasa Indonesia](CONTRIBUTING.id.md)

Use Python 3.12 and install a fresh virtual environment:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[notebooks,dev]'
python -m unittest discover -s tests -v
python scripts/execute_notebooks.py --output work/executed-notebooks
python -m build
```

Keep simulated quantum resources separate from the classical TCP control plane.
Use one qsimcirq shot per freshly prepared pair. Changes to encoding, byte order,
frame validation or resource accounting need meaningful roundtrip/error tests.
Never feed sender truth, encoding choices or global states to the receiving
endpoint. Global-state access belongs only in observer tools and physics tests.

Notebook outputs should come from execution, with fixed seeds and complete
parameters. Do not hardcode success counts or train on evaluation messages.
Explain limitations and cite primary sources. Notebooks must run top to bottom
without network downloads, credentials, absolute personal paths or hidden state.

Update English/Indonesian document pairs together. Each notebook narrative
section and diagram label has both languages. Terminal messages use both
languages; code identifiers, commands, statuses, and JSON fields stay stable.
Scholarly titles and bibliography identifiers retain their original form.

For bug reports include the release version, OS, Python/dependency versions,
command, seed and a minimal synthetic message. Do not post private chat logs,
credentials or personal information. This preview server is localhost-only and
has no authentication/encryption; do not expose it as a public service.

Changes are contributed under the repository's MIT license.
