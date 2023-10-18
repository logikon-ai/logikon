# test score function
from typing import List, Optional

import pytest

from logikon.debuggers.reconstruction.pros_cons_builder_lmql import EXAMPLES_ISSUE_PROSCONS, format_proscons

def test_examples():
    assert len(EXAMPLES_ISSUE_PROSCONS) == 3
    formatted = [format_proscons(*example) for example in EXAMPLES_ISSUE_PROSCONS]
    assert len(formatted) == 3