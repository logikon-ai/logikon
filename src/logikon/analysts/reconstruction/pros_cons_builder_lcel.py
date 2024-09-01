"""Module with analyst for building a pros & cons list with langchain

```mermaid
flowchart TD
    p["`prompt`"]
    c["`completion`"]
    i["`issue`"]
    o["`options`"]
    r["`reasons (unstructured)`"]
    pcl["`pros cons list`"]
    ur["`reasons (unused)`"]
    rm("`reason mining`")
    pco("`pros cons organizing`")
    add("`add unused reasons`")
    cr("`check and revise`")
    subgraph artifact
    ad["`data`"]
    am["`metadata`"]
    end
    i --> rm
    p --> rm
    c --> rm
    p --> o
    i --> o --> pco
    i --> pco
    r --> pco --> add
    i --> cr
    add --> cr --> pcl --> ad
    add --> ur --> am
    rm --> r --> am
```

"""

from __future__ import annotations

import asyncio
import copy
import json
import pprint
import random
import re
from typing import ClassVar, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import SimpleJsonOutputParser, StrOutputParser
from langchain_core.prompts import AIMessagePromptTemplate, ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.prompts.chat import MessageLikeRepresentation
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel, RootModel

import logikon.schemas.argument_mapping as am
from logikon.analysts import classifier_queries, lcel_queries
from logikon.analysts.base import SYSTEM_MESSAGE_PROMPT
from logikon.analysts.lcel_analyst import LCELAnalyst
from logikon.schemas.pros_cons import Claim, ClaimList, ProsConsList, RootClaim
from logikon.schemas.results import AnalysisState, Artifact
from logikon.utils import argdown

MAX_N_REASONS = 18
MAX_N_ROOTS = 10
MAX_LEN_TITLE = 32
MAX_LEN_ROOTCLAIM = 128
_MAX_LEN_GIST = 180
N_DRAFTS = 3
LABELS = "ABCDEFG"

### CONSTRAINTS ###

## TODO: write tests for these regexes
# REGEX_CLAIM = r"\{\"text\":\s\"[^\"\n]*\",\s\"label\":\s\"[^\"\n]*\"\}"
# REGEX_ROOTCLAIM = r"\{\"root_text\":\s\"[^\"]*\",\s\"root_label\":\s\"[^\"]*\",\s\"pros\":\s((\[\])|(\["+REGEX_CLAIM+r"(,\s"+REGEX_CLAIM+r")*\])),\s\"cons\":\s((\[\])|(\["+REGEX_CLAIM+r"(,\s"+REGEX_CLAIM+r")*\]))\}"  # noqa: E501
# REGEX_PROSCONS = r"\[\s*"+REGEX_ROOTCLAIM+r"(,\s*"+REGEX_ROOTCLAIM+r")*\s*]"


### EXAMPLES ###

EXAMPLES_ISSUE_PROSCONS = [
    (
        "Bullfighting?",
        ProsConsList(
            roots=[
                RootClaim(
                    label="Bullfighting ban",
                    text="Bullfighting should be banned.",
                    pros=[Claim(label="Cruelty", text="Bullfighting is cruelty for the purpose of entertainment.")],
                    cons=[
                        Claim(label="Economic benefits", text="Bullfighting may benefit national economies."),
                        Claim(label="Cultural value", text="Bullfighting is part of history and local cultures."),
                    ],
                )
            ]
        ),
    ),
    (
        "Our next holiday",
        ProsConsList(
            roots=[
                RootClaim(
                    label="New York",
                    text="Let's spend our next holiday in New York.",
                    pros=[Claim(label="Culture", text="New York has incredible cultural events to offer.")],
                    cons=[Claim(label="Costs", text="Spending holidays in a big city is too expensive.")],
                ),
                RootClaim(
                    label="Florida",
                    text="Let's spend our next holiday in Florida.",
                    pros=[Claim(label="Swimming", text="Florida has wonderful beaches and a warm ocean.")],
                    cons=[],
                ),
                RootClaim(
                    label="Los Angeles",
                    text="Let's spend our next holiday in Los Angeles.",
                    pros=[],
                    cons=[Claim(label="No Novelty", text="We've been in Los Angeles last year.")],
                ),
            ]
        ),
    ),
    (
        "Pick best draft",
        ProsConsList(
            roots=[
                RootClaim(
                    label="Draft-1",
                    text="Draft-1 is the best draft.",
                    pros=[
                        Claim(label="Readability", text="Draft-1 is easier to read than the other drafts."),
                        Claim(label="Engagement", text="Draft-1 is much more funny than the other drafts."),
                    ],
                    cons=[],
                )
            ]
        ),
    ),
]


