
from __future__ import annotations

import random
from typing import Dict, List

from src.sim.models import Agent


def ClampInt(v: int, lo: int, hi: int) -> int:
    """Clamp integer v into the inclusive range [lo, hi]."""
    return max(lo, min(hi, v))


class World:

    """
    Grid world with sparse, binary food and simple foraging agents.

    Determinism:
      - Initial RNG seeded by cfg['SEED'] (default 42).
      - Per-tick RNG uses (SEED, tick).
      - Agents act in ascending Agent.id.

    Config keys:
      GRID_WIDTH, GRID_HEIGHT, SEED, INITIAL_FOOD_PROB, NUM_AGENTS,
      HUNGER_MAX, HUNGER_INCREASE_PER_TICK, HUNGER_EAT_AMOUNT,
      VISION_RADIUS, WANDER_IDLE_CHANCE, WANDER_IDLE_CHANCE_AT_MAX_HUNGER,
      FOOD_REGEN_PROB
    """
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.w = int(cfg["GRID_WIDTH"])
        self.h = int(cfg["GRID_HEIGHT"])
        self.tick = 0
        self.rng = random.Random(int(cfg.get("SEED", 42)))
        # Food map: 0 or 1 per cell
        self.food = [[1 if self.rng.random() < cfg["INITIAL_FOOD_PROB"] else 0
                      for _ in range(self.w)] for _ in range(self.h)]
        # Spawn agents
        self.agents: List[Agent] = []
        # Track skulls
        self.skulls = []
        for _ in range(int(cfg["NUM_AGENTS"])):
            while True:
                x = self.rng.randrange(self.w)
                y = self.rng.randrange(self.h)
                # Allow stacking for MVP; or keep unique positions
                a = Agent.new(x,y)
                a.hunger = self.cfg["HUNGER_MAX"]
                self.agents.append(a)
                break

    def neighbors8(self, x:int, y:int):
        """
        Yields 8-connected neighbors within bounds.
        """
        for dy in (-1,0,1):
            for dx in (-1,0,1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x+dx, y+dy
                if 0 <= nx < self.w and 0 <= ny < self.h:
                    yield (nx, ny)

    def vision_cells(self, x:int, y:int, r:int):
        """
        Yields cells in Manhattan disk of radius r within bounds.
        """
        for dy in range(-r, r+1):
            for dx in range(-r, r+1):
                nx, ny = x+dx, y+dy
                if 0 <= nx < self.w and 0 <= ny < self.h:
                    # Manhattan distance for vision
                    if abs(dx) + abs(dy) <= r:
                        yield (nx, ny)

    def step(self) -> None:
        """
        Advance one tick:
          1) hunger += HUNGER_INCREASE_PER_TICK; record explored
          2) if food on tile: eat (tile->0, hunger reduced)
          3) else: if any food within Manhattan VISION_RADIUS: move one step toward nearest
          4) else: wander (prob 1 - idle_prob) to least-explored neighbor; ties broken by tiny noise and food bonus
        After agents: attempt sparse regeneration (≈ (w*h)//50 tries with FOOD_REGEN_PROB).
        """
        # One simulation tick
        self.tick += 1
        # Deterministic RNG per tick
        trng = random.Random((hash((self.cfg.get("SEED",42), self.tick)) & 0xFFFFFFFF))
        # Agents act in ID order for determinism
        for agent in sorted(self.agents, key=lambda a: a.id):
            if not agent.alive:
                continue  # dead agents do nothing
            # Increase hunger
            agent.hunger = max(0.0, agent.hunger - self.cfg["HUNGER_INCREASE_PER_TICK"])

            # death check
            if agent.hunger <= 0.0:
                agent.alive = False
                self.skulls.append({"x": agent.x, "y": agent.y, "ttl": int(self.cfg["SKULL_FADE_TICKS"])})
                continue

            # Log explored
            agent.explored.add((agent.x, agent.y))

            acted = False

            # 1) If food on current tile, eat
            if self.food[agent.y][agent.x] > 0:
                self.food[agent.y][agent.x] = 0
                agent.hunger = min(self.cfg["HUNGER_MAX"],
                                   agent.hunger + self.cfg["HUNGER_EAT_AMOUNT"])  # ← replenish
                acted = True

            if not acted:
                # 2) Look for food in vision radius, move toward nearest if any
                vr = int(self.cfg["VISION_RADIUS"])
                visible_food = []
                for (cx, cy) in self.vision_cells(agent.x, agent.y, vr):
                    if self.food[cy][cx] > 0:
                        dist = abs(cx-agent.x) + abs(cy-agent.y)
                        visible_food.append((dist, cx, cy))
                if visible_food:
                    visible_food.sort(key=lambda t: t[0])
                    _, fx, fy = visible_food[0]
                    dx = 0 if fx==agent.x else (1 if fx>agent.x else -1)
                    dy = 0 if fy==agent.y else (1 if fy>agent.y else -1)
                    agent.x = ClampInt(agent.x + dx, 0, self.w-1)
                    agent.y = ClampInt(agent.y + dy, 0, self.h-1)
                    acted = True

            if not acted:
                # 3) Wander — the hungrier, the less likely to idle and the more exploratory
                # Compute idle probability interpolation
                deficit = 1.0 - (agent.hunger / self.cfg["HUNGER_MAX"])
                idle_prob = (
                    self.cfg["WANDER_IDLE_CHANCE"] * (1.0 - deficit) +
                    self.cfg["WANDER_IDLE_CHANCE_AT_MAX_HUNGER"] * deficit
                )
                if trng.random() >= idle_prob:
                    # Prefer moving into least explored neighbor when not starving
                    # When starving, exploration pressure increases anyway since idle_prob is low
                    neigh = list(self.neighbors8(agent.x, agent.y))
                    trng.shuffle(neigh)
                    # Score neighbors by exploration count (0 best) + small randomness
                    def score(cell, agent=agent):
                        c = 0 if cell not in agent.explored else 1
                        return c + trng.random()*0.1 + (-0.1 if self.food[cell[1]][cell[0]] > 0 else 0.0)

                    neigh.sort(key=score)
                    nx, ny = neigh[0]
                    agent.x, agent.y = nx, ny
                # else: idle

        # 4) Very scarce regeneration: empty cells have small chance to spawn food
        regen_prob = self.cfg["FOOD_REGEN_PROB"]
        if regen_prob > 0:
            # Regen only a handful per tick to keep it scarce
            tries = max(1, (self.w * self.h) // 50)
            for _ in range(tries):
                if trng.random() < regen_prob:
                    rx = trng.randrange(self.w)
                    ry = trng.randrange(self.h)
                    self.food[ry][rx] = 1

        # Fade skulls
        for s in list(self.skulls):
            s["ttl"] -= 1
            if s["ttl"] <= 0:
                self.skulls.remove(s)

    def snapshot(self) -> Dict:
        # Build small payload for clients
        return {
            "tick": self.tick,
            "width": self.w,
            "height": self.h,
            "food": [(x,y) for y in range(self.h) for x in range(self.w) if self.food[y][x] > 0],
            "agents": [
                {"id": a.id, "x": a.x, "y": a.y, "hunger": a.hunger}
                for a in self.agents if a.alive                              # ← alive only
            ],
            "skulls": [
                {"x": s["x"], "y": s["y"], "alpha": s["ttl"]/self.cfg["SKULL_FADE_TICKS"]}
                for s in self.skulls                                         # ← fading 1→0
            ]
        }
