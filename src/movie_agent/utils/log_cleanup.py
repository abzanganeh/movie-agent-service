"""
Log cleanup utility for managing log file retention.

Cleanup Strategy:
1. Delete files older than max_age_days (if specified)
2. Keep only the most recent max_files (delete oldest if exceeded)

This ensures:
- Logs don't accumulate indefinitely
- Disk space is managed automatically
- Most recent logs are always preserved
"""
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def cleanup_logs(
    logs_dir: str,
    max_files: int = 10,
    max_age_days: Optional[int] = None,
    pattern: str = "*.log"
) -> int:
    """
    Clean up log files based on count and/or age.
    
    :param logs_dir: Directory containing log files
    :param max_files: Maximum number of log files to keep (keeps most recent)
    :param max_age_days: Maximum age in days (delete older files). If None, only count-based cleanup.
    :param pattern: Glob pattern for log files (default: "*.log")
    :return: Number of files deleted
    """
    logs_path = Path(logs_dir)
    
    if not logs_path.exists():
        return 0
    
    # Get all log files matching pattern
    log_files = list(logs_path.glob(pattern))
    
    if not log_files:
        return 0
    
    deleted_count = 0
    now = datetime.now()
    
    # Strategy 1: Delete files older than max_age_days
    if max_age_days is not None:
        cutoff_date = now - timedelta(days=max_age_days)
        for log_file in log_files:
            try:
                # Get file modification time
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if mtime < cutoff_date:
                    log_file.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted old log file: {log_file.name} (age: {(now - mtime).days} days)")
            except (OSError, Exception) as e:
                logger.warning(f"Failed to delete log file {log_file.name}: {e}")
        
        # Re-fetch remaining files after age-based deletion
        log_files = [f for f in logs_path.glob(pattern) if f.exists()]
    
    # Strategy 2: Keep only the most recent max_files
    if len(log_files) > max_files:
        # Sort by modification time (newest first)
        log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        # Delete files beyond the limit (oldest ones)
        files_to_delete = log_files[max_files:]
        for log_file in files_to_delete:
            try:
                log_file.unlink()
                deleted_count += 1
                logger.debug(f"Deleted log file (exceeded limit): {log_file.name}")
            except (OSError, Exception) as e:
                logger.warning(f"Failed to delete log file {log_file.name}: {e}")
    
    if deleted_count > 0:
        logger.info(f"Log cleanup: Deleted {deleted_count} log file(s) from {logs_dir}")
    
    return deleted_count

