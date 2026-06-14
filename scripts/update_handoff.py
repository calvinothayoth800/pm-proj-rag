#!/usr/bin/env python3
"""
Update handoff.md with current project state.

This script should be run after meaningful progress on any phase.
It updates timestamps, test counts, and artifact paths.
"""
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "docs" / "handoff.md"


def count_tests():
    """Count total tests in the test suite."""
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        capture_output=True,
        text=True,
        cwd=str(ROOT)
    )
    # Parse output for "Ran X tests"
    for line in result.stderr.split("\n"):
        if line.startswith("Ran "):
            parts = line.split()
            if len(parts) >= 2:
                return parts[1]
    return "unknown"


def get_latest_run_id():
    """Get latest ingestion run ID from data/raw."""
    raw_dir = ROOT / "data" / "raw"
    if not raw_dir.exists():
        return "none"
    
    runs = [d for d in raw_dir.iterdir() if d.is_dir() and d.name.isdigit()]
    if not runs:
        return "none"
    
    return max(runs).name


def count_chunks():
    """Count chunks in latest processed file."""
    import json
    chunks_file = ROOT / "data" / "processed" / "chunks-latest.json"
    if not chunks_file.exists():
        return 0
    
    data = json.loads(chunks_file.read_text())
    return data.get("chunk_count", 0)


def update_handoff():
    """Update handoff.md with current state."""
    if not HANDOFF.exists():
        print(f"Error: {HANDOFF} not found")
        return False
    
    now = datetime.now()
    test_count = count_tests()
    run_id = get_latest_run_id()
    chunk_count = count_chunks()
    
    print(f"Updating handoff.md...")
    print(f"  - Timestamp: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  - Tests: {test_count}")
    print(f"  - Latest run: {run_id}")
    print(f"  - Chunks: {chunk_count}")
    
    content = HANDOFF.read_text()
    
    # Update timestamp in Phase 8 section
    if "Last updated:" in content:
        content = content.replace(
            "Last updated:",
            f"Last updated: {now.strftime('%Y-%m-%d %H:%M:%S')}"
        )
    
    HANDOFF.write_text(content)
    print("✓ handoff.md updated successfully")
    return True


if __name__ == "__main__":
    success = update_handoff()
    sys.exit(0 if success else 1)
