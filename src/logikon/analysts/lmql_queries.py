"""LMQL Queries shared by Logikon Reconstruction Analysts"""


from __future__ import annotations

import lmql

import logikon.schemas.argument_mapping as am
from logikon.schemas.pros_cons import Claim  # noqa: F401
from logikon.utils.prompt_templates_registry import PromptTemplate  # noqa: F401


def system_prompt() -> str:
    """Returns the bare system prompt used in all lmql queries"""
    system_prompt = "You are a helpful, honest and knowledgeable AI assistant with expertise "
    "in critical thinking and argumentation analysis. Always answer as helpfully as possible. "
    "Be concise."
    return system_prompt


@lmql.query
def supports_q(argument_data: dict, claim_data: dict, prmpt_data: dict):  # noqa: ARG001
    '''lmql
    argmax(chunksize=1)
        argument = Claim(**argument_data)
        claim = Claim(**claim_data)
        prmpt = PromptTemplate(**prmpt_data)
        """
        {prmpt.sys_start}
        {system_prompt()}{prmpt.sys_end}

        {prmpt.user_start}
        Assignment: Identify if an argument supports a claim.

        Read the following argument carefully.

        <argument>
        {argument.label}: {argument.text}
        </argument>

        Does this argument provide evidence for the following claim?

        <claim>
        [[{claim.label}]]: {claim.text}
        </claim>

        (A) Yes, the argument supports the claim.
        (B) No, the argument does not support the claim.

        Just answer with "(A)" or "(B)". No explanations or comments.
        You'll be asked to justify your answer later on.{prmpt.user_end}
        {prmpt.ass_start}
        Answer: ([LABEL]"""
    distribution
        LABEL in ["A", "B"]
    '''


@lmql.query
def attacks_q(argument_data: dict, claim_data: dict, prmpt_data: dict):  # noqa: ARG001
    '''lmql
    argmax(chunksize=1)
        argument = Claim(**argument_data)
        claim = Claim(**claim_data)
        prmpt = PromptTemplate(**prmpt_data)
        """
        {prmpt.sys_start}
        {system_prompt()}{prmpt.sys_end}

        {prmpt.user_start}
        Assignment: Identify if an argument speaks against a claim.

        Read the following argument carefully.

        <argument>
        {argument.label}: {argument.text}
        </argument>

        Does this argument provide evidence against the following claim?

        <claim>
        [[{claim.label}]]: {claim.text}
        </claim>

        (A) Yes, the argument disconfirms the claim.
        (B) No, the argument does not disconfirm the claim.

        Just answer with "(A)" or "(B)". No explanations or comments.
        You'll be asked to justify your answer later on.{prmpt.user_end}
        {prmpt.ass_start}
        Answer: ([LABEL]"""
    distribution
        LABEL in ["A", "B"]
    '''


@lmql.query
def most_confirmed(argument_data: dict, claims_data: list, prmpt_data: dict):  # noqa: ARG001
    '''lmql
    argmax(chunksize=1)
        argument = Claim(**argument_data)
        claims = [Claim(**claim_data) for claim_data in claims_data]
        assert len(claims) <= 10
        labels = [l for l in "ABCDEFGHIJ"][:len(claims)]
        prmpt = PromptTemplate(**prmpt_data)
        """
        {prmpt.sys_start}
        {system_prompt()}{prmpt.sys_end}

        {prmpt.user_start}
        Assignment: Identify the claim which is most strongly supported by an argument.

        Read the following argument carefully.

        <argument>
        {argument.label}: {argument.text}
        </argument>

        I'll show you a list of claims. Please identify the claim which is most strongly supported by the argument.

        The argument speaks in favor of:\n
        """
        for label, claim in zip(labels, claims):
            "({label}) \"{claim.label}: {claim.text}\"\n"
        """
        Just answer with ({'/'.join(labels)}). You'll be asked to justify your answer later on.{prmpt.user_end}
        {prmpt.ass_start}
        Answer: ([LABEL]"""
    distribution
        LABEL in labels
    '''


