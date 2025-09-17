# Distributor Monitor – Agent Brief

## What this project is
- Streamlit application to ingest on-chain Claim events from a distributor contract and present live metrics, tables, and exports.
- No persistent DB; all state lives in memory while the app is open.

## Core goals & KPIs
- **Metrics**: total_claimed, unique_claimers, claims_count, per-address distribution, cumulative timeline.
- **Exports**: CSV of events; JSON snapshot for distributor restarts.

## Architecture overview
- **UI**: `streamlit_app/app.py`, `streamlit_app/ui/{sidebar.py, state.py, views.py}`
- **Core**: `streamlit_app/core/{abi.py, decode.py, claims_aggregate.py, sync.py, app_logic.py, exports.py}`
- **Data sources**: `datasources/blockscout.py` (Etherscan-like logs API), `datasources/rpc.py` (Ankr JSON-RPC)
- **Config/Secrets**: `config.py`, `.env` (via `python-dotenv`)
- **Tests**: `tests/*` with `pytest` and `pytest-asyncio`

## Data flow (happy path)
- User selects network, enters contract address, uploads ABI.json.
- App finds Claim event(s) from ABI and lets the user select which to track.
- **Initial sync**: fetch historical logs via Blockscout pagination (page/offset) → decode → normalize → deduplicate by `(tx_hash, log_index)` → aggregate.
- **Live updates**: poll latest block from RPC, fetch new logs with an overlap window (`confirmation_blocks`) to tolerate short reorgs → decode → merge & dedup → update aggregates.
- UI shows metric cards, cumulative chart (Altair), and a sortable table; users can export CSV/JSON snapshot.

## State & caching
- **Session state** (`ui/state.py`): `events`, `last_block`, toggles (live, trigger_initial_sync), selected events, and parameters.
- **Dedup key**: `(tx_hash, log_index)` ensures idempotent pagination/live merges.
- Optional TTL caching can be added via Streamlit cache; no persistent storage by design.

## ABI & decoding
- **Load ABI**: `core/abi.py` (`load_abi_from_json`, `find_claim_events`).
- **Decode logs**: `core/decode.py` supports Claim(address,uint256)-like events and produces normalized records with fields: `claimer`, `amount_raw`, `tx_hash`, `block_number`, `log_index`, `timestamp`.

## Aggregation & exports
- **Aggregation**: `core/claims_aggregate.py` computes totals, per-address distribution (normalized by `decimals`), and cumulative series.
- **Exports**: `core/exports.py` has `events_to_csv` and snapshot `{ chain, contract, last_block, claimed_by }`.

## Sync logic
- **Initial**: `core/sync.py::initial_sync` → Blockscout fetch → decode → dedup → aggregate.
- **Incremental**: `core/sync.py::incremental_sync` → from_block with overlap → fetch/decode → merge/dedup → update cursor and aggregates.
- **Orchestration**: `core/app_logic.py` combines Blockscout + RPC flows (`run_initial_sync`, `run_live_tick`).

## Config & secrets
- **Networks**: `config.py` (`NETWORKS` for `mainnet` and `sepolia`). `resolve_network_config()` injects `ANKR_API_KEY` when present.
- **Secrets**: `.env` with `ANKR_API_KEY`, `ETHERSCAN_API_KEY` (Blockscout works without a key). Loaded on app start.

## Runbook (local)
- Python 3.11+
- Install: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Tests: `pytest -q` (plus `ruff` and `mypy --strict` are configured to be clean).
- Run: `source .venv/bin/activate && python -m streamlit run src/streamlit_app/app.py`
- Env: ensure `.env` has keys if using RPC fallback (`ANKR_API_KEY`), Etherscan key is optional.

## Key dependencies
- Streamlit, httpx, eth-abi, eth-utils, **eth-hash[pycryptodome]** (keccak), pandas, altair, structlog, python-dotenv, pytest(+asyncio), ruff, mypy.

## Testing strategy
- **Unit**: ABI parsing, log decoding, dedup, aggregation.
- **Integration (mocked)**: Blockscout pagination and incremental overlap; RPC `eth_blockNumber`.
- **App import smoke**: `tests/test_app_launch.py` (skips if Streamlit missing in test runtime).

## Error handling & reliability
- UI surfaces failures via `st.error` for Initial Sync and Live updates.
- Confirmation overlap guards against short reorgs.
- Idempotent merges via `(tx_hash, log_index)` dedup.

## Pitfalls / do not do
- **No relative imports in `app.py` under Streamlit**: use absolute imports (`streamlit_app.*`) and a minimal `sys.path` bootstrap to `src`.
- **Do not use `st.autorefresh`** (not a Streamlit API): use a minimal HTML meta refresh for live polling or a manual refresh with TTL cache.
- **Do not forget keccak backend**: install `eth-hash[pycryptodome]` or `event_abi_to_log_topic` will fail at runtime.
- **Do not run outside venv**: always `source .venv/bin/activate` to avoid missing modules.
- **Do not assume ABI upload auto-selects events**: ensure at least one Claim event is selected before syncing.
- Avoid heavy blocking operations in the UI; keep live poll intervals conservative to respect rate limits.

## Glossary
- **Blockscout client**: Etherscan-like logs API (page/offset) for historical/incremental fetch.
- **RPC client**: Ankr JSON-RPC (`eth_blockNumber`, potential `eth_getLogs` fallback).
- **Confirmation overlap**: blocks re-scanned per live tick for reorg tolerance.
- **Snapshot**: JSON mapping address → normalized amount; used to restart a distributor.
