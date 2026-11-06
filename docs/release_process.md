# Public release and private mirror

`Quantum-Chat` is the canonical public repository. Its `origin` uses ordinary
branch/tag pushes, never `push --mirror` from the working checkout. The separate
`Quantum-Chat-Private` repository is a private Git mirror of the public branch
and tag history. It is not a private channel for chat messages or a cryptographic
feature of the simulator.

Release sequence:

1. Review source, notebook outputs and Git history for credentials/private data.
2. Execute unit/network tests, acceptance trials, every notebook, and package build.
3. Push the release commit normally to public `main`, then wait for CI.
4. Create a version tag and a research-preview GitHub release with source,
   wheel/notebook bundle and SHA-256 checksums. MIT and CFF metadata accompany it.
5. Synchronize the dedicated private mirror and compare all branch/tag object IDs.

Mirror helper (Git and authenticated GitHub CLI required):

```sh
python scripts/sync_private_mirror.py         # inspect dry-run first
python scripts/sync_private_mirror.py --apply # mirror branches/tags
```

The helper verifies the destination is private, refuses identical source and
destination, uses a dedicated bare repository, and fetches only project
branches/tags. Editor/Codex refs, local virtualenvs, chat logs and ignored work
files are never mirrored. Mirror semantics update or delete destination refs to
match the source. GitHub issues, Actions logs and release assets are not Git refs
and are not replicated by this operation. No token is stored in the repository.

The initial public release is `v0.1.0`, marked as a research preview. There is no
PyPI publication, software DOI, hardware link or peer-review claim.
