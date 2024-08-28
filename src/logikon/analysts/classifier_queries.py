"""Dialectics Classifier Queries shared by Logikon Reconstruction Analysts and Reasoning Guides"""

from __future__ import annotations

import logging

import logikon.schemas.argument_mapping as am
from logikon.backends.classifier import HfClassification, HfClassifier
from logikon.backends.multiple_choice import MultipleChoiceResult
from logikon.schemas.pros_cons import Claim

MAX_CLAIMS_RELEVANCE = 10


async def dialectic_relations(
    arguments: Claim | list[Claim], claims: Claim | list[Claim], classifier: HfClassifier
) -> list[MultipleChoiceResult]:
    """Query to assess dialectic relations"""
    if isinstance(arguments, Claim):
        arguments = [arguments]
    if isinstance(claims, Claim):
        claims = [claims]

    if len(arguments) != len(claims):
        msg = "Arguments and claims must have the same length"
        raise ValueError(msg)

    # templates and classes
    text_template = "Claim: {topic}. Reason: {argument}."
    hypothesis_template = "The claim is {} the given reason."
    classes_verbalized = ["directly confirmed by", "directly disconfirmed by", "independent of"]
    classes = [am.SUPPORT, am.ATTACK, am.NEUTRAL]

    # prepare inputs
    inputs = [
        text_template.format(topic=claim.text, argument=argument.text) for argument, claim in zip(arguments, claims)
    ]

    # define default dialectic relation
    default_diarel = MultipleChoiceResult(
        probs={am.SUPPORT: 0.0, am.ATTACK: 0.0, am.NEUTRAL: 1.0},
        label_max=am.NEUTRAL,
        idx_max=2,
        choices=classes,
    )

    classification_results = await classifier(
        inputs=inputs,
        hypothesis_template=hypothesis_template,
        classes_verbalized=classes_verbalized,
    )

    if len(classification_results) != len(inputs):
        err = (
            "Classifier failed to assess dialectical relations: "
            f"Input length ({len(classification_results)}) ≠ result length ({len(inputs)}). "
        )
        logging.getLogger(__name__).error(err)
        raise ValueError(err)

    results: list[MultipleChoiceResult] = []
    for cres in classification_results:
        if isinstance(cres, HfClassification):
            probs = {k: cres.scores[cres.labels.index(v)] for k, v in zip(classes, classes_verbalized)}
            label_max = next(
                k for k, v in zip(classes, classes_verbalized) if v == cres.labels[0]
            )  # labels are sorted by score
            idx_max = classes.index(label_max)
            result = MultipleChoiceResult(probs=probs, label_max=label_max, idx_max=idx_max, choices=classes)
            results.append(result)
        else:
            # default result
            logging.getLogger(__name__).warning(
                f"Invalid classification result: {cres}, "
                "using default value (NEUTRAL) for dialectic relations prediction."
            )
            results.append(default_diarel)

    return results


async def most_confirmed(
    arguments: Claim | list[Claim], claims: list[Claim] | list[list[Claim]], classifier: HfClassifier
) -> list[MultipleChoiceResult]:
    """Query to find most confirmed claims

    returns:
        list[MultipleChoiceResult]: List of results for each argument
                                    where choices are the alternative claims
                                    each choice (i.e. claim) is identified by its label
    """
    return await most_relevant(arguments=arguments, claims=claims, valence=am.SUPPORT, classifier=classifier)


async def most_disconfirmed(
    arguments: Claim | list[Claim], claims: list[Claim] | list[list[Claim]], classifier: HfClassifier
) -> list[MultipleChoiceResult]:
    """Query to find most confirmed claims

    returns:
        list[MultipleChoiceResult]: List of results for each argument
                                    where choices are the alternative claims
                                    each choice (i.e. claim) is identified by its label
    """
    return await most_relevant(arguments=arguments, claims=claims, valence=am.ATTACK, classifier=classifier)


