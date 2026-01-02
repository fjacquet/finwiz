"""
Flow State Manager for discovering and managing persisted CrewAI flow states.

This module provides functionality to:
- Discover persisted flow states from CrewAI's SQLite storage
- Extract metadata from state files
- Prompt users for resume selection
- Load flow state data by UUID
- Clean up old state files
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class FlowStateManager:
    """Manages discovery and loading of persisted flow states."""

    def __init__(self) -> None:
        """Initialize FlowStateManager with CrewAI SQLite persistence location."""
        # CrewAI's SQLiteFlowPersistence stores in ~/Library/Application Support/{app_name}/
        self.state_dir = Path.home() / "Library" / "Application Support" / "finwiz"
        self.db_path = self.state_dir / "flow_states.db"

    def discover_persisted_states(self, limit: int = 10) -> list[dict]:
        """
        Discover unique persisted flow states from SQLite database.

        Args:
            limit: Maximum number of unique flow states to return (default: 10)

        Returns:
            List of state metadata dicts with: uuid, age_hours, last_update, etc.

        """
        states = []

        if not self.db_path.exists():
            logger.info(f"No flow states database found at {self.db_path}")
            return states

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Get unique flow UUIDs with their most recent timestamp
            cursor.execute(
                """
                SELECT flow_uuid, MAX(timestamp) as last_timestamp
                FROM flow_states
                GROUP BY flow_uuid
                ORDER BY last_timestamp DESC
                LIMIT ?
            """,
                (limit,),
            )

            unique_flows = cursor.fetchall()

            for flow_uuid, last_timestamp in unique_flows:
                try:
                    # Get the final state for this flow (run_sequential_workflow or report)
                    cursor.execute(
                        """
                        SELECT state_json, method_name, timestamp
                        FROM flow_states
                        WHERE flow_uuid = ?
                        ORDER BY timestamp DESC
                        LIMIT 1
                    """,
                        (flow_uuid,),
                    )

                    row = cursor.fetchone()
                    if not row:
                        continue

                    state_json, method_name, timestamp = row
                    state_data = json.loads(state_json) if state_json else {}

                    # Extract key state fields
                    session_id = state_data.get("session_id", "")
                    analysis_count = state_data.get("analysis_count", 0)
                    current_date = state_data.get("current_date", "")

                    # Parse timestamp for age calculation
                    try:
                        last_update = datetime.fromisoformat(timestamp) if timestamp else datetime.now()
                        # Handle timezone-aware timestamps
                        if last_update.tzinfo is not None:
                            last_update = last_update.replace(tzinfo=None)
                        age_hours = (datetime.now() - last_update).total_seconds() / 3600
                    except ValueError:
                        last_update = datetime.now()
                        age_hours = 0

                    # Determine completion status from final method
                    is_complete = method_name in ["report", "run_sequential_workflow"]

                    states.append(
                        {
                            "uuid": flow_uuid,
                            "method": method_name,
                            "session_id": session_id,
                            "analysis_count": analysis_count,
                            "current_date": current_date,
                            "age_hours": age_hours,
                            "last_update": last_update,
                            "is_stale": age_hours > 24,
                            "is_complete": is_complete,
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to parse state {flow_uuid}: {e}")

            conn.close()

        except Exception as e:
            logger.warning(f"Failed to read flow states database: {e}")

        return states

    def _extract_state_metadata(self, state_file: Path) -> dict | None:
        """
        Extract metadata from state file.

        Args:
            state_file: Path to SQLite state file

        Returns:
            Dict with metadata or None if extraction fails

        """
        try:
            conn = sqlite3.connect(str(state_file))
            cursor = conn.cursor()

            # Query latest state
            cursor.execute("""
                SELECT state_data, created_at 
                FROM flow_state 
                ORDER BY created_at DESC 
                LIMIT 1
            """)

            row = cursor.fetchone()
            if not row:
                conn.close()
                return None

            state_json, created_at = row
            state_data = json.loads(state_json)

            # Extract FinwizState fields
            holdings_processed = state_data.get("holdings_processed", 0)
            total_holdings = state_data.get("total_holdings", 0)
            flow_start_time = state_data.get("flow_start_time")

            # Calculate age
            if flow_start_time:
                start_dt = datetime.fromisoformat(flow_start_time)
                age_hours = (datetime.now() - start_dt).total_seconds() / 3600
            else:
                age_hours = 0

            conn.close()

            return {
                "uuid": state_file.stem,  # Filename without extension
                "file_path": str(state_file),
                "age_hours": age_hours,
                "holdings_processed": holdings_processed,
                "total_holdings": total_holdings,
                "progress_pct": (holdings_processed / total_holdings * 100) if total_holdings > 0 else 0,
                "last_update": datetime.fromtimestamp(state_file.stat().st_mtime),
                "is_stale": age_hours > 24,
            }

        except sqlite3.Error as e:
            logger.error(f"SQLite error extracting metadata from {state_file}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {state_file}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to extract metadata from {state_file}: {e}")
            return None

    def prompt_user_for_resume(self, states: list[dict]) -> str | None:
        """
        Prompt user to select a state to resume or start fresh.

        Args:
            states: List of state metadata dicts

        Returns:
            UUID to resume, or None to start fresh

        """
        if not states:
            return None

        print("\n" + "=" * 70)
        print("🔄 FOUND EXISTING FLOW STATES")
        print("=" * 70)

        for idx, state in enumerate(states, 1):
            age_str = f"{state['age_hours']:.1f}h ago"
            status_str = "✅ Complete" if state.get("is_complete") else "⏸️ Partial"
            stale_marker = " ⚠️ STALE" if state["is_stale"] else ""

            print(f"\n{idx}. UUID: {state['uuid'][:8]}...{stale_marker}")
            print(f"   Status: {status_str} (last step: {state['method']})")
            print(f"   Date: {state.get('current_date', 'N/A')} | Age: {age_str}")
            print(f"   Last Update: {state['last_update'].strftime('%Y-%m-%d %H:%M:%S')}")

        print(f"\n{len(states) + 1}. Start Fresh (new UUID)")
        print("=" * 70)

        while True:
            try:
                choice = input(f"\nSelect option (1-{len(states) + 1}): ").strip()
                choice_num = int(choice)

                if 1 <= choice_num <= len(states):
                    selected = states[choice_num - 1]

                    # Warn if stale
                    if selected["is_stale"]:
                        confirm = input(f"\n⚠️  State is {selected['age_hours']:.1f}h old (>24h). Resume anyway? (y/n): ").strip().lower()
                        if confirm != "y":
                            continue

                    print(f"\n✅ Resuming from UUID: {selected['uuid']}")
                    return str(selected["uuid"]) if selected["uuid"] else None

                elif choice_num == len(states) + 1:
                    print("\n✅ Starting fresh with new UUID")
                    return None

                else:
                    print(f"❌ Invalid choice. Please enter 1-{len(states) + 1}")

            except ValueError:
                print(f"❌ Invalid input. Please enter a number 1-{len(states) + 1}")
            except KeyboardInterrupt:
                print("\n\n❌ Cancelled by user")
                raise SystemExit(0)

    def load_flow_state_by_uuid(self, flow_uuid: str) -> dict | None:
        """
        Load flow state data by UUID from the SQLite database.

        Args:
            flow_uuid: UUID of the flow state to load

        Returns:
            State data dict or None if not found

        """
        if not self.db_path.exists():
            logger.error(f"Flow states database not found: {self.db_path}")
            return None

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Query state by flow_uuid (get most recent)
            cursor.execute(
                """
                SELECT state_json
                FROM flow_states
                WHERE flow_uuid = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """,
                (flow_uuid,),
            )

            row = cursor.fetchone()
            conn.close()

            if not row:
                logger.error(f"No state found for flow UUID: {flow_uuid}")
                return None

            state_data = json.loads(row[0]) if row[0] else {}
            return state_data

        except sqlite3.Error as e:
            logger.error(f"SQLite error loading state for {flow_uuid}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error loading state for {flow_uuid}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load state for {flow_uuid}: {e}")
            return None

    def cleanup_old_states(self, max_age_days: int = 7) -> int:
        """
        Clean up state entries older than max_age_days from the database.

        Args:
            max_age_days: Maximum age in days before deletion

        Returns:
            Number of state entries deleted

        """
        if not self.db_path.exists():
            return 0

        cutoff = datetime.now() - timedelta(days=max_age_days)
        cutoff_str = cutoff.isoformat()

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Count rows to be deleted
            cursor.execute(
                """
                SELECT COUNT(*) FROM flow_states
                WHERE timestamp < ?
            """,
                (cutoff_str,),
            )
            count = cursor.fetchone()[0]

            if count > 0:
                # Delete old entries
                cursor.execute(
                    """
                    DELETE FROM flow_states
                    WHERE timestamp < ?
                """,
                    (cutoff_str,),
                )
                conn.commit()
                logger.info(f"Deleted {count} old flow state entries (older than {max_age_days} days)")

            conn.close()
            return int(count) if count else 0

        except sqlite3.Error as e:
            logger.warning(f"Failed to cleanup old states: {e}")
            return 0
        except Exception as e:
            logger.warning(f"Failed to cleanup old states: {e}")
            return 0
