"""LCEL Queries shared by Logikon Reconstruction Analysts and Reasoning Guides"""

from __future__ import annotations

import asyncio

import logikon.schemas.argument_mapping as am
from logikon.backends.chat_models_with_grammar import LogitsModel
from logikon.backends.multiple_choice import MultipleChoiceResult, multiple_choice_query
from logikon.schemas.pros_cons import Claim

_SUPPORTS_Q_PROMPT = """
Assignment: Determine whether an argument supports a claim.

Read the following argument carefully.

<argument>
{argument_label}: {argument_text}
</argument>

Does this argument provide evidence for the following claim?

<claim>
[[{claim_label}]]: {claim_text}
</claim>

(A) Yes, the argument supports the claim.
(B) No, the argument does not support the claim.

Just answer with "A" or "B". No explanations or comments.
You'll be asked to justify your answer later on."""

_ATTACKS_Q_PROMPT = """
Assignment: Determine whether an argument speaks against a claim.

Read the following argument carefully.

<argument>
{argument_label}: {argument_text}
</argument>

Does this argument provide evidence against the following claim?

<claim>
[[{claim_label}]]: {claim_text}
</claim>

(A) Yes, the argument disconfirms the claim.
(B) No, the argument does not disconfirm the claim.

Just answer with "A" or "B". No explanations or comments.
You'll be asked to justify your answer later on."""

_MOST_CONFIRMED_PROMPT = """
Assignment: Identify the claim which is most strongly supported by an argument.

Read the following argument carefully.

<argument>
{argument_label}: {argument_text}
</argument>

I'll show you a list of claims. Please identify the claim which is most strongly supported by the argument.

The argument speaks in favor of:\n

{labels_claims_list}

Just answer with ({labels_list}). You'll be asked to justify your answer later on."""

_MOST_DISCONFIRMED_PROMPT = """
Assignment: Identify the claim which is supported by an argument.

Read the following argument carefully.

<argument>
{argument_label}: {argument_text}
</argument>

I'll show you a list of claims. Please identify the claim which is supported by the argument.

Note that all these claims are negations.

The argument speaks in favor of:\n

{labels_negations_list}

Just answer with ({labels_list}). You'll be asked to justify your answer later on."""

_VALENCE_PROMPT = """
Assignment: Identify whether a given consideration speaks for or against a claim.

{issue_text}Read the consideration and claim carefully.

<consideration>
{argument_label}: {argument_text}
</consideration>
<claim>
{claim_label}: {claim_text}
</claim>

Does the consideration speak for, or rather against the claim?

Here is a simple heuristic that may help you to solve the task:
Suppose that Bob, who is clear-thinking and fact-loving, is unsure about the claim "{claim_text}"
Now, let's assume that Bob newly learns about and accepts the consideration "{argument_text}"
Is this novel consideration rather going to:

(A) strengthen Bob's belief in the claim.
(B) weaken Bob's belief in the claim.

In case (A), the consideration speaks for the claim; in case (B), it speaks against the claim.

So, given your thorough assessment, which is correct:

(A) The consideration speaks for the claim.
(B) The consideration speaks against the claim.

Just answer with (A/B). You'll be asked to justify your answer later on."""


async def supports_q(
    arguments: Claim | list[Claim], claims: Claim | list[Claim], model: LogitsModel
) -> list[MultipleChoiceResult]:
    """Query support with LCEL

    Label A: The argument supports the claim
    Label B: The argument does not support the claim
    """

    if isinstance(arguments, Claim):
        arguments = [arguments]
    if isinstance(claims, Claim):
        claims = [claims]

    if len(arguments) != len(claims):
        msg = "Arguments and claims must have the same length"
        raise ValueError(msg)

    questions = [
        _SUPPORTS_Q_PROMPT.format(
            argument_label=argument.label, argument_text=argument.text, claim_label=claim.label, claim_text=claim.text
        )
        for argument, claim in zip(arguments, claims)
    ]
    labels = ["A", "B"]

    coros = [multiple_choice_query(question=question, labels=labels, model=model) for question in questions]
    results = await asyncio.gather(*coros)

    for result in results:
        result.choices = [True, False]

    return results


async def attacks_q(
    arguments: Claim | list[Claim], claims: Claim | list[Claim], model: LogitsModel
) -> list[MultipleChoiceResult]:

    if isinstance(arguments, Claim):
        arguments = [arguments]
    if isinstance(claims, Claim):
        claims = [claims]

    if len(arguments) != len(claims):
        msg = "Arguments and claims must have the same length"
        raise ValueError(msg)

    questions = [
        _ATTACKS_Q_PROMPT.format(
            argument_label=argument.label, argument_text=argument.text, claim_label=claim.label, claim_text=claim.text
        )
        for argument, claim in zip(arguments, claims)
    ]
    labels = ["A", "B"]

    coros = [multiple_choice_query(question=question, labels=labels, model=model) for question in questions]
    results = await asyncio.gather(*coros)

    for result in results:
        result.choices = [True, False]

    return results


