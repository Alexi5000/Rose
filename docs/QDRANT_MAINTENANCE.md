Qdrant Maintenance and Recovery
=================================

When Qdrant returns 500 Internal Server Error with "OutputTooSmall" (gridstore panic), it's usually due to a corrupted segment or mismatch in payload / index.

Recommended steps (non-destructive first):

1. Capture logs
   - `docker-compose logs qdrant --tail 200`
   - Check for `OutputTooSmall` stack trace and segment IDs

2. Inspect collection via HTTP API or script
   - `python scripts/qdrant_inspect.py` (sets QDRANT_URL via env if needed)
   - Confirm `config.params.vectors.size` and `points_count`.

3. Restart Qdrant to check transient errors
   - `docker-compose restart qdrant` (may temporarily fix in-memory issues)

4. Backup data (good practice before destructive actions)
   - Copy the `./long_term_memory` folder to a safe location.

5. If errors persist (panics still occur):
   - Recreate collection with new name (recommended approach):
       1. Create a new collection with correct vector params.
       2. Re-ingest all known points (requires data source or backup). If no backup available, use short-term memory as fallback.
   - Avoid `drop` if you are unsure — this is destructive. Always backup first.

6. Consider upgrading Qdrant Docker image
   - Use the latest stable version which may contain fixes for Gridstore: `qdrant/qdrant:stable`.

7. Monitor and alert
   - The backend will raise `qdrant_unexpected_response` metric when Qdrant 500 occurs. Setup alerts for spikes.

8. Next steps if you need help
   - Share `qdrant` logs for the timeframe where internal panics occur.
   - Consider reproducing with a minimized dataset to report issue to Qdrant maintainers.

Be careful: Reindexing can be data-destructive; ensure backups and potentially production maintenance window.
