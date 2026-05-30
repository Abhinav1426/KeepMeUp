"""
Content generator — refactored from `generate_content.py`.

Produces a large, varied text file for long typing sessions. Adds preset
selection (Programming / Business / Mixed) on top of the original snippet-pool
approach. The snippet content is preserved from the original generator.
"""

import os
import random


PYTHON_SNIPPETS = [
    '''def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


def fib_iter(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
''',
    '''def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)


def merge(left, right):
    result, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
''',
    '''class LRUCache:
    def __init__(self, capacity: int):
        from collections import OrderedDict
        self.capacity = capacity
        self.cache = OrderedDict()

    def get(self, key):
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
''',
    '''from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class User:
    id: int
    name: str
    email: str
    roles: List[str] = field(default_factory=list)

    def has_role(self, role: str) -> bool:
        return role in self.roles
''',
]

JAVASCRIPT_SNIPPETS = [
    '''const debounce = (fn, wait = 300) => {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn.apply(this, args), wait);
  };
};
''',
    '''async function fetchWithRetry(url, options = {}, retries = 3) {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      const res = await fetch(url, options);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      if (attempt === retries) throw err;
      await new Promise(r => setTimeout(r, 2 ** attempt * 100));
    }
  }
}
''',
]

SQL_SNIPPETS = [
    '''-- Find top spenders by month
SELECT
    DATE_TRUNC('month', o.created_at) AS month,
    c.name,
    SUM(o.total_cents) / 100.0 AS revenue
FROM orders o
JOIN customers c ON c.id = o.customer_id
WHERE o.status = 'completed'
GROUP BY 1, 2
ORDER BY month DESC, revenue DESC
LIMIT 100;
''',
]

PROSE_SNIPPETS = [
    """Architecture Decision Record: Move ingestion pipeline from cron to event-driven workers

Context: the nightly cron-based ETL has been failing intermittently when source files arrive late. Late files are silently dropped until the next run, causing downstream dashboards to under-report by 4-12 hours.

Decision: replace the cron-driven ingest with an event-driven worker that listens on the upload bucket. When a new file lands, a notification is published, fanned out to a queue, and consumed by a small fleet of idempotent workers.

Consequences: latency drops from up to 24h to under a minute. Operational surface increases — we now have a queue and DLQ to monitor.
""",
    """Code review notes — PR #4821

Overall this is a solid refactor and I'm in favor of merging once a few things are addressed. The split of the bloated handler module into request parsing, business logic, and persistence layers makes the call graph far easier to follow.

Concerns: the new RetryableError wrapper swallows the original exception's traceback in some paths. Please use raise NewError(...) from original so debugging stays usable.

Nits: rename process_v2 to something descriptive. Otherwise looks great.
""",
    """Incident retrospective — checkout service 500 spike, March 14

Summary: between 14:02 and 14:31 UTC, ~22% of checkout requests returned 500. Customer impact was limited because the client retries silently.

Root cause: a recent change to the inventory service introduced a per-request database connection rather than reusing the pooled connection. During a flash sale, connection exhaustion caused cascading timeouts in checkout.

Action items: revert to pooled connections. Add a connection-count alert. Add a load test to CI that mimics flash-sale concurrency.
""",
]


PRESETS = {
    "Programming": ([PYTHON_SNIPPETS, JAVASCRIPT_SNIPPETS, SQL_SNIPPETS], [6, 3, 2]),
    "Business Text": ([PROSE_SNIPPETS], [1]),
    "Mixed": ([PYTHON_SNIPPETS, JAVASCRIPT_SNIPPETS, SQL_SNIPPETS, PROSE_SNIPPETS], [5, 3, 2, 4]),
}


def generate_content(out_path: str, preset: str = "Mixed",
                     target_chars: int = 120_000, append: bool = False) -> int:
    """Write generated content to *out_path*. Returns final character count."""
    pools, weights = PRESETS.get(preset, PRESETS["Mixed"])

    existing = ""
    if append and os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            existing = f.read()

    parts = [existing.rstrip("\n"), "\n\n"] if existing else []
    total = len(existing)
    last = None
    while total < target_chars:
        pool = random.choices(pools, weights=weights)[0]
        s = random.choice(pool)
        if s is last:
            continue
        last = s
        parts.append(s)
        parts.append("\n\n")
        total += len(s) + 2

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("".join(parts))
    return os.path.getsize(out_path)
