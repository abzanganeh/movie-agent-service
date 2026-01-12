#!/usr/bin/env python3
"""
View and analyze CLI demo logs.

Usage:
    python demo/view_logs.py [log_file_path]
    
If no log file is specified, shows the most recent log file.
"""
import json
import sys
from pathlib import Path
from datetime import datetime


def format_timestamp(iso_str: str) -> str:
    """Format ISO timestamp to readable format."""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return iso_str


def print_entry(entry: dict, index: int):
    """Print a log entry in a readable format."""
    entry_type = entry.get("type", "unknown")
    timestamp = format_timestamp(entry.get("timestamp", ""))
    
    print(f"\n{'='*80}")
    print(f"[{index}] {entry_type.upper()} - {timestamp}")
    print(f"{'='*80}")
    
    if entry_type in ["chat", "game", "poster"]:
        print(f"Query: {entry.get('query', 'N/A')}")
    
    if entry_type.endswith("_response"):
        print(f"Answer: {entry.get('answer', 'N/A')}")
        if entry.get("movies"):
            print(f"Movies: {', '.join(entry['movies'])}")
        if entry.get("tools_used"):
            print(f"Tools Used: {', '.join(entry['tools_used'])}")
        if entry.get("llm_latency_ms"):
            print(f"LLM Latency: {entry['llm_latency_ms']}ms")
        if entry.get("tool_latency_ms"):
            print(f"Tool Latency: {entry['tool_latency_ms']}ms")
        if entry.get("title"):
            print(f"Title: {entry['title']}")
        if entry.get("inferred_genres"):
            print(f"Genres: {', '.join(entry['inferred_genres'])}")
        if entry.get("resolution_metadata"):
            print(f"Resolution Metadata: {json.dumps(entry['resolution_metadata'], indent=2)}")
    
    if entry_type == "error":
        print(f"Error Type: {entry.get('error_type', 'Unknown')}")
        print(f"Error Message: {entry.get('error', 'N/A')}")


def find_most_recent_log() -> Path:
    """Find the most recent log file."""
    logs_dir = Path("logs")
    if not logs_dir.exists():
        return None
    
    log_files = list(logs_dir.glob("cli_demo_*.log"))
    if not log_files:
        return None
    
    # Sort by modification time, most recent first
    log_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return log_files[0]


def main():
    """Main function."""
    if len(sys.argv) > 1:
        log_file = Path(sys.argv[1])
    else:
        log_file = find_most_recent_log()
    
    if not log_file or not log_file.exists():
        print("❌ No log file found.")
        print("\nUsage:")
        print("  python demo/view_logs.py [log_file_path]")
        print("\nOr run the CLI demo first to generate logs:")
        print("  PYTHONPATH=src python demo/cli_demo.py")
        return 1
    
    print(f"📝 Reading log file: {log_file}")
    print(f"   Size: {log_file.stat().st_size} bytes")
    print()
    
    entries = []
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('='):
                continue
            try:
                entry = json.loads(line)
                entries.append(entry)
            except json.JSONDecodeError:
                # Skip non-JSON lines (headers, footers)
                continue
    
    if not entries:
        print("No log entries found.")
        return 0
    
    print(f"Found {len(entries)} log entries\n")
    
    # Print all entries
    for i, entry in enumerate(entries, 1):
        print_entry(entry, i)
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total entries: {len(entries)}")
    
    entry_types = {}
    for entry in entries:
        entry_type = entry.get("type", "unknown")
        entry_types[entry_type] = entry_types.get(entry_type, 0) + 1
    
    print("\nEntry types:")
    for entry_type, count in sorted(entry_types.items()):
        print(f"  {entry_type}: {count}")
    
    # Error summary
    errors = [e for e in entries if e.get("type") == "error"]
    if errors:
        print(f"\n⚠️  Errors: {len(errors)}")
        for error in errors:
            print(f"  - {error.get('error_type', 'Unknown')}: {error.get('error', 'N/A')}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

