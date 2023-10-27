"""LMQL Queries shared by Logikon Reconstruction Analysts"""


from __future__ import annotations
from typing import List, Dict, Tuple

import lmql

from logikon.schemas.pros_cons import Claim
import logikon.schemas.argument_mapping as am
from logikon.utils.prompt_templates_registry import PromptTemplate


def system_prompt() -> str:
    """Returns the bare system prompt used in all lmql queries"""
    system_prompt = "You are a helpful, honest and knowledgeable AI assistant with expertise in critical thinking and argumentation analysis. Always answer as helpfully as possible."
    return system_prompt


@lmql.query
def supports_q(argument_data: dict, claim_data: dict):
    '''lmql
    argmax(chunksize=1)
        argument = Claim(**argument_data)
        claim = Claim(**claim_data)
        """
        ### System
        {system_prompt()}

        ### User

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

        Just answer with "(A)" or "(B)". No explanations or comments. You'll be asked to justify your answer later on.

        ### Assistant

        Answer: ([LABEL]"""
    distribution
        LABEL in ["A", "B"]
    '''


@lmql.query
def attacks_q(argument_data: dict, claim_data: dict):
    '''lmql
    argmax(chunksize=1)
        argument = Claim(**argument_data)
        claim = Claim(**claim_data)
        """
        ### System
        {system_prompt()}

        ### User

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

        Just answer with "(A)" or "(B)". No explanations or comments. You'll be asked to justify your answer later on.

        ### Assistant

        Answer: ([LABEL]"""
    distribution
        LABEL in ["A", "B"]
    '''


@lmql.query
def most_confirmed(argument_data: dict, claims_data: list):
    '''lmql
    argmax(chunksize=1)
        argument = Claim(**argument_data)
        claims = [Claim(**claim_data) for claim_data in claims_data]
        assert len(claims) <= 10
        labels = [l for l in "ABCDEFGHIJ"][:len(claims)]
        """
        ### System
        {system_prompt()}

        ### User

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
        Just answer with ({'/'.join(labels)}). You'll be asked to justify your answer later on.

        ### Assistant

        Answer: ([LABEL]"""
    distribution
        LABEL in labels
    '''


@lmql.query
def most_disconfirmed(argument_data: dict, claims_data: list):
    '''lmql
    argmax(chunksize=1)
        argument = Claim(**argument_data)
        claims = [Claim(**claim_data) for claim_data in claims_data]
        assert len(claims) <= 10
        labels = [l for l in "ABCDEFGHIJ"][:len(claims)]
        """
        ### System
        {system_prompt()}

        ### User

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
            text = text[0].lower() + text[1:]
            "({label}) \"It is not the case that {text}\"\n"
        """
        Just answer with ({'/'.join(labels)}). You'll be asked to justify your answer later on.

        ### Assistant

        Answer: ([LABEL]"""
    distribution
        LABEL in labels
    '''


@lmql.query
def valence(argument_data: dict, claim_data: dict, issue: str, prmpt_data: dict):
    '''lmql
    argmax(chunksize=1)
        argument = Claim(**argument_data)
        claim = Claim(**claim_data)
        prmpt = PromptTemplate(**prmpt_data)
        issue_text = f"Both claim and consideration have been set forth in a debate about this issue: {issue}\n" if issue else ""
        """
        {prmpt.sys_start}
        {system_prompt()}{prmpt.sys_end}

        {prmpt.user_start}
        Assignment: Identify whether a given consideration speaks for or against a claim.

        {issue_text}Read the following consideration and claim carefully.

        <consideration>
        {argument.label}: {argument.text}
        </consideration>
        <claim>
        {claim.label}: {claim.text}
        </claim>

        Does the consideration speak for, or against the claim?

        Here is some explanation and a simple heuristic that may help you to solve this task:
        Assume that (clear-thinking and fact-loving) Bob accepts both the claim and the consideration. Which is, for Bob, the more plausible way to express his stance?

        (A) "{claim.text} Which is (partly) because I believe: {argument.text}"
        (B) "{claim.text} Nonetheless, I also believe that: {argument.text}"

        If (A) sounds more plausible, then the consideration is an argument for the claim (speaks for). If (B) is more plausible, the consideration is an objection to the claim (speaks against).

        So, given your thorough assessment, which is correct:

        (A) The consideration tends to speak for the claim.
        (B) The consideration tends to speak against the claim.

        Just answer with (A/B). You'll be asked to justify your answer later on.{prmpt.user_end}

        {prmpt.ass_start}
        Answer: ([LABEL]"""
    distribution
        LABEL in ["A", "B"]
    '''


def get_distribution(result: lmql.LMQLResult) -> List[Tuple[str, float]]:
    """Extracts the distribution from an LMQL result

    Args:
        result (lmql.LMQLResult): LMQL Result object obtained from distribution query

    Raises:
        ValueError: No distribution found in LMQL result

    Returns:
        List[Tuple[str,float]]: Discrete distribution over labels (label, probability)
    """
    try:
        return result.variables[f'P({result.distribution_variable})']
    except:
        raise ValueError(f"Failed to extract distribution from LMQL result: {result}")


def label_to_idx(label):
    try:
        idx = "ABCDEFGHIJ".index(label)
    except ValueError:
        raise ValueError(f"Unknown label {label}")
    return idx


def label_to_claim(label, claims):
    idx = label_to_idx(label)
    if idx >= len(claims):
        raise ValueError(f"Too few claims for {label}")
    return claims[idx]


def label_to_valence(label):
    if label == "A":
        return am.SUPPORT
    elif label == "B":
        return am.ATTACK
    else:
        raise ValueError(f"Unknown label {label}")
