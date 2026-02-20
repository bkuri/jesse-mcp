# Jesse Bare Metal Integration Investigation

**Date**: 2026-02-19
**Status**: Investigation Complete - Mock Data Recommended
**Outcome**: Jesse multiprocessing issues prevent reliable API-based backtest result retrieval

---

## Executive Summary

Attempted to fix Jesse backtest integration by switching from Docker to bare metal installation. While workers complete successfully, they crash before persisting results to the database, making API-based result retrieval unreliable.

**Recommendation**: Use mock data for paper trading E2E tests. Jesse integration requires deeper investigation into multiprocessing and database connection handling.

---

## Problem Statement

### Original Issue
- Jesse Docker container spawns backtest workers via multiprocessing
- Workers fail with circular import error when using spawn mode
- Backtest sessions never complete or persist results

### Attempted Solution
- Install Jesse bare metal with Python 3.11 via pyenv
- Patch multiprocessing to use fork instead of spawn
- Run Jesse directly on host (no Docker isolation)

---

## Root Cause Analysis

### Docker Issue
Circular import error when spawning workers with spawn mode. Jesse forces spawn mode which creates fresh Python processes that hit circular imports when loading Jesse modules.

### Bare Metal Issue
Even with fork mode, database connections don't survive fork. Peewee ORM connection pool corrupted in child process. Workers crash before calling store_backtest_session().

---

## What Works

1. Direct Python backtest calls (same process)
2. Jesse API starts and accepts requests
3. Worker processes start
4. Removed finished worker messages appear

## What Doesn't Work

1. API-based backtest result retrieval
2. Session persistence after worker completes
3. Backtest log files (all 0 bytes)
4. Result caching

---

## Evidence

### Log Files (All 0 bytes)
All backtest log files are empty, indicating workers crash before writing.

### Database
No new sessions persisted after API calls. Only direct Python calls succeed.

### Worker Logs
Workers start and complete but session not found in database.

---

## Current State

**Working**:
- Jesse API on port 9200
- Strategy loading (4 strategies)
- Candle data (Binance Spot, BTC-USDT)
- Direct Python backtest calls
- mcproxy connects to Jesse

**Not Working**:
- API-based result retrieval
- Session persistence
- Log file writing

---

## Recommendations

1. Use mock data for paper trading E2E tests
2. For future Jesse integration, consider:
   - Reinitializing database in worker processes
   - Queue-based architecture with separate API/worker
   - Thread pool instead of process pool

---

*Full investigation details in JESSE_INVESTIGATION_INDEX.md*
