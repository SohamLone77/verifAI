# COST_TRACKING
from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Optional

from app.models import Observation, State
from reward.cost_tracker import CostTracker


@dataclass
class EpisodeState:
    state: State
    obs: Observation
    episode_count: int
    cost_tracker: CostTracker


class SessionStore:
    """
    Thread-safe in-memory session store.

    Maps session_id -> (State, Observation) for active episodes.
    """

    def __init__(self) -> None:
        self._store: dict[str, EpisodeState] = {}
        self._lock = threading.Lock()

    def create(self, session_id: str, state: State, obs: Observation) -> None:
        with self._lock:
            self._store[session_id] = EpisodeState(
                state=state,
                obs=obs,
                episode_count=0,
                cost_tracker=CostTracker(),
            )

    def get(self, session_id: str) -> Optional[EpisodeState]:
        with self._lock:
            return self._store.get(session_id)

    def update(self, session_id: str, state: State, obs: Observation) -> None:
        with self._lock:
            if session_id in self._store:
                self._store[session_id].state = state
                self._store[session_id].obs = obs

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._store.pop(session_id, None)

    def exists(self, session_id: str) -> bool:
        with self._lock:
            return session_id in self._store

    def all_sessions(self) -> list[str]:
        with self._lock:
            return list(self._store.keys())

    def increment_episode(self, session_id: str) -> None:
        with self._lock:
            if session_id in self._store:
                self._store[session_id].episode_count += 1


# Singleton store — shared across all requests
session_store = SessionStore()
