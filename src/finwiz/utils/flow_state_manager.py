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
        """Initialize FlowStateManager with CrewAI default state directory."""
        # CrewAI stores state in ~/.crewai/state/ by default
        self.state_dir = Path.home() / ".crewai" / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def discover_persisted_states(self) -> list[dict]:
        """
        Discover all persisted flow states.

        Returns:
            List of state metadata dicts with: uuid, age_hours, progress, last_update

        """
        states = []

        if not self.state_dir.exists():
            return states

        # Find all .db files (CrewAI SQLite persistence)
        for state_file in self.state_dir.glob("*.db"):
            try:
                metadata = self._extract_state_metadata(state_file)
                if metadata:
                    states.append(metadata)
            except Exception as e:
                logger.warning(f"Failed to read state {state_file}: {e}")

        # Sort by last update (newest first)
        states.sort(key=lambda x: x["last_update"], reverse=True)

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
            progress_str = f"{state['holdings_processed']}/{state['total_holdings']} ({state['progress_pct']:.1f}%)"
            stale_marker = " ⚠️ STALE" if state["is_stale"] else ""

            print(f"\n{idx}. UUID: {state['uuid'][:8]}...{stale_marker}")
            print(f"   Age: {age_str}")
            print(f"   Progress: {progress_str}")
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
                        confirm = (
                            input(f"\n⚠️  State is {selected['age_hours']:.1f}h old (>24h). Resume anyway? (y/n): ").strip().lower()
                        )
                        if confirm != "y":
                            continue

                    print(f"\n✅ Resuming from UUID: {selected['uuid']}")
                    return selected["uuid"]

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

    def load_flow_state_by_uuid(self, uuid: str) -> dict | None:
        """
        Load flow state data by UUID.

        Args:
            uuid: UUID of the flow state to load

        Returns:
            State data dict or None if not found

        """
        state_file = self.state_dir / f"{uuid}.db"

        if not state_file.exists():
            logger.error(f"State file not found: {state_file}")
            return None

        try:
            conn = sqlite3.connect(str(state_file))
            cursor = conn.cursor()

            cursor.execute("""
                SELECT state_data 
                FROM flow_state 
                ORDER BY created_at DESC 
                LIMIT 1
            """)

            row = cursor.fetchone()
            if not row:
                conn.close()
                return None

            state_data = json.loads(row[0])
            conn.close()

            return state_data

        except sqlite3.Error as e:
            logger.error(f"SQLite error loading state from {state_file}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error loading state from {state_file}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load state from {state_file}: {e}")
            return None

    def cleanup_old_states(self, max_age_days: int = 7) -> int:
        """
        Clean up state files older than max_age_days.

        Args:
            max_age_days: Maximum age in days before deletion

        Returns:
            Number of files deleted

        """
        if not self.state_dir.exists():
            return 0

        cutoff = datetime.now() - timedelta(days=max_age_days)
        deleted = 0

        for state_file in self.state_dir.glob("*.db"):
            try:
                mtime = datetime.fromtimestamp(state_file.stat().st_mtime)
                if mtime < cutoff:
                    state_file.unlink()
                    deleted += 1
                    logger.info(f"Deleted old state: {state_file.name}")
            except Exception as e:
                logger.warning(f"Failed to delete {state_file}: {e}")

        return deleted
