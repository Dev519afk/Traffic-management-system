"""Four-way single-green signal controller for simulation (not real-road deployment)."""
from dataclasses import dataclass
from typing import Mapping

DIRECTIONS = ("North", "East", "South", "West")


def choose_green(waiting: int) -> int:
    """Select a bounded GREEN duration from a non-negative queue estimate."""
    if not isinstance(waiting, int) or isinstance(waiting, bool) or waiting < 0:
        raise ValueError("Waiting count must be a non-negative integer")
    return 20 if waiting < 5 else 30 if waiting < 12 else 45


@dataclass
class SignalController:
    """Sequential 4-approach controller. Tick once per simulated second."""
    active: str = "North"
    state: str = "GREEN"
    remaining: int = 20
    yellow_seconds: int = 3
    all_red_seconds: int = 2
    completed_greens: int = 0

    @classmethod
    def start(cls, demand: Mapping[str, int]) -> "SignalController":
        _check_demand(demand)
        return cls(remaining=choose_green(demand["North"]))

    def lights(self) -> dict[str, str]:
        lights = {d: "RED" for d in DIRECTIONS}
        if self.state in ("GREEN", "YELLOW"):
            lights[self.active] = self.state
        if sum(s == "GREEN" for s in lights.values()) > 1:
            raise RuntimeError("Safety invariant violated: multiple GREEN signals")
        return lights

    def tick(self, demand: Mapping[str, int], seconds: int = 1) -> None:
        _check_demand(demand)
        if seconds < 1 or not isinstance(seconds, int):
            raise ValueError("Seconds must be a positive integer")
        for _ in range(seconds):
            self.remaining -= 1
            if self.remaining > 0:
                self.lights()
                continue
            if self.state == "GREEN":
                self.completed_greens += 1
                self.state = "YELLOW"
                self.remaining = self.yellow_seconds
            elif self.state == "YELLOW":
                self.state = "ALL_RED"
                self.remaining = self.all_red_seconds
            elif self.state == "ALL_RED":
                idx = DIRECTIONS.index(self.active)
                self.active = DIRECTIONS[(idx + 1) % len(DIRECTIONS)]
                self.state = "GREEN"
                self.remaining = choose_green(demand[self.active])
            else:
                raise RuntimeError(f"Unknown signal state: {self.state}")
            self.lights()


def _check_demand(demand: Mapping[str, int]) -> None:
    for direction in DIRECTIONS:
        if direction not in demand:
            raise ValueError(f"Missing demand for {direction}")
        choose_green(demand[direction])
