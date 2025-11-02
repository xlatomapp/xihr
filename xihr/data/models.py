"""Core data models for races, horses, and payoffs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple


class ValidationError(ValueError):
    """Raised when a record fails validation."""


@dataclass(slots=True)
class HorseEntryModel:
    """Model representing a horse participating in a race."""

    race_id: str
    horse_id: str
    name: str
    jockey: str
    trainer: str
    draw: int
    odds: Dict[str, float]

    @classmethod
    def model_validate(cls, payload: Mapping[str, Any]) -> "HorseEntryModel":
        """Validate ``payload`` and return a :class:`HorseEntryModel`."""

        try:
            race_id = str(payload["race_id"])
            horse_id = str(payload["horse_id"])
            name = str(payload["name"])
            jockey = str(payload["jockey"])
            trainer = str(payload["trainer"])
            draw = int(payload["draw"])
            raw_odds = payload.get("odds", {})
        except KeyError as exc:
            raise ValidationError(f"Missing horse field: {exc.args[0]}") from exc
        if draw < 1:
            raise ValidationError(f"Horse draw must be >= 1, got {draw}")
        if isinstance(raw_odds, str) and raw_odds:
            raw_odds = json.loads(raw_odds)
        if not isinstance(raw_odds, Mapping):
            raise ValidationError("Horse odds must be a mapping of bet type to price")
        odds: Dict[str, float] = {}
        for bet_type, value in raw_odds.items():
            price = float(value)
            if price <= 0:
                raise ValidationError(f"Odds for {bet_type} must be positive, got {price}")
            odds[str(bet_type)] = price
        return cls(
            race_id=race_id,
            horse_id=horse_id,
            name=name,
            jockey=jockey,
            trainer=trainer,
            draw=draw,
            odds=odds,
        )

    def get_horse(self, horse_id: str) -> "HorseEntryModel" | None:
        """Return the horse with the given identifier if present."""

        return self if self.horse_id == horse_id else None


@dataclass(slots=True)
class RaceModel:
    """Model representing a race card entry."""

    race_id: str
    date: datetime
    course: str
    distance: int
    ground: str
    weather: str
    horses: List[HorseEntryModel]

    @classmethod
    def model_validate(cls, payload: Mapping[str, Any]) -> "RaceModel":
        """Validate ``payload`` and return a :class:`RaceModel`."""

        try:
            race_id = str(payload["race_id"])
            date_raw = payload["date"]
            course = str(payload["course"])
            distance = int(payload["distance"])
            ground = str(payload["ground"])
            weather = str(payload["weather"])
        except KeyError as exc:
            raise ValidationError(f"Missing race field: {exc.args[0]}") from exc
        if distance <= 0:
            raise ValidationError("Race distance must be positive")
        if isinstance(date_raw, datetime):
            date_value = date_raw
        else:
            date_value = datetime.fromisoformat(str(date_raw))
        horses_raw = payload.get("horses", [])
        horses: List[HorseEntryModel]
        if all(isinstance(item, HorseEntryModel) for item in horses_raw):
            horses = list(horses_raw)  # type: ignore[list-item]
        else:
            horses = [HorseEntryModel.model_validate(item) for item in horses_raw]
        return cls(
            race_id=race_id,
            date=date_value,
            course=course,
            distance=distance,
            ground=ground,
            weather=weather,
            horses=horses,
        )

    def get_horse(self, horse_id: str) -> HorseEntryModel | None:
        """Return the horse with the given identifier if present."""

        return next((horse for horse in self.horses if horse.horse_id == horse_id), None)


@dataclass(slots=True)
class PayoffModel:
    """Model representing a race payoff entry."""

    race_id: str
    bet_type: str
    combination: Tuple[str, ...]
    odds: float
    payout: float

    @classmethod
    def model_validate(cls, payload: Mapping[str, Any]) -> "PayoffModel":
        """Validate ``payload`` and return a :class:`PayoffModel`."""

        try:
            race_id = str(payload["race_id"])
            bet_type = str(payload["bet_type"])
            combination_raw = payload.get("combination", ())
            odds = float(payload["odds"])
            payout = float(payload["payout"])
        except KeyError as exc:
            raise ValidationError(f"Missing payoff field: {exc.args[0]}") from exc
        if odds <= 0:
            raise ValidationError("Payoff odds must be positive")
        if payout < 0:
            raise ValidationError("Payoff payout must be non-negative")
        if isinstance(combination_raw, str):
            combination = tuple(part for part in combination_raw.split("-") if part)
        elif isinstance(combination_raw, (list, tuple)):
            combination = tuple(str(part) for part in combination_raw)
        else:
            raise ValidationError("Payoff combination must be a string or sequence")
        return cls(
            race_id=race_id,
            bet_type=bet_type,
            combination=combination,
            odds=odds,
            payout=payout,
        )


HORSE_ENTRY_SCHEMA = (
    "race_id",
    "horse_id",
    "name",
    "jockey",
    "trainer",
    "draw",
    "odds",
)
"""Field names expected in horse entry records."""


RACE_SCHEMA = (
    "race_id",
    "date",
    "course",
    "distance",
    "ground",
    "weather",
)
"""Field names expected in race metadata records."""


PAYOFF_SCHEMA = (
    "race_id",
    "bet_type",
    "combination",
    "odds",
    "payout",
)
"""Field names expected in payoff records."""


@dataclass(slots=True)
class HorseEntry:
    """Runtime representation of a horse entry."""

    race_id: str
    horse_id: str
    name: str
    jockey: str
    trainer: str
    draw: int
    odds: Dict[str, float]


@dataclass(slots=True)
class Race:
    """Runtime representation of a race."""

    race_id: str
    date: datetime
    course: str
    distance: int
    ground: str
    weather: str
    horses: Tuple[HorseEntry, ...]

    def get_horse(self, horse_id: str) -> HorseEntry | None:
        """Return the horse with the given identifier if present."""

        return next((horse for horse in self.horses if horse.horse_id == horse_id), None)


@dataclass(slots=True)
class Payoff:
    """Runtime representation of a race payoff."""

    race_id: str
    bet_type: str
    combination: Tuple[str, ...]
    odds: float
    payout: float


def to_domain_horse(model: HorseEntryModel) -> HorseEntry:
    """Convert a :class:`HorseEntryModel` into its dataclass representation."""

    return HorseEntry(
        race_id=model.race_id,
        horse_id=model.horse_id,
        name=model.name,
        jockey=model.jockey,
        trainer=model.trainer,
        draw=model.draw,
        odds=dict(model.odds),
    )


def to_domain_race(model: RaceModel) -> Race:
    """Convert a :class:`RaceModel` into its dataclass representation."""

    horses = tuple(to_domain_horse(horse) for horse in model.horses)
    return Race(
        race_id=model.race_id,
        date=model.date,
        course=model.course,
        distance=model.distance,
        ground=model.ground,
        weather=model.weather,
        horses=horses,
    )


def to_domain_payoff(model: PayoffModel) -> Payoff:
    """Convert a :class:`PayoffModel` into its dataclass representation."""

    return Payoff(
        race_id=model.race_id,
        bet_type=model.bet_type,
        combination=tuple(model.combination),
        odds=model.odds,
        payout=model.payout,
    )


class ModelValidationError(RuntimeError):
    """Raised when incoming tabular data does not conform to the expected shape."""

    errors: list[Exception]
    """Detailed validation errors produced while processing records."""

    def __init__(self, message: str, *, errors: Sequence[Exception] | None = None) -> None:
        super().__init__(message)
        self.errors = list(errors or [])


def _missing_fields(record: Mapping[str, Any], required: Sequence[str]) -> list[str]:
    """Return missing fields for ``record`` given ``required`` names."""

    return [field for field in required if field not in record]


def validate_and_build_horses(data: Iterable[Mapping[str, Any]]) -> List[HorseEntryModel]:
    """Validate horse records and return Pydantic-style models."""

    errors: list[Exception] = []
    horses: list[HorseEntryModel] = []
    for index, record in enumerate(data):
        payload = dict(record)
        missing = _missing_fields(payload, HORSE_ENTRY_SCHEMA)
        if missing:
            errors.append(ValueError(f"Horse record {index} missing fields: {', '.join(missing)}"))
            continue
        try:
            horses.append(HorseEntryModel.model_validate(payload))
        except ValidationError as exc:
            errors.append(exc)
    if errors:
        raise ModelValidationError("Invalid horse data", errors=errors)
    return horses


def validate_and_build_races(
    races: Iterable[Mapping[str, Any]],
    horses: Iterable[HorseEntryModel] | None = None,
) -> List[RaceModel]:
    """Validate race records and attach horse models when provided."""

    race_to_horses: dict[str, list[HorseEntryModel]] = {}
    for horse in horses or []:
        race_to_horses.setdefault(horse.race_id, []).append(horse)

    errors: list[Exception] = []
    race_models: list[RaceModel] = []
    for index, record in enumerate(races):
        payload = dict(record)
        missing = _missing_fields(payload, RACE_SCHEMA)
        if missing:
            errors.append(ValueError(f"Race record {index} missing fields: {', '.join(missing)}"))
            continue
        payload["horses"] = race_to_horses.get(payload["race_id"], [])
        try:
            race_models.append(RaceModel.model_validate(payload))
        except ValidationError as exc:
            errors.append(exc)
    if errors:
        raise ModelValidationError("Invalid race data", errors=errors)
    return race_models


def validate_and_build_payoffs(payoffs: Iterable[Mapping[str, Any]]) -> List[PayoffModel]:
    """Validate payoff records and return models."""

    errors: list[Exception] = []
    payoff_models: list[PayoffModel] = []
    for index, record in enumerate(payoffs):
        payload = dict(record)
        missing = _missing_fields(payload, PAYOFF_SCHEMA)
        if missing:
            errors.append(ValueError(f"Payoff record {index} missing fields: {', '.join(missing)}"))
            continue
        try:
            payoff_models.append(PayoffModel.model_validate(payload))
        except ValidationError as exc:
            errors.append(exc)
    if errors:
        raise ModelValidationError("Invalid payoff data", errors=errors)
    return payoff_models


__all__ = [
    "HORSE_ENTRY_SCHEMA",
    "PAYOFF_SCHEMA",
    "RACE_SCHEMA",
    "HorseEntry",
    "HorseEntryModel",
    "ModelValidationError",
    "Payoff",
    "PayoffModel",
    "Race",
    "RaceModel",
    "ValidationError",
    "to_domain_horse",
    "to_domain_payoff",
    "to_domain_race",
    "validate_and_build_horses",
    "validate_and_build_payoffs",
    "validate_and_build_races",
]
