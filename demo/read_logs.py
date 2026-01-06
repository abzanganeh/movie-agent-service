#!/usr/bin/env python3
"""
Simple utility to read and display CLI demo logs.

Usage:
    python demo/read_logs.py logs/cli_demo_20240101_120000.log
    python demo/read_logs.py logs/cli_demo_20240101_120000.log --pretty
    python demo/read_logs.py logs/cli_demo_20240101_120000.log --stats
"""
import json
import argparse
from pathlib import Path
from collections import defaultdict


def read_log_file(log_file: Path):
    """Read log file and return entries."""
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
                continue
    return entries


def print_pretty(entries):
    """Print log entries in a human-readable format."""
    for entry in entries:
        entry_type = entry.get('type', 'unknown')
        timestamp = entry.get('timestamp', '')
        
        if entry_type == 'chat' or entry_type == 'poster':
            print(f"\n[{timestamp}] Query ({entry_type}):")
            print(f"  {entry.get('query', '')}")
        
        elif entry_type.endswith('_response'):
            print(f"\n[{timestamp}] Response:")
            if 'answer' in entry:
                print(f"  Answer: {entry['answer']}")
            if 'movies' in entry and entry['movies']:
                print(f"  Movies: {', '.join(entry['movies'])}")
            if 'tools_used' in entry and entry['tools_used']:
                print(f"  Tools: {', '.join(entry['tools_used'])}")
            if 'latency_ms' in entry:
                print(f"  Latency: {entry['latency_ms']}ms")
            if 'title' in entry:
                print(f"  Title: {entry['title']}")
            if 'inferred_genres' in entry:
                print(f"  Genres: {', '.join(entry['inferred_genres'])}")
        
        elif entry_type == 'error':
            print(f"\n[{timestamp}] Error:")
            print(f"  Query: {entry.get('query', '')}")
            print(f"  Error: {entry.get('error', '')}")


def print_stats(entries):
    """Print statistics about the log entries."""
    stats = defaultdict(int)
    total_queries = 0
    total_responses = 0
    total_errors = 0
    total_latency = 0
    latency_count = 0
    
    for entry in entries:
        entry_type = entry.get('type', 'unknown')
        stats[entry_type] += 1
        
        if entry_type in ['chat', 'poster']:
            total_queries += 1
        elif entry_type.endswith('_response'):
            total_responses += 1
            if 'latency_ms' in entry and entry['latency_ms']:
                total_latency += entry['latency_ms']
                latency_count += 1
        elif entry_type == 'error':
            total_errors += 1
    
    print("\n" + "="*60)
    print("Session Statistics")
    print("="*60)
    print(f"Total queries: {total_queries}")
    print(f"Total responses: {total_responses}")
    print(f"Total errors: {total_errors}")
    
    if latency_count > 0:
        avg_latency = total_latency / latency_count
        print(f"Average latency: {avg_latency:.0f}ms")
    
    print("\nEntry types:")
    for entry_type, count in sorted(stats.items()):
        print(f"  {entry_type}: {count}")
    print("="*60)


def main():
    parser = argparse.ArgumentParser(description="Read and display CLI demo logs")
    parser.add_argument("log_file", type=Path, help="Path to log file")
    parser.add_argument("--pretty", action="store_true", help="Print in human-readable format")
    parser.add_argument("--stats", action="store_true", help="Print statistics")
    args = parser.parse_args()
    
    if not args.log_file.exists():
        print(f"Error: Log file not found: {args.log_file}")
        return 1
    
    entries = read_log_file(args.log_file)
    
    if not entries:
        print("No log entries found.")
        return 0
    
    if args.stats:
        print_stats(entries)
    elif args.pretty:
        print_pretty(entries)
    else:
        # Default: print raw JSON
        for entry in entries:
            print(json.dumps(entry, ensure_ascii=False, indent=2))
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