### FORMATTERS ###


def trunk_to_sentence(text: str) -> str:
    """Truncates text by cutting off incomplete sentences."""
    text = text.strip(" '\n")
    if text and text[-1] not in [".", "!", "?"]:
        # remove preceding marks
        text = text.strip(".!? ")
        # split text at any of ".", "!", "?"
        splits = re.split(r"([.!?])", text)
        text = "".join(splits[:-1]) if len(splits) > 1 else text
    return text


def format_reasons(reasons: list[Claim]) -> str:
    """Dump reasons as valid json string"""
    reasons_data = [r.model_dump() for r in reasons]
    formatted = json.dumps(reasons_data, indent=4)
    return formatted


def format_proscons(issue: str, proscons: ProsConsList, extra_reasons: list | None = None) -> str:
    formatted = ""
    # reasons block
    formatted += "reasons:\n"
    if not extra_reasons:
        reasons = []
    else:
        reasons = copy.deepcopy(extra_reasons)
    for root in proscons.roots:
        reasons.extend(root.pros)
        reasons.extend(root.cons)
    reasons = random.Random(42).sample(reasons, min(len(reasons), MAX_N_REASONS))
    formatted += f"{format_reasons(reasons)}\n"
    # issue
    formatted += f'issue: "{issue}"\n'
    # pros and cons block
    formatted += "pros_and_cons:\n"
    formatted += argdown.format_proscons(proscons)
    return formatted


def format_examples() -> str:
    formatted = [format_proscons(*example) for example in EXAMPLES_ISSUE_PROSCONS]
    formatted = ["<example>\n" + example + "\n</example>" for example in formatted]
    formatted_s = "\n".join(formatted)
    return formatted_s


def format_options(options: list[str]) -> str:
    formatted = json.dumps(options)
    return formatted


def format_critique(critique: list[str]) -> str:
    formatted = [f"{e}. {c}" for e, c in enumerate(critique)]
    return "\n".join(formatted)


### PROMPT TEMPLATES ###

_PROMPT_MINE_REASONS = """Your Assignment: Summarize all the arguments (pros and cons) presented in a text.

Use the following inputs (a TEXT that addresses an ISSUE) to solve your assignment.

<TEXT>
{prompt}{completion}
</TEXT>

<ISSUE>
{issue}
</ISSUE>

What are the TEXT's arguments (pros and cons) that address the ISSUE?

Let me give you more detailed instructions:

- Go through the text from beginning to end and extract all arguments in the order of appearance.
- For each argument, sketch the argument's gist in one or two grammatically correct sentences (less than {max_len_gist} chars), staying close to the original wording.
- In addition, provide a short label that flashlights the argument's key idea (2-4 words).
- Format your answer as valid JSON:
```json
[
    {{
        "text": "state here the first argument's gist in 1-2 concise sentences ...",
        "label": "argument's title (2-4 words) ..."
    }},
    {{
        "text": "another argument's gist ...",
        "label": "2nd argument's title (2-4 words) ..."
    }},
    // add more arguments, as necessary ...
]
```
- Avoid repeating one and the same argument in different words.
- You don't have to distinguish between pro and con arguments.
- IMPORTANT: Stay faithful to the text! Don't invent your own reasons. Only provide reasons which are either presented or discussed in the text."""  # noqa: E501

_DUMMY_CLAIM_LABEL = "Dummy claim label (remove or replace)"
_DUMMY_CLAIM_TEXT = "Dummy claim text (remove or replace)."