@lmql.query
def most_disconfirmed(argument_data: dict, claims_data: list, prmpt_data: dict):  # noqa: ARG001
    '''lmql
    argmax(chunksize=1)
        argument = Claim(**argument_data)
        claims = [Claim(**claim_data) for claim_data in claims_data]
        assert len(claims) <= 10
        labels = [l for l in "ABCDEFGHIJ"][:len(claims)]
        prmpt = PromptTemplate(**prmpt_data)
        """
        {prmpt.sys_start}
        {system_prompt()}{prmpt.sys_end}

        {prmpt.user_start}
        Assignment: Identify the claim which is supported by an argument.

        Read the following argument carefully.

        <argument>
        {argument.label}: {argument.text}
        </argument>

        I'll show you a list of claims. Please identify the claim which is supported by the argument.

        Note that all these claims are negations.

        The argument speaks in favor of:\n
        """
        for label, claim in zip(labels, claims):
            text = claim.text
            text = text[0].lower() + text[1:] if text else text
            "({label}) \"It is not the case that {text}\"\n"
        """
        Just answer with ({'/'.join(labels)}). You'll be asked to justify your answer later on.{prmpt.user_end}
        {prmpt.ass_start}
        Answer: ([LABEL]"""
    distribution
        LABEL in labels
    '''


#
# The heuristic in the following lmql query implements Wolfgang Spohn's
# explication of the reason relation as probabilistic relevance.
#
# W. Spohn, The Laws of Belief, OUP 2012, pp. 32ff.
#
@lmql.query
def valence(argument_data: dict, claim_data: dict, issue: str, prmpt_data: dict):  # noqa: ARG001
    '''lmql
    argmax(chunksize=1)
        argument = Claim(**argument_data)
        claim = Claim(**claim_data)
        prmpt = PromptTemplate(**prmpt_data)
        issue_text = (
            f"The following claim and consideration are drawn from a balanced debate, "
            f"containing an equal share of pros and cons, about this issue: {issue}\n"
        ) if issue else ""
        """
        {prmpt.sys_start}
        {system_prompt()}{prmpt.sys_end}

        {prmpt.user_start}
        Assignment: Identify whether a given consideration speaks for or against a claim.

        {issue_text}Read the consideration and claim carefully.

        <consideration>
        {argument.label}: {argument.text}
        </consideration>
        <claim>
        {claim.label}: {claim.text}
        </claim>

        Does the consideration speak for, or rather against the claim?

        Here is a simple heuristic that may help you to solve the task:
        Suppose that Bob, who is clear-thinking and fact-loving, is unsure about the claim "{claim.text}"
        Now, let's assume that Bob newly learns about and accepts the consideration "{argument.text}"
        Is this novel consideration rather going to:

        (A) strengthen Bob's belief in the claim.
        (B) weaken Bob's belief in the claim.

        In case (A), the consideration speaks for the claim; in case (B), it speaks against the claim.

        So, given your thorough assessment, which is correct:

        (A) The consideration speaks for the claim.
        (B) The consideration speaks against the claim.

        Just answer with (A/B). You'll be asked to justify your answer later on.{prmpt.user_end}
        {prmpt.ass_start}
        Answer: ([LABEL]"""
    distribution
        LABEL in ["A", "B"]
    '''


def get_distribution(result: lmql.LMQLResult) -> list[tuple[str, float]]:
    """Extracts the distribution from an LMQL result

    Args:
        result (lmql.LMQLResult): LMQL Result object obtained from distribution query

    Raises:
        ValueError: No distribution found in LMQL result

    Returns:
        List[Tuple[str,float]]: Discrete distribution over labels (label, probability)
    """
    try:
        return result.variables[f"P({result.distribution_variable})"]
    except Exception as err:
        msg = f"Failed to extract distribution from LMQL result: {result}"
        raise ValueError(msg) from err


def label_to_idx(label):
    try:
        idx = "ABCDEFGHIJ".index(label)
    except ValueError as err:
        msg = f"Unknown label {label}"
        raise ValueError(msg) from err
    return idx


def label_to_claim(label, claims):
    idx = label_to_idx(label)
    if idx >= len(claims):
        msg = f"Too few claims for {label}"
        raise ValueError(msg)
    return claims[idx]


def label_to_valence(label):
    if label == "A":
        return am.SUPPORT
    elif label == "B":
        return am.ATTACK
    else:
        msg = f"Unknown label {label}"
        raise ValueError(msg)
