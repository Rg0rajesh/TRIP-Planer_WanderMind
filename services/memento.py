"""
Memento Design Pattern — Travel Preference Memory Layer
=========================================================
Originator  : UserProfile  — owns state, creates / restores snapshots
Memento     : TravelMemento — immutable state snapshot
Caretaker   : MemoryCaretaker — manages memento history + JSON persistence
"""

import json
import os
from datetime import datetime
from copy import deepcopy

MEMORY_PATH = os.path.join(os.path.dirname(__file__), "memory_store.json")


# ─── Memento (immutable snapshot) ────────────────────────────────────────────
class TravelMemento:
    def __init__(self, state: dict, label: str = ""):
        self._state = deepcopy(state)
        self._timestamp = datetime.now().isoformat()
        self._label = label

    def get_state(self) -> dict:
        return deepcopy(self._state)

    def get_timestamp(self) -> str:
        return self._timestamp

    def get_label(self) -> str:
        return self._label

    def to_dict(self) -> dict:
        return {
            "state": self._state,
            "timestamp": self._timestamp,
            "label": self._label,
        }

    @staticmethod
    def from_dict(d: dict) -> "TravelMemento":
        m = TravelMemento.__new__(TravelMemento)
        m._state = d["state"]
        m._timestamp = d["timestamp"]
        m._label = d.get("label", "")
        return m


# ─── Originator (owns current state) ─────────────────────────────────────────
class UserProfile:
    def __init__(self):
        self._state = {
            "name": "",
            "budget_preference": "",
            "interests": [],
            "home_city": "",
            "visited_destinations": [],
            "planned_trips": [],
            "chat_context": [],
            "preferred_duration": "",
            "travel_style": "",        # budget / comfort / luxury
            "dietary_preferences": [],
            "created_at": datetime.now().isoformat(),
        }

    # ── State mutators ────────────────────────────────────────────────────────
    def update(self, **kwargs):
        for k, v in kwargs.items():
            if k in self._state:
                self._state[k] = v

    def add_trip(self, trip: dict):
        trip["saved_at"] = datetime.now().isoformat()
        self._state["planned_trips"].append(trip)
        dest = trip.get("destination", "")
        if dest and dest not in self._state["visited_destinations"]:
            self._state["visited_destinations"].append(dest)
        # Keep last 20
        self._state["planned_trips"] = self._state["planned_trips"][-20:]

    def add_chat_message(self, role: str, content: str):
        self._state["chat_context"].append({
            "role": role,
            "content": content,
            "ts": datetime.now().isoformat(),
        })
        self._state["chat_context"] = self._state["chat_context"][-40:]

    def get_state(self) -> dict:
        return deepcopy(self._state)

    def get_context_summary(self) -> str:
        s = self._state
        parts = []
        if s["home_city"]:
            parts.append(f"Home city: {s['home_city']}")
        if s["budget_preference"]:
            parts.append(f"Typical budget: {s['budget_preference']}")
        if s["interests"]:
            parts.append(f"Interests: {', '.join(s['interests'])}")
        if s["travel_style"]:
            parts.append(f"Travel style: {s['travel_style']}")
        if s["dietary_preferences"]:
            parts.append(f"Dietary: {', '.join(s['dietary_preferences'])}")
        if s["visited_destinations"]:
            recent = s["visited_destinations"][-5:]
            parts.append(f"Recently planned: {', '.join(recent)}")
        return "\n".join(parts) if parts else "No prior preferences stored."

    # ── Memento interface ─────────────────────────────────────────────────────
    def save_to_memento(self, label: str = "") -> "TravelMemento":
        return TravelMemento(self._state, label=label)

    def restore_from_memento(self, memento: "TravelMemento"):
        self._state = memento.get_state()


# ─── Caretaker (manages history + persistence) ────────────────────────────────
class MemoryCaretaker:
    _MAX_HISTORY = 50

    def __init__(self):
        self._profile = UserProfile()
        self._history: list[TravelMemento] = []
        self._load()

    # ── Public API ────────────────────────────────────────────────────────────
    @property
    def profile(self) -> UserProfile:
        return self._profile

    def checkpoint(self, label: str = "auto-save"):
        """Snapshot current state and persist."""
        m = self._profile.save_to_memento(label=label)
        self._history.append(m)
        if len(self._history) > self._MAX_HISTORY:
            self._history = self._history[-self._MAX_HISTORY:]
        self._persist()

    def undo(self) -> bool:
        """Restore previous snapshot."""
        if len(self._history) < 2:
            return False
        self._history.pop()          # discard current
        self._profile.restore_from_memento(self._history[-1])
        self._persist()
        return True

    def get_history_summary(self) -> list[dict]:
        return [
            {"label": m.get_label(), "timestamp": m.get_timestamp()}
            for m in reversed(self._history[-15:])
        ]

    def get_trips(self) -> list[dict]:
        return self._profile.get_state().get("planned_trips", [])

    def context_summary(self) -> str:
        return self._profile.get_context_summary()

    def update_profile(self, **kwargs):
        self._profile.update(**kwargs)
        self.checkpoint(label="profile-update")

    def add_trip(self, trip: dict):
        self._profile.add_trip(trip)
        self.checkpoint(label=f"trip-{trip.get('destination','?')}")

    def add_chat(self, role: str, content: str):
        self._profile.add_chat_message(role, content)
        # Don't snapshot every message — batch persist
        self._persist()

    def get_chat_history(self) -> list[dict]:
        return self._profile.get_state().get("chat_context", [])[-20:]

    # ── Persistence ───────────────────────────────────────────────────────────
    def _persist(self):
        data = {
            "current_state": self._profile.get_state(),
            "history": [m.to_dict() for m in self._history],
        }
        try:
            with open(MEMORY_PATH, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[Memento] Persist error: {e}")

    def _load(self):
        if not os.path.exists(MEMORY_PATH):
            return
        try:
            with open(MEMORY_PATH) as f:
                data = json.load(f)
            # Restore current profile state
            if "current_state" in data:
                self._profile._state = data["current_state"]
            # Restore history
            if "history" in data:
                self._history = [TravelMemento.from_dict(d) for d in data["history"]]
        except Exception as e:
            print(f"[Memento] Load error: {e}")

    def clear(self):
        self._profile = UserProfile()
        self._history = []
        if os.path.exists(MEMORY_PATH):
            os.remove(MEMORY_PATH)


# ─── Singleton instance ───────────────────────────────────────────────────────
_caretaker: MemoryCaretaker | None = None

def get_memory() -> MemoryCaretaker:
    global _caretaker
    if _caretaker is None:
        _caretaker = MemoryCaretaker()
    return _caretaker
