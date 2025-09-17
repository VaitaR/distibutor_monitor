from __future__ import annotations

import datetime
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

from ..core.claims_aggregate import aggregate_claims, build_cumulative_series
from ..core.exports import build_snapshot, events_to_csv
from .state import ensure_session_state


def _format_last_update_time(last_sync_time: datetime.datetime | None) -> str:
    """Format the last sync time in a user-friendly way."""
    if last_sync_time is None:
        return "Never"

    now = datetime.datetime.now()
    diff = now - last_sync_time

    if diff.total_seconds() < 60:
        return f"{int(diff.total_seconds())} seconds ago"
    elif diff.total_seconds() < 3600:
        return f"{int(diff.total_seconds() // 60)} minutes ago"
    elif diff.total_seconds() < 86400:
        return f"{int(diff.total_seconds() // 3600)} hours ago"
    else:
        return last_sync_time.strftime("%Y-%m-%d %H:%M:%S")


def render_main() -> None:
    app = ensure_session_state(st)
    events: list[dict[str, Any]] = app.events

    # Use user-configured token decimals
    token_decimals = app.token_decimals
    agg = aggregate_claims(events, decimals=token_decimals)

    c1, c2, c3, c4 = st.columns(4)
    # Format the total claimed to show reasonable number of decimal places
    total_formatted = f"{agg.total_claimed_adj:.6f}".rstrip('0').rstrip('.')
    c1.metric("Total Claimed", total_formatted)
    c2.metric("Unique Claimers", agg.unique_claimers)
    c3.metric("Claims Count", agg.claims_count)
    c4.metric("Last Block", app.last_block)

    # Display last update time
    last_update_text = _format_last_update_time(app.last_sync_time)
    if app.last_sync_time is None:
        st.info(f"📊 **Last Updated:** {last_update_text}")
    else:
        # Show different colors based on how recent the update was
        now = datetime.datetime.now()
        if app.last_sync_time and (now - app.last_sync_time).total_seconds() < 300:  # Less than 5 minutes
            st.success(f"🔄 **Last Updated:** {last_update_text}")
        elif app.last_sync_time and (now - app.last_sync_time).total_seconds() < 1800:  # Less than 30 minutes
            st.info(f"🔄 **Last Updated:** {last_update_text}")
        else:
            st.warning(f"⚠️ **Last Updated:** {last_update_text} - Data may be outdated")

    # Cumulative chart
    series = build_cumulative_series(events, decimals=token_decimals)
    if series:
        df = pd.DataFrame(series, columns=["timestamp", "cumulative_adj"])
        # Convert timestamp to datetime for better chart display
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        # Convert Decimal to float for Altair compatibility
        df['cumulative_adj'] = df['cumulative_adj'].astype(float)

        chart = (
            alt.Chart(df)
            .mark_line()
            .encode(
                x=alt.X("datetime:T", title="Time"),
                y=alt.Y("cumulative_adj:Q", title="Cumulative Claimed")
            )
            .properties(height=240)
        )
        st.altair_chart(chart, use_container_width=True)

    if events:
        df_events = pd.DataFrame(events)
        df_events = df_events.sort_values(["timestamp", "block_number", "log_index"], ascending=True)

        # Add converted amount column
        if 'amount_raw' in df_events.columns:
            from decimal import Decimal
            df_events['amount'] = df_events['amount_raw'].apply(
                lambda x: float(Decimal(x) / (Decimal(10) ** token_decimals)) if x else 0
            )

        # Convert timestamp to readable datetime
        if 'timestamp' in df_events.columns:
            df_events['datetime'] = pd.to_datetime(df_events['timestamp'], unit='s')

        # Convert large integers to strings to avoid overflow in Streamlit
        for col in df_events.columns:
            if col in ['amount_raw', 'timestamp']:  # Keep these as strings to avoid overflow
                df_events[col] = df_events[col].astype(str)
            elif df_events[col].dtype in ['int64', 'object']:
                # Check if column contains large integers
                try:
                    max_val = df_events[col].max()
                    if isinstance(max_val, int) and abs(max_val) > 2**53:  # JavaScript safe integer limit
                        df_events[col] = df_events[col].astype(str)
                except (TypeError, ValueError):
                    pass

        # Reorder columns to show converted values first
        cols = list(df_events.columns)
        if 'amount' in cols and 'datetime' in cols:
            # Put converted columns first
            priority_cols = ['claimer', 'amount', 'datetime', 'tx_hash', 'block_number', 'log_index']
            ordered_cols = [col for col in priority_cols if col in cols]
            remaining_cols = [col for col in cols if col not in ordered_cols]
            df_events = df_events[ordered_cols + remaining_cols]

        st.dataframe(df_events, use_container_width=True, hide_index=True)

        cexp1, cexp2 = st.columns(2)
        with cexp1:
            csv_text = events_to_csv(events)
            st.download_button("Export CSV", data=csv_text, file_name="events.csv", mime="text/csv")
        with cexp2:
            snapshot = build_snapshot(chain=app.chain, contract=app.contract_address, events=events, decimals=token_decimals)
            st.download_button("Export Snapshot JSON", data=pd.Series(snapshot).to_json(), file_name="snapshot.json", mime="application/json")