async def most_confirmed(
    arguments: Claim | list[Claim], claims: list[Claim] | list[list[Claim]], model: LogitsModel
) -> list[MultipleChoiceResult]:

    if isinstance(arguments, Claim):
        arguments = [arguments]
    if not claims or isinstance(claims[0], Claim):
        claims = [claims]  # type: ignore

    if len(arguments) != len(claims):
        msg = (
            "Arguments and claims must have the same length. "
            f"But got {len(arguments)} arguments and {len(claims)} claims."
            f"Arguments: {arguments[:2]}... "
            f"Claims: {claims[:2]}..."
        )
        raise ValueError(msg)

    questions = []
    labels_ = []
    choices_ = []
    for argument, claims_arg in zip(arguments, claims):
        choices = claims_arg[:10]  # type: ignore
        labels = [label for label in "ABCDEFGHIJ"][: len(choices)]  # noqa: C416
        labels_claims_list = "\n".join(
            [f"({label}) {claim.label}: {claim.text}" for label, claim in zip(labels, choices)]
        )
        labels_list = "/".join(labels)
        question = _MOST_CONFIRMED_PROMPT.format(
            argument_label=argument.label,
            argument_text=argument.text,
            labels_claims_list=labels_claims_list,
            labels_list=labels_list,
        )
        questions.append(question)
        labels_.append(labels)
        choices_.append(choices)

    async def _add_choices(question: str, labels: list[str], model: LogitsModel, choices: list[Claim]):
        result = await multiple_choice_query(question=question, labels=labels, model=model)
        result.choices = choices
        return result

    coros = [
        _add_choices(question=question, labels=labels, model=model, choices=choices)
        for question, labels, choices in zip(questions, labels_, choices_)
    ]
    results = await asyncio.gather(*coros)

    return results


async def most_disconfirmed(
    arguments: Claim | list[Claim], claims: list[Claim] | list[list[Claim]], model: LogitsModel
) -> list[MultipleChoiceResult]:

    if isinstance(arguments, Claim):
        arguments = [arguments]
    if not claims or isinstance(claims[0], Claim):
        claims = [claims]  # type: ignore

    if len(arguments) != len(claims):
        msg = "Arguments and claims must have the same length"
        raise ValueError(msg)

    questions = []
    labels_ = []
    choices_ = []

    for argument, claims_arg in zip(arguments, claims):
        choices = claims_arg[:10]  # type: ignore
        labels = [label for label in "ABCDEFGHIJ"][: len(choices)]  # noqa: C416

        def _to_lower(text: str):
            if text:
                return text[0].lower() + text[1:]
            return text

        labels_negations_list = "\n".join(
            [f"({label}) It is not the case that {_to_lower(claim.text)}" for label, claim in zip(labels, choices)]
        )
        labels_list = "/".join(labels)

        question = _MOST_DISCONFIRMED_PROMPT.format(
            argument_label=argument.label,
            argument_text=argument.text,
            labels_negations_list=labels_negations_list,
            labels_list=labels_list,
        )

        questions.append(question)
        labels_.append(labels)
        choices_.append(choices)

    async def _add_choices(question: str, labels: list[str], model: LogitsModel, choices: list[Claim]):
        result = await multiple_choice_query(question=question, labels=labels, model=model)
        result.choices = choices
        return result

    coros = [
        _add_choices(question=question, labels=labels, model=model, choices=choices)
        for question, labels, choices in zip(questions, labels_, choices_)
    ]
    results = await asyncio.gather(*coros)

    return results


async def valence(
    arguments: Claim | list[Claim], claims: Claim | list[Claim], issue: str, model: LogitsModel
) -> list[MultipleChoiceResult]:
    """Query valence with LCEL

    The heuristic in this lcel query implements Wolfgang Spohn's
    explication of the reason relation as probabilistic relevance.

    W. Spohn, The Laws of Belief, OUP 2012, pp. 32ff.
    """

    if isinstance(arguments, Claim):
        arguments = [arguments]
    if isinstance(claims, Claim):
        claims = [claims]

    if len(arguments) != len(claims):
        msg = "Arguments and claims must have the same length"
        raise ValueError(msg)

    issue_text = (
        (
            f"The following claim and consideration are drawn from a balanced debate, "
            f"containing an equal share of pros and cons, about this issue: {issue}\n"
        )
        if issue
        else ""
    )
    labels = ["A", "B"]
    choices = [am.SUPPORT, am.ATTACK]

    questions = [
        _VALENCE_PROMPT.format(
            issue_text=issue_text,
            argument_label=argument.label,
            argument_text=argument.text,
            claim_label=claim.label,
            claim_text=claim.text,
        )
        for argument, claim in zip(arguments, claims)
    ]

    coros = [multiple_choice_query(question=question, labels=labels, model=model) for question in questions]
    results = await asyncio.gather(*coros)

    for result in results:
        result.choices = choices

    return results
