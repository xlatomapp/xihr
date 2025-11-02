# 🏇 xihr – Japanese Horse Racing Betting Simulator/live betting tool

## Goals
- Build a **Python package** (`xihr`) that simulates and runs live Japanese horse racing betting strategies.  
- Support **all JRA betting patterns** (単勝, 複勝, 枠連, 馬連, 馬単, ワイド, 三連複, 三連単).  
- Provide a **BaseStrategy** API that allows scheduling, data access, betting, and portfolio management.  
- Use a **normalized data model** for races, horses, odds, and payoffs.  
- Allow users to provide data via **CSV, Excel, or database** repositories.
- Support both **simulation** and **live mode** via a repository pattern.  
- Provide a **CLI** built with **Typer**.  
- Manage **settings and configs** with **Pydantic Settings Management**.  

---

## Features

### 1. Betting Patterns
The engine must support:  
- **Win (単勝)** – select horse to finish 1st.  
- **Place (複勝)** – select horse to finish in top 2–3.  
- **Bracket Quinella (枠連)** – pick two brackets finishing 1st & 2nd.  
- **Quinella (馬連)** – pick two horses finishing 1st & 2nd in any order.  
- **Exacta (馬単)** – pick two horses finishing 1st & 2nd exact order.  
- **Quinella Place (ワイド)** – pick two horses that both finish in top 3.  
- **Trifecta Box (三連複)** – pick three horses finishing 1st–3rd any order.  
- **Trifecta Exact (三連単)** – pick three horses finishing 1st–3rd exact order.  

### 2. Normalized Data Model
Data should be in pandas and they should have below schema. Validation should be done with pydantic and pandera.
- **Race**
  Race:
      race_id: str
      date: datetime
      course: str
      distance: int
      ground: str
      weather: str
      horses: List["HorseEntry"]
  
- **HorseEntry**
  HorseEntry:
      horse_id: str
      name: str
      jockey: str
      trainer: str
      odds: Dict[str, float]   # odds by bet type
      draw: int
  
- **Payoff**
  Payoff:
      race_id: str
      bet_type: str
      combination: Tuple[str]
      odds: float
      payout: float

### 3. Strategy System
- **BaseStrategy APIs**
  - `schedule(time: str, fn: Callable)` → register a schedule (time, function).  
  - `get_data(race_id: str, bet_type: str)` → retrieve race/odds.  
  - `get_historical(horse_id:str)` -> retrieve historical data
  - `place_bet(race_id: str, horse_ids: List[str], stake: float, bet_type: str)` → place bet.  
  - `get_balance()` → bankroll balance.  
  - `get_positions()` → list of active/settled bets.  
- Strategies can define schedules and use events (`on_data`, `on_time`, `on_bet`, `on_result`).  
- Please provide more APIs that codex thinks it would be useful

### 4. Repository Pattern
- **DataRepository**
  - Simulation: loads historical data via repository implementation.
  - Live: connects to live API feed.  
- **BettingRepository**
  - Simulation: simulates payouts.  
  - Live: executes bets with broker/exchange API.  
- Repositories abstract environment away from strategies.  

### 5. Data Repository Implementations
- **SimulationDataRepository** factories
  ```python
  class SimulationDataRepository:
      @classmethod
      def from_csv(...)
      def from_excel(...)
      def from_database(...)
  ```
- Implementations normalise raw data into domain models for reuse across the engine.
- User specifies the repository type via CLI/config.

### 6. Analytics
- Basic stats e.g. total races, total races bet.
- Track KPIs: win rate, ROI, avg payout, max drawdown, total profit, max consecutive win, max consecutive loss.
- Report per strategy and bet type.  
- HTML deshboard for the results.  

### 7. CLI 
- CLI should be implemented using Typer package.
- Commands:  
  - `xihr run` – run a strategy (sim or live).  
  - `xihr run --live` – run live strategy.  
  - `xihr report` – generate reports.  
- Options:
  - `--strategy STRATEGY_NAME`
  - `--data-source csv|excel|db`
  - `--data PATH`
  - `--bankroll AMOUNT`  
  - `--config PATH`  

### 8. Config & Settings
- Use **Pydantic Settings Management**.  
- Config schema includes:
  - `initial_bankroll`
  - `data_source` (csv, excel, db, api)
  - `data_source_settings` (path, db connection, API keys)
  - `betting_limits`  
- Config can be loaded from `.env`, YAML, or CLI or env vairiable. 

---

## Project Structure
idea would be below, if you have better idea, please implement based on your idea.
```
xihr/
│
├── xihr/
│   ├── __init__.py
│   ├── engine.py                # Event loop + scheduling
│   ├── events.py                # Event types
│   ├── strategy.py              # BaseStrategy + APIs
│   ├── portfolio.py             # Bankroll & bet tracking
│   ├── analytics.py             # KPIs & reporting
│   ├── repositories/            # Repository pattern
│   │   ├── data_repository.py
│   │   ├── betting_repository.py
│   ├── settings.py              # Pydantic settings
│   └── cli.py                   # Typer CLI
│
├── strategies/                  # Example strategies
│   ├── __init__.py
│   ├── naive_favorite.py
│   └── value_betting.py
│
├── tests/                       # Pytest tests
├── data/                        # Sample data
├── configs/                     # Example configs
├── pyproject.toml
├── requirements.txt
└── README.md
```

---


