# Reproduction source snapshot

The snapshot preserves repository-relative paths and exact source bytes, including the unchanged six backend modules used by the experiment and the previous CSV audited in the report. To rerun, use these files in a checkout of the original repository and follow the package README from that checkout's root. The runner records the checkout's Git commit as well as source hashes. The snapshot does not include a Git history or a Python environment.

requirements-lock.txt pins the executed Python dependencies. The Excel builder uses the Codex bundled @oai/artifact-tool package; scientific CSV tables, figures, and manuscript text can be regenerated with Python independently of Excel export.
