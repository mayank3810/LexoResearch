from __future__ import annotations

from app.compile.loader import load_world_model
from app.compile.validate import validate_world_model
from app.models.runtime import Observation, StartingBook, WorldSnapshot
from app.engine.propagate import run_tape

WORLD_A_SEED = [
    Observation(
        event_id="EVT-FY2028-COMMENTARY",
        outcome="confirmation_near_70_with_backlog",
        date="2026-11-17",
        adjudicated=True,
    )
]

WORLD_B_SEED = [
    Observation(
        event_id="EVT-CAPEX-MSFT",
        outcome="flat_or_down",
        date="2027-01-28",
        adjudicated=False,
    ),
    Observation(
        event_id="EVT-CAPEX-AMZN",
        outcome="flat_or_down",
        date="2027-01-30",
        adjudicated=False,
    ),
]


SEEDS = {
    "A": WORLD_A_SEED,
    "B": WORLD_B_SEED,
}


def seed_for(world_id: str) -> list[Observation]:
    key = world_id.upper()
    if key not in SEEDS:
        raise KeyError(world_id)
    return [Observation.model_validate(o.model_dump()) for o in SEEDS[key]]


class WorldSession:
    def __init__(self, world_id: str, seed: list[Observation]) -> None:
        self.world_id = world_id
        self.seed = [Observation.model_validate(o.model_dump()) for o in seed]
        self.observations = [Observation.model_validate(o.model_dump()) for o in seed]
        self.starting_book = StartingBook.FLAT

    def reset(self) -> None:
        self.observations = [Observation.model_validate(o.model_dump()) for o in self.seed]
        self.starting_book = StartingBook.FLAT

    def upsert(self, observation: Observation) -> None:
        for i, existing in enumerate(self.observations):
            if existing.event_id == observation.event_id:
                merged = observation.model_copy(
                    update={"adjudicated": observation.adjudicated or existing.adjudicated}
                )
                self.observations[i] = merged
                return
        self.observations.append(observation)

    def adjudicate(self, event_id: str, outcome: str) -> None:
        for i, existing in enumerate(self.observations):
            if existing.event_id == event_id:
                self.observations[i] = existing.model_copy(
                    update={"outcome": outcome, "adjudicated": True}
                )
                return
        self.observations.append(
            Observation(event_id=event_id, outcome=outcome, adjudicated=True)
        )


class SessionStore:
    def __init__(self) -> None:
        self.model = load_world_model()
        validate_world_model(self.model)
        self.worlds = {
            "A": WorldSession("A", WORLD_A_SEED),
            "B": WorldSession("B", WORLD_B_SEED),
        }

    def get(self, world_id: str) -> WorldSession:
        key = world_id.upper()
        if key not in self.worlds:
            raise KeyError(world_id)
        return self.worlds[key]

    def snapshot(self, world_id: str) -> WorldSnapshot:
        session = self.get(world_id)
        return run_tape(
            self.model,
            session.observations,
            session.starting_book,
            session.world_id,
        )

    def replay(self, world_id: str) -> WorldSnapshot:
        return self.snapshot(world_id)

    def compute(
        self,
        world_id: str,
        observations: list[Observation] | None = None,
        starting_book: StartingBook | None = None,
    ) -> WorldSnapshot:
        session = self.get(world_id)
        obs = observations if observations is not None else session.observations
        book = starting_book if starting_book is not None else session.starting_book
        return run_tape(self.model, obs, book, session.world_id)


store = SessionStore()
