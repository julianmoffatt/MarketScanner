from dataclasses import dataclass

@dataclass(frozen=True)
class BacktestConfig:
    starting_capital: float = 5000.0
    initial_exposure: float = 0.5
    window_years: int = 5
    fee: float = 0.25
    spread: float = 0.001
    periods_per_year: int = 252
    risk_free_rate: float = 0.0

    def __post_init__(self):
        if self.starting_capital <= 0:
            raise ValueError(f"starting_capital must be > 0, got {self.starting_capital}")
        if not 0 <= self.initial_exposure <= 1:
            raise ValueError(f"initial_exposure must be between 0 and 1, got {self.initial_exposure}")
        if self.window_years <= 0:
            raise ValueError(f"window_years must be > 0, got {self.window_years}")
        if self.fee < 0:
            raise ValueError(f"fee must be >= 0, got {self.fee}")
        if self.spread < 0:
            raise ValueError(f"spread must be >= 0, got {self.spread}")
        if self.periods_per_year <= 0:
            raise ValueError(f"periods_per_year must be > 0, got {self.periods_per_year}")