"""Benchmark script for job matching.

Usage:
    python -m scripts.benchmark_job_matching --job-file path/to/job.txt
"""

import argparse
import time

from rag_project.rag_core.app_facade import RAGApp
from rag_project.logger import get_logger


logger = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Benchmark job matching pipeline")
    parser.add_argument(
        "--job-file", required=True, help="Path to job description text file"
    )
    args = parser.parse_args()

    job_text = open(args.job_file, "r", encoding="utf-8").read()

    app = RAGApp()
    logger.info("Benchmark starting for job_file=%s", args.job_file)
    t0 = time.time()
    result = app.job_matching.analyze_match(job_text)
    elapsed = time.time() - t0
    logger.info(
        "Benchmark completed in %.2fs match_rate=%.1f", elapsed, result.match_rate
    )

    print(f"Elapsed: {elapsed:.2f}s")
    print(
        f"Match rate: {result.match_rate:.1f}% ({result.match_count}/{len(result.evaluations)})"
    )
    print("Matched requirements:")
    for ev in result.evaluations:
        if "MATCH" in ev.verdict.upper() and "MISSING" not in ev.verdict.upper():
            print(f"- {ev.requirement.name}: {ev.verdict} | {ev.reasoning}")
    print("Missing/partial requirements:")
    for ev in result.evaluations:
        if "MISSING" in ev.verdict.upper() or "PARTIAL" in ev.verdict.upper():
            print(f"- {ev.requirement.name}: {ev.verdict} | {ev.reasoning}")


if __name__ == "__main__":
    main()
