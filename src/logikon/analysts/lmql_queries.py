"""LMQL Queries shared by Logikon Reconstruction Analysts"""


from __future__ import annotations
from typing import List, Dict, Tuple

import lmql

from logikon.schemas.pros_cons import Claim
import logikon.schemas.argument_mapping as am


def system_prompt() -> str:
    """Returns the system prompt used in all lmql queries"""
    system_prompt = """
### System
        
You are a helpful, honest and knowledgeable AI assistant with expertise in critical thinking and argumentation analysis. Always answer as helpfully as possible.
"""

    return system_prompt


@lmql.query
def supports_q(argument_data: dict, claim_data: dict):
    '''lmql
    argmax(chunksize=1)
        argument = Claim(**argument_data)
        claim = Claim(**claim_data)
        """
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
def valence(argument_data: dict, claim_data: dict):
    '''lmql
    argmax(chunksize=1)
        argument = Claim(**argument_data)
        claim = Claim(**claim_data)
        """
        {system_prompt()}

        ### User

        Assignment: Identify whether an argument speaks for or against a claim.

        Read the following argument and claim carefully.

        <argument>
        {argument.label}: {argument.text}
        </argument>
        <claim>
        {claim.label}: {claim.text}
        </claim>

        Does the argument a pro reason for, or a con reason against against the claim?

        Here is a simple test: Which of the following is more plausible:

        (A) "{claim.text} BECAUSE {argument.text}"
        (B) "{claim.text} ALTHOUGH {argument.text}"

        In case (A), the argument speaks for (supports) the claim. In case (B) the argument speaks against (disconfirms) the claim.

        So, given your thorough assessment, which is correct:

        (A) The argument speaks for the claim.
        (B) The argument speaks against the claim.

        Just answer with (A/B). You'll be asked to justify your answer later on.

        ### Assistant

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