_MESSAGES_PROS_CONS_PREAMBLE: list[MessageLikeRepresentation] = [
    SystemMessage(content=SYSTEM_MESSAGE_PROMPT),
    HumanMessage(
        content=(
            "Assignment: Organize an unstructured set of reasons as a pros & cons list.\n\n"
            "Let's begin by thinking through the basic issue addressed by the reasons:"
        )
    ),
    AIMessagePromptTemplate.from_template("{issue}"),
    HumanMessage(
        content=(
            "What are the basic options available to an agent who needs to address this issue?\n"
            "Keep your answer short: Sketch each option in 3-6 words only."
        )
    ),
    AIMessagePromptTemplate.from_template("{formatted_options}"),
    HumanMessagePromptTemplate.from_template(
        "Thanks, let's keep that in mind.\n\n"
        "Let us now come back to the main assignment: constructing a pros & cons list from a set of reasons.\n\n"
        "You'll be given a set of reasons, which you're supposed to organize as a pros and cons list. "
        "Without modifiying the individual reasons themselves."
        "To do so, you have to find a fitting target claim (root statement) the reasons are arguing "
        "for (pros) or against (cons).\n"
        "Use the following inputs (a list of reasons that address an issue) to solve your assignment.\n"
        "<inputs>\n"
        "<issue>{issue}</issue>\n"
        "<reasons>\n"
        "{formatted_reasons}"
        "</reasons>\n"
        "</inputs>\n"
        "Let me show you a few examples to illustrate the task and the intended output:\n\n"
        "{formatted_examples}\n\n"
        "Note, however, that your pros and cons list may deviate from these examples, especially in "
        "terms of content and size.\n\n"
        "Please consider carefully the following further, more specific instructions:\n\n"
        "* Be bold: Your root claim(s) should be simple and unequivocal, and correspond to the basic options "
        "you have identified above.\n"
        "* No reasoning: Your root claim(s) must not contain any reasoning (or comments, or explanations).\n"
        "* Keep it short: Try to identify a single root claim. Add further root claims only if necessary "
        "(e.g., if reasons address three alternative decision options).\n"
        "* Recall options: Use the options you've identified above to construct the pros and cons list.\n"
        "* Be exhaustive: All reasons must figure in your pros and cons list. Keep the original reason labels.\n"
        "* !!Re-organize!!: Don't stick to the order of the original reason list.\n\n"
        "Moreover:\n\n"
        "* Use simple and plain language.\n"
        "* If you identify multiple root claims, make sure they are mutually exclusive alternatives.\n"
        "* Avoid repeating one and the same root claim in different words.\n"
        "* Use valid JSON syntax to structure your answer.\n"
        "Please start by recalling the reasons list your're supposed to re-organize."
    ),
    AIMessagePromptTemplate.from_template("{formatted_reasons}"),
    HumanMessage(content=("Correct. Now, let's start organizing the reasons into a pros and cons list.")),
]


