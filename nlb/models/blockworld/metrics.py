import dataclasses
import enum


class Policy(enum.Enum):
    HEURISTIC = enum.auto()
    OPEN_LOOP_LLM = enum.auto()
    CLOSED_LOOP_LLM = enum.auto()


@dataclasses.dataclass
class Result:
    policy: str  # Policy.name
    rng_seed: int
    num_blocks: int
    model: str
    reasoning_effort: str
    steps: int = 0
    success: bool = False
    wall_time_s: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
