# test score function

from logikon.analysts.reconstruction.pros_cons_builder_lcel import (
    EXAMPLES_ISSUE_PROSCONS,
    format_examples,
    format_proscons,
)


def test_examples():
    assert len(EXAMPLES_ISSUE_PROSCONS) == 3
    formatted = [format_proscons(*example) for example in EXAMPLES_ISSUE_PROSCONS]
    assert len(formatted) == 3

    formatted_examples = format_examples()
    print(formatted_examples)  # noqa: T201
    assert formatted_examples.startswith("<example>")
    assert formatted_examples.endswith("</example>")
