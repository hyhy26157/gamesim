
import uuid
from dataclasses import dataclass, field
from typing import Set, Tuple


@dataclass
class Agent:
    """
    Represents a foraging agent in the grid world simulation.

    Attributes:
        id (str): Unique identifier for the agent (UUID string).
        x (int): Current x-coordinate of the agent on the grid.
        y (int): Current y-coordinate of the agent on the grid.
        hunger (float): Current hunger level. Increases each tick,
            decreases when eating. Clamped externally to [0..HUNGER_MAX].
        explored (Set[Tuple[int, int]]): Set of grid cells the agent
            has visited, used to bias wandering toward unexplored areas.

    Methods:
        new(x: int, y: int) -> Agent:
            Factory method that creates a new agent with a fresh UUID,
            positioned at (x, y), hunger initialized to 0.0, and an
            empty explored set.
    """
    id: str
    x: int
    y: int
    hunger: float = 0.0
    explored: Set[Tuple[int,int]] = field(default_factory=set)
    alive: bool = True

    @staticmethod
    def new(x:int, y:int):
        return Agent(
            id=str(uuid.uuid4()), 
            x=x,
            y=y, 
            hunger=0.0, 
            explored=set(),
            alive= True)
