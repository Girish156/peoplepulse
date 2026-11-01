"""
PeoplePulse Determinism / Compare Runs Script
===============================================
Runs generate_data.py twice with the same seed and mode, then compares
all output file checksums and row counts.

Reports PASS if all checksums match, FAIL otherwise.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


GENERATOR_SCRIPT = os.path.join(os.path.dirname(__file__), "generate_data.py")
REPORTS_DIR = "data/reports"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def count_csv_rows(path: str) -> int:
    if not os.path.exists(path):
        return -1
    with open(path, newline="", encoding="utf-8") as f:
        # subtract 1 for header
        return max(0, sum(1 for _ in f) - 1)


def run_generator(seed: int, mode: str, output_dir: str, ground_truth_dir: str) -> bool:
    result = subprocess.run(
        [
            sys.executable, GENERATOR_SCRIPT,
            "--seed", str(seed),
            "--mode", mode,
            "--output-dir", output_dir,
            "--ground-truth-dir", ground_truth_dir,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  ERROR: Generator exited with code {result.returncode}")
        print(result.stderr)
        return False
    return True


def collect_checksums(directory: str) -> dict[str, str]:
    """Return {filename: sha256} for all files in directory."""
    checksums = {}
    if not os.path.isdir(directory):
        return checksums
    for fname in sorted(os.listdir(directory)):
        fpath = os.path.join(directory, fname)
        if os.path.isfile(fpath):
            checksums[fname] = sha256_file(fpath)
    return checksums


def collect_row_counts(directory: str) -> dict[str, int]:
    counts = {}
    if not os.path.isdir(directory):
        return counts
    for fname in sorted(os.listdir(directory)):
        if fname.endswith(".csv"):
            fpath = os.path.join(directory, fname)
            counts[fname] = count_csv_rows(fpath)
    return counts


def compare_runs(seed: int = 20261022, mode: str = "small") -> dict:
    print(f"[CompareRuns] Seed={seed}, Mode={mode}")

    with tempfile.TemporaryDirectory() as tmp:
        run1_out = os.path.join(tmp, "run1", "generated")
        run1_gt = os.path.join(tmp, "run1", "ground_truth")
        run2_out = os.path.join(tmp, "run2", "generated")
        run2_gt = os.path.join(tmp, "run2", "ground_truth")

        # Run 1
        print("[CompareRuns] Running generator (run 1)...")
        ok1 = run_generator(seed, mode, run1_out, run1_gt)
        if not ok1:
            return {"status": "FAIL", "reason": "Generator failed on run 1"}

        # Run 2
        print("[CompareRuns] Running generator (run 2)...")
        ok2 = run_generator(seed, mode, run2_out, run2_gt)
        if not ok2:
            return {"status": "FAIL", "reason": "Generator failed on run 2"}

        # Compare checksums
        cs1 = collect_checksums(run1_out)
        cs2 = collect_checksums(run2_out)
        gt_cs1 = collect_checksums(run1_gt)
        gt_cs2 = collect_checksums(run2_gt)

        rc1 = collect_row_counts(run1_out)
        rc2 = collect_row_counts(run2_out)

        mismatched_files = []
        all_files = sorted(set(cs1.keys()) | set(cs2.keys()))

        for fname in all_files:
            h1 = cs1.get(fname, "MISSING")
            h2 = cs2.get(fname, "MISSING")
            if h1 != h2:
                mismatched_files.append({
                    "file": fname,
                    "run1_checksum": h1,
                    "run2_checksum": h2,
                })

        gt_mismatched = []
        for fname in sorted(set(gt_cs1.keys()) | set(gt_cs2.keys())):
            h1 = gt_cs1.get(fname, "MISSING")
            h2 = gt_cs2.get(fname, "MISSING")
            if h1 != h2:
                gt_mismatched.append({
                    "file": fname,
                    "run1_checksum": h1,
                    "run2_checksum": h2,
                })

        row_count_mismatches = []
        for fname in sorted(set(rc1.keys()) | set(rc2.keys())):
            c1 = rc1.get(fname, -1)
            c2 = rc2.get(fname, -1)
            if c1 != c2:
                row_count_mismatches.append({
                    "file": fname,
                    "run1_rows": c1,
                    "run2_rows": c2,
                })

        all_matched = (
            len(mismatched_files) == 0 and
            len(gt_mismatched) == 0 and
            len(row_count_mismatches) == 0
        )

        report = {
            "seed": seed,
            "mode": mode,
            "status": "PASS" if all_matched else "FAIL",
            "files_compared": len(all_files),
            "mismatched_files": mismatched_files,
            "ground_truth_mismatches": gt_mismatched,
            "row_count_mismatches": row_count_mismatches,
            "run1_checksums": cs1,
            "run2_checksums": cs2,
            "run1_row_counts": rc1,
            "run2_row_counts": rc2,
        }

    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="PeoplePulse Determinism Checker")
    parser.add_argument("--seed", type=int, default=20261022)
    parser.add_argument("--mode", choices=["small", "full"], default="small")
    parser.add_argument("--reports-dir", default=REPORTS_DIR)
    args = parser.parse_args()

    report = compare_runs(args.seed, args.mode)

    os.makedirs(args.reports_dir, exist_ok=True)
    json_path = os.path.join(args.reports_dir, "compare_runs_report.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Also write markdown
    md_path = os.path.join(args.reports_dir, "compare_runs_report.md")
    lines = [
        "# PeoplePulse Determinism Check Report",
        "",
        f"**Seed**: {report['seed']}  ",
        f"**Mode**: {report['mode']}  ",
        f"**Status**: {'✅ PASS' if report['status'] == 'PASS' else '❌ FAIL'}",
        "",
        f"Files compared: {report['files_compared']}",
        "",
    ]

    if report["mismatched_files"]:
        lines += ["## Mismatched Files", ""]
        for m in report["mismatched_files"]:
            lines.append(f"- `{m['file']}`: run1={m['run1_checksum'][:16]}... run2={m['run2_checksum'][:16]}...")
        lines.append("")

    if report["row_count_mismatches"]:
        lines += ["## Row Count Mismatches", ""]
        for m in report["row_count_mismatches"]:
            lines.append(f"- `{m['file']}`: run1={m['run1_rows']} run2={m['run2_rows']}")
        lines.append("")

    if report["status"] == "PASS":
        lines += [
            "## ✅ All checksums and row counts match",
            "",
            "The generator is fully deterministic for the given seed and mode.",
        ]

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n[CompareRuns] Status: {report['status']}")
    print(f"  Files compared : {report['files_compared']}")
    print(f"  Mismatches     : {len(report['mismatched_files'])}")
    print(f"  Report written : {json_path}")

    sys.exit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