async def most_relevant(
    arguments: Claim | list[Claim], claims: list[Claim] | list[list[Claim]], valence: str, classifier: HfClassifier
) -> list[MultipleChoiceResult]:

    if not claims:
        logging.getLogger(__name__).warning("No claims provided for most_relevant query.")
        msg = "No claims provided for most_relevant query."
        raise ValueError(msg)

    if isinstance(arguments, Claim):
        arguments = [arguments]
    claims_sets: list[list[Claim]]
    if isinstance(claims[0], Claim):
        claims_sets = [claims]  # type: ignore
    else:
        claims_sets = claims  # type: ignore

    if len(arguments) != len(claims_sets):
        msg = (
            "Arguments and batches of claims must have the same length. "
            f"But got {len(arguments)} arguments and {len(claims_sets)} batches of claims."
            f"Arguments: {arguments[:2]}... "
            f"Claims: {claims_sets[:2]}..."
        )
        raise ValueError(msg)

    for i in range(len(claims_sets)):
        if len(claims_sets[i]) > MAX_CLAIMS_RELEVANCE:
            msg = (
                f"Maximum number of claims exceeded: {len(claims_sets[i])}. "
                "Will proceed with first {MAX_CLAIMS_RELEVANCE}."
            )
            logging.getLogger(__name__).warning(msg)
            claims_sets[i] = claims_sets[i][:MAX_CLAIMS_RELEVANCE]

    # inputs and classes
    classes_verbalized: list[tuple[str, ...]] = [
        tuple({claim.label for claim in claims_set}) for claims_set in claims_sets
    ]

    if valence == am.SUPPORT:
        hypothesis_template = "Of all claims listed, claim [{}] is most strongly disconfirmed by the given reason."
    elif valence == am.ATTACK:
        hypothesis_template = "Of all claims listed, claim [{}] is most strongly confirmed by the given reason."
    else:
        msg = f"Invalid valence: {valence}. Expected SUPPORT or ATTACK."
        raise ValueError(msg)

    inputs: list[str] = []
    for argument, claims_set in zip(arguments, claims_sets):
        claims_formatted = "\n".join([f"[{claim.label}]: {claim.text}" for claim in claims_set])
        text = f"Reason: {argument.text}.\nClaims:\n{claims_formatted}"
        inputs.append(text)

    # partition input according to whether claims are identical
    # each partition has identical categories and can hence
    # be processed in a single batch by classifier
    partitions: list[dict] = []
    for unique_cverb in set(classes_verbalized):
        idxs = [i for i, cv in enumerate(classes_verbalized) if cv == unique_cverb]
        partitions.append(
            {
                "inputs": [inputs[i] for i in idxs],
                "claims_sets": [claims_sets[i] for i in idxs],
                "classes_verbalized": list(unique_cverb),
                "hypothesis_template": hypothesis_template,
            }
        )

    results: list[MultipleChoiceResult] = []

    for partition in partitions:

        classification_results = await classifier(**{k: v for k, v in partition.items() if k != "claims_sets"})  # type: ignore

        # postprocess
        cverb = partition["classes_verbalized"]
        for cres, claims_set in zip(classification_results, partition["claims_sets"]):
            if isinstance(cres, HfClassification):
                choice_labels = [c.label for c in claims_set]  # original ordering of labels
                probs = {label: cres.scores[cres.labels.index(label)] for label in cverb}
                label_max = cres.labels[0]  # labels are sorted by score
                idx_max = choice_labels.index(label_max)
                result = MultipleChoiceResult(probs=probs, label_max=label_max, idx_max=idx_max, choices=claims_set)
                results.append(result)
            else:
                # default result
                logging.getLogger(__name__).warning(
                    f"Invalid classification result: {cres}. "
                    "Using uniform distribution for most_relevant prediction."
                )
                results.append(
                    MultipleChoiceResult(
                        probs={label: 1 / len(cverb) for label in cverb}, label_max=cverb[0], idx_max=0, choices=cverb
                    )
                )

    return results
