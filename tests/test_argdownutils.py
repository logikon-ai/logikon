# test argdown parser and regexes

import re

import pytest

from logikon.schemas.pros_cons import Claim, ProsConsList, RootClaim
from logikon.utils import argdown


@pytest.fixture(name="snippet_1")
def snippet_1() -> str:
    snippet = """```argdown
[claim1]: claim 1.
// PROS
+ [pro_label1]: pro 1.
+ [pro_label1]: pro 2.
// CONS
- [con_label1]: con 1.
- [con_label1]: con 2.
```"""
    return snippet


@pytest.fixture(name="snippet_2")
def snippet_2() -> str:
    snippet = """```argdown
[claim1]: claim 1.
// PROS
// CONS
- [con_label1]: con 1.
- [con_label1]: con 2.
```"""
    return snippet


def test_argdown_parser1(snippet_1):
    parser = argdown.ArgdownParser()
    pros_cons_list = parser.parse_proscons(snippet_1)

    assert len(pros_cons_list.roots) == 1
    root = pros_cons_list.roots[0]
    assert root.label == "claim1"
    assert root.text == "claim 1."
    assert len(root.pros) == 2
    assert len(root.cons) == 2


def test_argdown_parser2(snippet_2):
    parser = argdown.ArgdownParser()
    pros_cons_list = parser.parse_proscons(snippet_2)

    assert len(pros_cons_list.roots) == 1
    root = pros_cons_list.roots[0]
    assert root.label == "claim1"
    assert root.text == "claim 1."
    assert len(root.pros) == 0
    assert len(root.cons) == 2


def test_argdown_regexes(snippet_1, snippet_2):

    assert re.fullmatch(argdown.REGEX_PROSCONS, snippet_1)
    assert re.fullmatch(argdown.REGEX_PROSCONS, snippet_2)
    assert not re.fullmatch(argdown.REGEX_PROSCONS, snippet_1.replace("\n", "\n\n"))
    # TODO: add more tests for regexes


def test_argdown_formatter(snippet_2):
    formatter = argdown.ArgdownFormatter()
    proscons = ProsConsList(
        roots=[
            RootClaim(
                label="claim1",
                text="claim 1.",
                pros=[],
                cons=[Claim(label="con_label1", text="con 1."), Claim(label="con_label1", text="con 2.")],
            )
        ]
    )
    formatted = formatter.format_proscons(proscons)
    assert formatted == snippet_2
