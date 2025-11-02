"""Core data models for races, horses, and payoffs."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Tuple

import pandas as pd
import pandera as pa
from pydantic import BaseModel, Field, ValidationError, field_validator


class HorseEntryModel(BaseModel):
    """Pydantic model representing a horse participating in a race."""

    race_id: str = Field(..., description="Race identifier that the horse belongs to")
    horse_id: str = Field(..., description="Unique identifier for the horse")
    name: str = Field(..., description="Display name of the horse")
    jockey: str = Field(..., description="Jockey riding the horse")
    trainer: str = Field(..., description="Trainer responsible for the horse")
    draw: int = Field(..., ge=1, description="Gate draw position")
    odds: Dict[str, float] = Field(default_factory=dict, description="Quoted odds by bet type")

    @field_validator("odds")
    @classmethod
    def validate_odds(cls, value: Dict[str, float]) -> Dict[str, float]:
        """Ensure odds are all positive floats."""

        for bet_type, odds_value in value.items():
            if odds_value <= 0:
                msg = f"Odds for {bet_type} must be positive, got {odds_value}"
                raise ValueError(msg)
        return value


class RaceModel(BaseModel):
    """Pydantic model representing a race."""

    race_id: str = Field(..., description="Unique race identifier")
    date: datetime = Field(..., description="Scheduled start time")
    course: str = Field(..., description="Race course name")
    distance: int = Field(..., gt=0, description="Race distance in meters")
    ground: str = Field(..., description="Track condition")
    weather: str = Field(..., description="Weather at post time")
    horses: List[HorseEntryModel] = Field(default_factory=list)

    def get_horse(self, horse_id: str) -> HorseEntryModel | None:
        """Return the horse with the given identifier if present."""

        return next((horse for horse in self.horses if horse.horse_id == horse_id), None)


class PayoffModel(BaseModel):
    """Pydantic model representing a race payoff."""

    race_id: str = Field(..., description="Race identifier for the payoff")
    bet_type: str = Field(..., description="Type of bet the payoff applies to")
    combination: Tuple[str, ...] = Field(..., description="Runner combination yielding the payoff")
    odds: float = Field(..., gt=0, description="Odds offered for the winning combination")
    payout: float = Field(..., ge=0, description="Payout for a unit stake")


HORSE_ENTRY_SCHEMA = pa.DataFrameSchema(
    {
        "race_id": pa.Column(str),
        "horse_id": pa.Column(str),
        "name": pa.Column(str),
        "jockey": pa.Column(str),
        "trainer": pa.Column(str),
        "draw": pa.Column(int, checks=pa.Check.ge(1)),
        "odds": pa.Column(object),
    }
)
"""Pandera schema enforcing the horse entries table format."""


RACE_SCHEMA = pa.DataFrameSchema(
    {
        "race_id": pa.Column(str),
        "date": pa.Column(pa.DateTime),
        "course": pa.Column(str),
        "distance": pa.Column(int, checks=pa.Check.gt(0)),
        "ground": pa.Column(str),
        "weather": pa.Column(str),
    }
)
"""Pandera schema validating race metadata tables."""


PAYOFF_SCHEMA = pa.DataFrameSchema(
    {
        "race_id": pa.Column(str),
        "bet_type": pa.Column(str),
        "combination": pa.Column(object),
        "odds": pa.Column(float, checks=pa.Check.gt(0), coerce=True),
        "payout": pa.Column(float, checks=pa.Check.ge(0), coerce=True),
    }
)
"""Pandera schema enforcing payoff table structure."""


@dataclass(slots=True)
class HorseEntry:
    """Runtime representation of a horse entry."""

    race_id: str
    """Identifier of the race the entry belongs to."""
    horse_id: str
    """Unique horse identifier."""
    name: str
    """Horse name used for display."""
    jockey: str
    """Name of the jockey riding the horse."""
    trainer: str
    """Name of the trainer responsible for the horse."""
    draw: int
    """Gate position for the horse."""
    odds: Dict[str, float]
    """Quoted odds by bet type."""


@dataclass(slots=True)
class Race:
    """Runtime representation of a race."""

    race_id: str
    """Unique identifier for the race."""
    date: datetime
    """Scheduled start time of the race."""
    course: str
    """Course where the race takes place."""
    distance: int
    """Race distance in meters."""
    ground: str
    """Ground condition at post time."""
    weather: str
    """Weather conditions at the course."""
    horses: Tuple[HorseEntry, ...]
    """Participants in the race."""

    def get_horse(self, horse_id: str) -> HorseEntry | None:
        """Return the horse with the given identifier if present."""

        return next((horse for horse in self.horses if horse.horse_id == horse_id), None)


@dataclass(slots=True)
class Payoff:
    """Runtime representation of a race payoff."""

    race_id: str
    """Identifier of the race the payoff belongs to."""
    bet_type: str
    """Type of bet for the payoff."""
    combination: Tuple[str, ...]
    """Runner combination that yielded the payoff."""
    odds: float
    """Odds paid for the winning combination."""
    payout: float
    """Payout amount for a unit stake."""


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
    """Raised when incoming tabular data does not conform to the schema."""

    errors: list[Exception]
    """Detailed validation errors produced by the underlying libraries."""

    def __init__(self, message: str, *, errors: list[Exception] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []


def validate_and_build_horses(data: pd.DataFrame) -> List[HorseEntryModel]:
    """Validate a horse dataframe and return Pydantic models."""

    try:
        validated = HORSE_ENTRY_SCHEMA.validate(data, lazy=True)
    except pa.errors.SchemaErrors as exc:  # pragma: no cover - rewrap pandera error
        raise ModelValidationError(
            "Invalid horse data", errors=exc.failure_cases.to_dict("records")
        ) from exc

    horses: List[HorseEntryModel] = []
    for record in validated.to_dict(orient="records"):
        try:
            horses.append(HorseEntryModel.model_validate(record))
        except ValidationError as exc:
            raise ModelValidationError("Invalid horse record", errors=[exc]) from exc
    return horses


def validate_and_build_races(
    races: pd.DataFrame,
    horses: Iterable[HorseEntryModel] | None = None,
) -> List[RaceModel]:
    """Validate race dataframe and attach horse models when provided."""

    race_to_horses: dict[str, list[HorseEntryModel]] = {}
    for horse in horses or []:
        race_to_horses.setdefault(horse.race_id, []).append(horse)
    try:
        validated = RACE_SCHEMA.validate(races, lazy=True)
    except pa.errors.SchemaErrors as exc:  # pragma: no cover
        raise ModelValidationError(
            "Invalid race data", errors=exc.failure_cases.to_dict("records")
        ) from exc

    race_models: List[RaceModel] = []
    for record in validated.to_dict(orient="records"):
        race_horses = race_to_horses.get(record["race_id"], [])
        try:
            race_models.append(
                RaceModel.model_validate({**record, "horses": race_horses})
            )
        except ValidationError as exc:
            raise ModelValidationError("Invalid race record", errors=[exc]) from exc
    return race_models


def validate_and_build_payoffs(payoffs: pd.DataFrame) -> List[PayoffModel]:
    """Validate payoff dataframe and return Pydantic models."""

    try:
        validated = PAYOFF_SCHEMA.validate(payoffs, lazy=True)
    except pa.errors.SchemaErrors as exc:  # pragma: no cover
        raise ModelValidationError(
            "Invalid payoff data", errors=exc.failure_cases.to_dict("records")
        ) from exc

    payoff_models: List[PayoffModel] = []
    for record in validated.to_dict(orient="records"):
        try:
            payoff_models.append(PayoffModel.model_validate(record))
        except ValidationError as exc:
            raise ModelValidationError("Invalid payoff record", errors=[exc]) from exc
    return payoff_models
