
# Mini World MVP (Python, FastAPI, WebSocket)

**What it is**: a tiny deterministic simulation with 5 agents on a 25×25 grid.  
Agents get hungry, look for food within a vision radius of 2, eat when they find it, and wander more when hungrier.  
Agents remember explored tiles to bias exploration. Food is scarce and regens slowly.

## Run

```bash
cd game_mvp
python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install fastapi uvicorn
python app.py
# open http://localhost:8000
```

## Tuning

Edit `config.json` then restart the server. Keys:

```json
{
  "GRID_WIDTH": 25,
  "GRID_HEIGHT": 25,
  "NUM_AGENTS": 5,
  "VISION_RADIUS": 2,
  "TICK_MS": 250,
  "INITIAL_FOOD_PROB": 0.05,
  "FOOD_REGEN_PROB": 0.005,
  "HUNGER_INCREASE_PER_TICK": 1.0,
  "HUNGER_EAT_AMOUNT": 25.0,
  "HUNGER_MAX": 100.0,
  "WANDER_IDLE_CHANCE": 0.2,
  "WANDER_IDLE_CHANCE_AT_MAX_HUNGER": 0.0,
  "SEED": 42
}
```

- Increase `HUNGER_INCREASE_PER_TICK` to make agents hungrier faster.
- Increase `FOOD_REGEN_PROB` to make food less scarce.
- Reduce `WANDER_IDLE_CHANCE` if you want more movement when not hungry.
- Change `SEED` for a new world layout and agent IDs (reproducible runs).

## Notes

- Deterministic per tick: agents update in ID order; tick RNG is seeded via `(SEED, tick)`.
- Vision uses Manhattan distance <= `VISION_RADIUS`.
- Wander: when not seeing food, agents prefer neighbors they've not explored; when hungrier, they idle less → more roaming.
- For simplicity, this MVP broadcasts the full snapshot each tick (tiny payload on 25×25).

## Next
- Persist events for replay, add more actions (gather/build), add a second personality.
- Partition world into regions and shard simulation workers if you scale.
