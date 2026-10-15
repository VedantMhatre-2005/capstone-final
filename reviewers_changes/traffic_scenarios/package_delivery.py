"""Package the reviewed report/data and exact source snapshots for handoff."""
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from .experiment import BACKEND, ROOT, dump


def main():
    output = ROOT / "reviewers_changes/yash_traffic_evaluation"
    assert json.loads((output / "results/delivery_verification.json").read_text())["passed"]
    # Plain-text LaTeX version of the completed manuscript draft.
    text = (output / "MANUSCRIPT_SECTION.md").read_text(encoding="utf-8")
    latex = ["% New experiment version: use with the paired tables in tables/legacy_tables.tex."]
    for line in text.splitlines():
        escaped = line.replace("%", r"\%").replace("&", r"\&").replace("_", r"\_")
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            latex.append(r"\subsection{" + escaped[3:] + "}")
        else:
            latex.append(escaped)
    (output / "MANUSCRIPT_SECTION.tex").write_text("\n".join(latex)+"\n", encoding="utf-8")
    source_dir = Path(__file__).parent
    sources = sorted(p for p in source_dir.iterdir() if p.is_file() and p.suffix in (".py", ".mjs", ".txt"))
    sources += [BACKEND / n for n in ("final_qaoa_with_signal.py", "pso.py", "graph.py",
                "predictions.py", "threshold.py", "run_publication_45_scenarios.py")]
    sources += [ROOT / "reviewers_changes/brute_force_comparison_results.csv"]
    snapshot = output / "reproduction/source_snapshot"
    for p in sources:
        target = snapshot / p.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(p.read_bytes())
    (output / "reproduction/README.md").write_text(
        "# Reproduction source snapshot\n\n"
        "The snapshot preserves repository-relative paths and exact source bytes, including the unchanged "
        "six backend modules used by the experiment and the previous CSV audited in the report. "
        "To rerun, use these files in a checkout of the original repository and follow the package README "
        "from that checkout's root. The runner records the checkout's Git commit as well as source hashes. "
        "The snapshot does not include a Git history or a Python environment.\n\n"
        "requirements-lock.txt pins the executed Python dependencies. The Excel builder uses the Codex "
        "bundled @oai/artifact-tool package; scientific CSV tables, figures, and manuscript text can be "
        "regenerated with Python independently of Excel export.\n", encoding="utf-8")
    excluded = {"workbook_data.json", "traffic_scenario_results.xlsx.inspect.ndjson"}
    files = sorted(p for p in output.rglob("*") if p.is_file() and p.name not in excluded and
                   "previews" not in p.relative_to(output).parts and p.name != "artifact_manifest.json")
    manifest = dict(files=[dict(path=str(p.relative_to(output)).replace("\\", "/"),
        bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files])
    dump(output / "artifact_manifest.json", manifest)
    archive = ROOT / "reviewers_changes/yash_traffic_evaluation.zip"
    with ZipFile(archive, "w", compression=ZIP_DEFLATED, compresslevel=7) as z:
        for p in files + [output / "artifact_manifest.json"]:
            z.write(p, Path("yash_traffic_evaluation") / p.relative_to(output))
    with ZipFile(archive) as z:
        assert z.testzip() is None
        assert len(z.namelist()) == len(files) + 1
    print(json.dumps(dict(archive=str(archive), files=len(files)+1, bytes=archive.stat().st_size), indent=2))


if __name__ == "__main__":
    main()
