"""
reporter.py
Handles issue report collection and in-memory logging.
In production, replace the in-memory list with a database write
or an email/ticketing API call.
"""

import time
from dataclasses import dataclass, field


@dataclass
class IssueRecord:
    record_id: str
    location:  str
    issue_type: str
    description: str
    timestamp: str


_issues: list[IssueRecord] = []


def create_record(location: str, issue_type: str, description: str) -> IssueRecord:
    """Create, store, and return a new issue record."""
    record = IssueRecord(
        record_id   = f"ISS-{int(time.time())}",
        location    = location,
        issue_type  = issue_type,
        description = description,
        timestamp   = time.strftime("%Y-%m-%d %H:%M:%S"),
    )
    _issues.append(record)
    # TODO: replace with DB write / email / ticketing API call
    return record


def all_records() -> list[IssueRecord]:
    return list(_issues)


def format_record(r: IssueRecord) -> str:
    lines = [
        f"  Record ID : {r.record_id}",
        f"  Location  : {r.location}",
        f"  Type      : {r.issue_type}",
        f"  Timestamp : {r.timestamp}",
    ]
    if r.description:
        lines.append(f"  Details   : {r.description}")
    return "\n".join(lines)
