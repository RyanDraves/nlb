import pathlib
import tempfile
import unittest
from importlib import util
from types import ModuleType

from nlb.models.blockworld import environment


def load_some_code(policy_code: str) -> ModuleType | None:
    """General code for loading a string into a module"""
    # Write the generated policy code to a temporary file
    my_temp_file = pathlib.Path(
        tempfile.NamedTemporaryFile(suffix='.py', delete_on_close=False).name
    )
    my_temp_file.write_text(policy_code)

    spec = util.spec_from_file_location(
        'nlb.modules.blockworld.heuristic_llm_policy', my_temp_file
    )
    if spec is None or spec.loader is None:
        return None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestHeuristicLoading(unittest.TestCase):
    def test_load_heuristic(self) -> None:
        policy_code = pathlib.Path(
            pathlib.Path(__file__).parent / 'heuristic_llm_sample_policy.txt'
        ).read_text()
        module = load_some_code(policy_code)
        assert module is not None
        assert hasattr(module, 'heuristic_policy')
        assert callable(module.heuristic_policy)

        assert (
            module.heuristic_policy([[2, 1], [0], []]) == environment.Action.MOVE_2_TO_3
        )