class ProsConsBuilderLCEL(LCELAnalyst):
    """ProsConsBuilderLCEL

    This LCELAnalyst is responsible for reconstructing a pros and cons list for a given issue.

    """

    __pdescription__ = "Pros and cons list with multiple root claims"
    __product__ = "proscons"
    __requirements__: ClassVar[list[str | set]] = ["issue"]

    @LCELAnalyst.timeout
    def _mine_reasons(self, prompt, completion, issue) -> list[Claim]:
        """Defines and executes LCEL chain for mining reasons (not distinguishing pros and cons)."""

        prompt = ChatPromptTemplate.from_template(_PROMPT_MINE_REASONS)

        guided_json = ClaimList.model_json_schema()
        gen_args = {"temperature": 0.4, "json_schema": guided_json}

        # fmt: off
        chain = (
            prompt
            | self._model.bind(**gen_args).with_retry()
            | SimpleJsonOutputParser()
        )
        # fmt: on

        inputs = {
            "prompt": prompt,
            "completion": completion,
            "issue": issue,
            "max_len_gist": _MAX_LEN_GIST,
        }

        result = chain.invoke(inputs)

        # postprocess reasons
        reasons = []
        for data in result:
            if not data:
                continue
            if "label" in data:
                label = data["label"].strip(' "\n')
            else:
                self.logger.debug(f"Mine reasons results: {result}")
                self.logger.warning(f"No label in claim item {data}. Using dummy.")
                label = _DUMMY_CLAIM_LABEL
            if "text" in data:
                text = trunk_to_sentence(data["text"].strip(' "\n'))
            else:
                self.logger.debug(f"Mine reasons results: {result}")
                self.logger.warning(f"No text in claim item {data}. Using dummy.")
                text = _DUMMY_CLAIM_TEXT

            reasons.append(Claim(label=label, text=text))

        return reasons

    @LCELAnalyst.timeout
    def _describe_options(self, issue, prompt) -> list[str]:
        """Defines and executes LCEL chain for describing basic decision options available."""

        prompt = ChatPromptTemplate.from_messages(
            [
                HumanMessage(
                    content=(
                        "Assignment: Build a pros & cons list for a given issue.\n\n"
                        "**Plan**\n"
                        "Step 1: State the central issue.\n"
                        "Step 2: Identify the basic options available to an agent who faces the issue.\n"
                        "Step 3: Construct a pros & cons list for the issue.\n\n"
                        "**Step 1**\n"
                        "Let's begin by stating our central issue clearly and concisely:"
                    )
                ),
                AIMessage(content=f'{{"issue"="{issue}"}}'),
                HumanMessagePromptTemplate.from_template(
                    "**Step 2**\n"
                    "What are the basic options available to an agent who needs to address the above issue?\n"
                    "You may use any hints from the following text, but you don't have to.\n"
                    "<text>\n{prompt}\n</text>\n"
                    "Keep your answer short: Sketch each option in 2-6 words only. Prefer imperative mood. "
                    "Format your answer as valid JSON (i.e., `[{{'option': '...'}}, {{'option': '...'}}, ...]`)."
                ),
            ]
        )

        class Option(BaseModel):
            option: str

        class OptionList(RootModel):
            root: list[Option]

        guided_json = OptionList.model_json_schema()
        gen_args = {"temperature": 0.4, "json_schema": guided_json}

        # fmt: off
        chain = (
            prompt
            | self._model.bind(**gen_args).with_retry()
            | SimpleJsonOutputParser()
        )
        # fmt: on

        inputs = {
            "prompt": prompt,
        }

        result = chain.invoke(inputs)

        options = [Option(**r).option for r in result]

        return options

    @LCELAnalyst.timeout
    def _build_pros_and_cons(self, reasons: list[Claim], issue: str, options: list[str]) -> ProsConsList:
        """Builds and executes LCEL chain for building pros and cons list."""

        messages = _MESSAGES_PROS_CONS_PREAMBLE
        prompt = ChatPromptTemplate.from_messages(messages)
        gen_args = {
            "temperature": 0.4,
            "regex": argdown.REGEX_PROSCONS,
            "bnf": argdown.GRAMMAR_PROSCONS,
        }

        # fmt: off
        chain = (
            prompt
            | self._model.bind(**gen_args).with_retry()
            | StrOutputParser()
            | RunnableLambda(argdown.parse_proscons)
        )
        # fmt: on

        inputs = {
            "issue": issue,
            "formatted_options": format_options(options),
            "formatted_examples": format_examples(),
            "formatted_reasons": format_reasons(reasons),
        }

        result = chain.invoke(inputs)
        result.options = options

        self.logger.debug(f"Pros and cons list: {result.model_dump()}")

        # TODO: consider drafting alternative pros&cons lists and choosing best

        return result

    @LCELAnalyst.timeout
    def _check_and_revise_content(
        self,
        reasons: list[Claim],
        issue: str,
        options: list[str],
        pros_and_cons: ProsConsList,
    ) -> ProsConsList:
        """Checks if reasons are missing / incorrectly added to pros cons list, and revises it accordingly."""

        # FIXME
        # So far we're just checking by labels. We should check text content, too.
        # Check if every root claim has a text, if not, provide one.
        # Revise and improve root claims in pros cons list. In particulat:
        # - There are more root claims than reasons
        # - Check if reasons are renederd or as root claims

        pro_labels = [reason.label for root in pros_and_cons.roots for reason in root.pros]
        con_labels = [reason.label for root in pros_and_cons.roots for reason in root.cons]
        unused_reasons = [
            reason.label for reason in reasons
            if reason.label not in pro_labels + con_labels + [_DUMMY_CLAIM_LABEL]
        ]
        hallucinated_pros = [label for label in pro_labels if label not in [reason.label for reason in reasons]]
        hallucinated_cons = [label for label in con_labels if label not in [reason.label for reason in reasons]]
        duplicate_reasons = [
            label for label in set(pro_labels + con_labels) if pro_labels.count(label) + con_labels.count(label) > 1
        ]

        critique: list[str] = []
        for label in unused_reasons:
            critique.append(f"The reason with label '{label}' does not appear in your pros and cons list.")
        for label in hallucinated_pros:
            critique.append(
                f"The pro reason with label '{label}' in your pros and cons list is not drawn "
                "from the original reasons list."
            )
        for label in hallucinated_cons:
            critique.append(
                f"The con reason with label '{label}' in your pros and cons list is not drawn "
                "from the original reasons list."
            )
        for label in duplicate_reasons:
            critique.append(f"A reason with label '{label}' appears multiple times in the pros and cons list.")

        if not critique:
            return pros_and_cons

        self.logger.info("Found content-related issues in pros and cons list. Revising ...")
        self.logger.debug(f"Critique: {critique}")

        messages = copy.deepcopy(_MESSAGES_PROS_CONS_PREAMBLE)
        messages.extend(
            [
                AIMessagePromptTemplate.from_template("{formatted_proscons}"),
                HumanMessagePromptTemplate.from_template(
                    "Thanks for the pros and cons list. However, I've noticed the following flaws:\n"
                    "{formatted_critique}\n"
                    "Can you please carefully re-read the above instructions, check the pros & cons list you've "
                    "provided, and correct the errors I pointed out? Please do so by producing a revised pros & "
                    "cons list below."
                ),
            ]
        )
        prompt = ChatPromptTemplate.from_messages(messages)
        gen_args = {
            "temperature": 0.4,
            "regex": argdown.REGEX_PROSCONS,
            "bnf": argdown.GRAMMAR_PROSCONS,
        }

        # fmt: off
        chain = (
            prompt
            | self._model.bind(**gen_args).with_retry()
            | StrOutputParser()
            | RunnableLambda(argdown.parse_proscons)
        )
        # fmt: on

        inputs = {
            "issue": issue,
            "formatted_options": format_options(options),
            "formatted_examples": format_examples(),
            "formatted_reasons": format_reasons(reasons),
            "formatted_proscons": format_proscons(issue, pros_and_cons),
            "formatted_critique": format_critique(critique),
        }

        result = chain.invoke(inputs)
        result.options = options

        self.logger.info(f"Revised pros and cons list: {result.model_dump()}")

        return result

    def _ensure_unique_labels(self, reasons: list[Claim]) -> list[Claim]:
        """Revises labels of reasons to ensure uniqueness

        Args:
            reasons (List[Claim]): list of reasons

        Returns:
            List[Claim]: list of reasons with unique labels
        """

        labels = [reason.label for reason in reasons]

        # replace empty labels with defaults
        labels = [label if label else f"Reason-{enum}" for enum, label in enumerate(labels)]

        duplicate_labels = [label for label in labels if labels.count(label) > 1]
        if not duplicate_labels:
            return reasons

        unique_reasons = copy.deepcopy(reasons)
        for e, reason in enumerate(unique_reasons):
            if reason.label in duplicate_labels:
                i = 1
                new_label = f"{reason.label}-{i!s}"
                while new_label in labels:
                    if i >= MAX_N_REASONS:
                        self.logger.warning("Failed to ensure unique labels for reasons.")
                        break
                    i += 1
                    new_label = f"{reason.label}-{i!s}"
                labels.append(new_label)
                unique_reasons[e] = Claim(label=new_label, text=reason.text)

        return unique_reasons

    async def _check_and_revise_logic2(
        self, pros_and_cons: ProsConsList, reasons: list[Claim], issue: str  # noqa: ARG002
    ) -> ProsConsList:
        """Checks and revises a pros & cons list

        Args:
            pros_and_cons (List[Dict]): the pros and cons list to be checked and revised
            issue (str): the overarching issue addressed by the pros and cons

        Returns:
            List[Dict]: the revised pros and cons list

        For each pro (con) reason *r* targeting root claim *c*:

        - Checks if *r* supports (attacks) another root claim *c'* more strongly
        - Two sanity checks
        - Revises map accordingly

        """

        class Revision(TypedDict):
            reason: Claim
            old_target_idx: int
            old_val: str
            new_target_idx: int
            new_val: str

        revisions: list[Revision] = []

        revised_pros_and_cons = copy.deepcopy(pros_and_cons)
        all_reasons = [reason for root in revised_pros_and_cons.roots for reason in root.pros + root.cons]

        if not all_reasons:
            return revised_pros_and_cons

        coros = [
            lcel_queries.most_confirmed(
                arguments=all_reasons,
                claims=len(all_reasons) * [revised_pros_and_cons.roots],  # type: ignore
                model=self._model,
            ),
            lcel_queries.most_disconfirmed(
                arguments=all_reasons,
                claims=len(all_reasons) * [revised_pros_and_cons.roots],  # type: ignore
                model=self._model,
            ),
        ]

        most_confirmed_array, most_disconfirmed_array = await asyncio.gather(*coros)
        most_confirmed_dict = dict(zip(all_reasons, most_confirmed_array))
        most_disconfirmed_dict = dict(zip(all_reasons, most_disconfirmed_array))

        # TODO: refactor code below so as to batch lcel_queries.valence calls with asyncio.gather

        for enum, root in enumerate(revised_pros_and_cons.roots):
            for pro in root.pros:
                # check target
                result_conf = most_confirmed_dict[pro]
                probs_conf = list(result_conf.probs.values())
                if max(probs_conf) < 2 * probs_conf[enum]:
                    continue

                old_val = am.SUPPORT
                new_val = old_val
                old_target_idx = enum
                new_target_idx = result_conf.idx_max

                # sanity check 1
                result = most_disconfirmed_dict[pro]
                if result.idx_max == result_conf.idx_max:
                    continue

                # sanity check 2
                result = (
                    await lcel_queries.valence(
                        arguments=pro,
                        claims=revised_pros_and_cons.roots[new_target_idx],
                        issue=issue,
                        model=self._model,
                    )
                )[0]
                new_val = result.choices[result.idx_max]
                if new_val != am.SUPPORT:  # never change valence
                    continue

                revisions.append(
                    {
                        "reason": pro,
                        "old_target_idx": old_target_idx,
                        "new_target_idx": new_target_idx,
                        "old_val": old_val,
                        "new_val": new_val,
                    }
                )

            for con in root.cons:
                # check target
                result_disconf = most_disconfirmed_dict[con]
                probs_disconf = list(result_disconf.probs.values())
                if max(probs_disconf) < 2 * probs_disconf[enum]:
                    continue

                old_val = am.ATTACK
                new_val = old_val
                old_target_idx = enum
                new_target_idx = result_disconf.idx_max

                # sanity check 1
                result = most_confirmed_dict[con]
                if result.idx_max == result_disconf.idx_max:
                    continue

                # sanity check 2
                result = (
                    await lcel_queries.valence(
                        arguments=con,
                        claims=revised_pros_and_cons.roots[new_target_idx],
                        issue=issue,
                        model=self._model,
                    )
                )[0]
                new_val = result.choices[result.idx_max]
                if new_val != am.ATTACK:  # never change valence
                    continue

                revisions.append(
                    {
                        "reason": con,
                        "old_target_idx": old_target_idx,
                        "new_target_idx": new_target_idx,
                        "old_val": old_val,
                        "new_val": new_val,
                    }
                )

        self.logger.debug(f"Identified {len(revisions)} revision of pros and cons list.")

        # revise pros and cons list according to revision instructions
        for revision in revisions:
            reason = revision["reason"]
            old_root = revised_pros_and_cons.roots[revision["old_target_idx"]]
            new_root = revised_pros_and_cons.roots[revision["new_target_idx"]]
            if revision["old_val"] == am.SUPPORT:
                old_root.pros.remove(reason)
            elif revision["old_val"] == am.ATTACK:
                old_root.cons.remove(reason)
            if revision["new_val"] == am.SUPPORT:
                new_root.pros.append(reason)
            elif revision["new_val"] == am.ATTACK:
                new_root.cons.append(reason)

        return revised_pros_and_cons

    async def _check_and_revise_logic(
        self, pros_and_cons: ProsConsList, reasons: list[Claim], issue: str
    ) -> ProsConsList:
        """Checks and revises a pros & cons list

        Args:
            pros_and_cons (List[Dict]): the pros and cons list to be checked and revised
            issue (str): the overarching issue addressed by the pros and cons

        Returns:
            List[Dict]: the revised pros and cons list

        For each pro (con) reason *r* targeting root claim *c*:

        - Checks if *r* supports (attacks) another root claim *c'* more strongly
        - Two sanity checks
        - Revises map accordingly

        """

        if not self._classifier:
            self.logger.warning("No classifier available. Using fall-back check-and-revise logic.")
            return await self._check_and_revise_logic2(pros_and_cons, reasons, issue)

        class Revision(TypedDict):
            reason: Claim
            old_target_idx: int
            old_val: str
            new_target_idx: int
            new_val: str

        revisions: list[Revision] = []

        revised_pros_and_cons = copy.deepcopy(pros_and_cons)
        all_reasons = [reason for root in revised_pros_and_cons.roots for reason in root.pros + root.cons]

        if not all_reasons or len(revised_pros_and_cons.roots) == 1:
            return revised_pros_and_cons

        coros = [
            classifier_queries.most_confirmed(
                arguments=all_reasons,
                claims=len(all_reasons) * [revised_pros_and_cons.roots],  # type: ignore
                classifier=self._classifier,
            ),
            classifier_queries.most_disconfirmed(
                arguments=all_reasons,
                claims=len(all_reasons) * [revised_pros_and_cons.roots],  # type: ignore
                classifier=self._classifier,
            ),
        ]

        most_confirmed_array, most_disconfirmed_array = await asyncio.gather(*coros)
        most_confirmed_dict = dict(zip(all_reasons, most_confirmed_array))
        most_disconfirmed_dict = dict(zip(all_reasons, most_disconfirmed_array))

        for enum, root in enumerate(revised_pros_and_cons.roots):
            for pro in root.pros:
                # check target
                result_conf = most_confirmed_dict[pro]
                probs_conf = list(result_conf.probs.values())
                if max(probs_conf) < 2 * probs_conf[enum]:
                    continue

                old_val = am.SUPPORT
                new_val = old_val
                old_target_idx = enum
                new_target_idx = result_conf.idx_max
                new_target_label = revised_pros_and_cons.roots[new_target_idx].label

                # sanity check 1
                result = most_disconfirmed_dict[pro]
                if result.idx_max == result_conf.idx_max:
                    continue

                # sanity check 2
                if result.probs[new_target_label] > result_conf.probs[new_target_label]:
                    continue

                revisions.append(
                    {
                        "reason": pro,
                        "old_target_idx": old_target_idx,
                        "new_target_idx": new_target_idx,
                        "old_val": old_val,
                        "new_val": new_val,
                    }
                )

            for con in root.cons:
                # check target
                result_disconf = most_disconfirmed_dict[con]
                probs_disconf = list(result_disconf.probs.values())
                if max(probs_disconf) < 2 * probs_disconf[enum]:
                    continue

                old_val = am.ATTACK
                new_val = old_val
                old_target_idx = enum
                new_target_idx = result_disconf.idx_max
                new_target_label = revised_pros_and_cons.roots[new_target_idx].label

                # sanity check 1
                result = most_confirmed_dict[con]
                if result.idx_max == result_disconf.idx_max:
                    continue

                # sanity check 2
                if result.probs[new_target_label] > result_disconf.probs[new_target_label]:
                    continue

                revisions.append(
                    {
                        "reason": con,
                        "old_target_idx": old_target_idx,
                        "new_target_idx": new_target_idx,
                        "old_val": old_val,
                        "new_val": new_val,
                    }
                )

        self.logger.debug(f"Identified {len(revisions)} revision of pros and cons list.")

        # revise pros and cons list according to revision instructions
        for revision in revisions:
            reason = revision["reason"]
            old_root = revised_pros_and_cons.roots[revision["old_target_idx"]]
            new_root = revised_pros_and_cons.roots[revision["new_target_idx"]]
            if revision["old_val"] == am.SUPPORT:
                old_root.pros.remove(reason)
            elif revision["old_val"] == am.ATTACK:
                old_root.cons.remove(reason)
            if revision["new_val"] == am.SUPPORT:
                new_root.pros.append(reason)
            elif revision["new_val"] == am.ATTACK:
                new_root.cons.append(reason)

        return revised_pros_and_cons

    async def _analyze(self, analysis_state: AnalysisState):
        """Extract pros and cons of text (prompt/completion).

        Args:
            analysis_state (AnalysisState): current analysis_state to which new artifact is added

        Raises:
            ValueError: Failure to create pros and cons list

        Proceeds as follows:

        1. Mine (i.e., extract) all individual reasons from prompt/completion text
        2. Identify basic options
        3. Organize reasons into pros and cons list
        4. Double-check and revise pros and cons list

        """

        prompt, completion = analysis_state.get_prompt_completion()
        issue = next(a.data for a in analysis_state.artifacts if a.id == "issue")

        if prompt is None or completion is None:
            msg = f"Prompt or completion is None. {self.__class__} requires both prompt and completion to analyze."
            raise ValueError(msg)

        # mine reasons
        reasons = self._mine_reasons(prompt=prompt, completion=completion, issue=issue)
        if not all(isinstance(reason, Claim) for reason in reasons):
            msg = f"Reasons are not of type Claim. Got {reasons}."
            raise ValueError(msg)
        reasons = self._ensure_unique_labels(reasons)
        self.logger.debug(f"Mined reasons: {pprint.pformat(reasons)}")

        # identify basic options
        options = self._describe_options(issue=issue, prompt=prompt)
        self.logger.debug(f"Identified options: {pprint.pformat(options)}")

        # build pros and cons list
        pros_and_cons = self._build_pros_and_cons(
            reasons=reasons,
            issue=issue,
            options=options,
        )
        if not isinstance(pros_and_cons, ProsConsList):
            msg = f"Pros and cons list is not of type ProsConsList. Got {pros_and_cons}."
            raise ValueError(msg)

        # check for missing or duplicate reasons, add unused reasons
        pros_and_cons = self._check_and_revise_content(
            reasons=reasons,
            issue=issue,
            options=options,
            pros_and_cons=pros_and_cons,
        )

        self.logger.debug(f"Built pros and cons list: {pprint.pformat(pros_and_cons.model_dump())}")

        # double-check and revise
        pros_and_cons = await self._check_and_revise_logic(pros_and_cons, reasons, issue)
        self.logger.debug(f"Revised pros and cons list: {pprint.pformat(pros_and_cons.model_dump())}")

        if pros_and_cons is None:
            self.logger.warning("Failed to build pros and cons list (pros_and_cons is None).")

        try:
            pros_and_cons_data = pros_and_cons.model_dump()  # type: ignore
        except AttributeError:
            pros_and_cons_data = pros_and_cons.model_dump()

        artifact = Artifact(
            id=self.get_product(),
            description=self.get_description(),
            data=pros_and_cons_data,
            metadata={"reasons_list": reasons},
        )

        analysis_state.artifacts.append(artifact)
