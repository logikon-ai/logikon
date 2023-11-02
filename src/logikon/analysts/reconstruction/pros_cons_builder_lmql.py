"""Module with analyst for building a pros & cons list with LMQL

```mermaid
flowchart TD
    p["`prompt`"]
    c["`completion`"]
    i["`issue`"]
    r["`reasons (unstructured)`"]
    pcl["`pros cons list`"]
    ur["`reasons (unused)`"]
    rm("`reason mining
    :>_reasons_`")
    pco("`pros cons organizing
    :>_pros cons list_`")
    add("`add unused reasons
    :>_pros cons list_`")
    cr("`check and revise
    :>_pros cons list_`")
    subgraph artifact
    ad["`data`"]
    am["`metadata`"]
    end
    p --> rm
    c --> rm
    i --> rm
    rm --> r --> am
    i --> pco
    r --> pco --> add --> pco
    i --> cr
    pco --> cr --> pcl --> ad
    pco --> ur --> am
```

"""

from __future__ import annotations
from typing import List, TypedDict, Tuple

import copy
import functools as ft
import pprint
import random
import re
import signal
import uuid

import lmql

from logikon.analysts.lmql_analyst import LMQLAnalyst
import logikon.analysts.lmql_queries as lmql_queries
from logikon.utils.prompt_templates_registry import PromptTemplate
from logikon.schemas.results import Artifact, AnalysisState
from logikon.schemas.pros_cons import ProsConsList, RootClaim, Claim
import logikon.schemas.argument_mapping as am

MAX_N_REASONS = 18
MAX_N_ROOTS = 10
MAX_LEN_TITLE = 32
MAX_LEN_ROOTCLAIM = 128
MAX_LEN_GIST = 180
N_DRAFTS = 3
LABELS = "ABCDEFG"

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
    text = text.strip(" \'\n")
    if text[-1] not in [".", "!", "?"]:
        # split text at any of ".", "!", "?"
        splits = re.split(r"([.!?])", text)
        text = "".join(splits[:-1]) if len(splits) > 1 else text
    return text


def format_reason(reason: Claim, max_len: int = -1) -> str:
    label_text = f"[{reason.label}]: {reason.text}"
    if max_len > 0 and len(label_text) > max_len:
        label_text = label_text[:max_len] + "..."
    return f"- \"{label_text}\"\n"


def format_proscons(issue: str, proscons: ProsConsList, extra_reasons: list = []) -> str:
    formatted = "```yaml\n"
    # reasons block
    formatted += "reasons:\n"
    reasons = extra_reasons
    for root in proscons.roots:
        reasons.extend(root.pros)
        reasons.extend(root.cons)
    reasons = random.Random(42).sample(reasons, min(len(reasons), MAX_N_REASONS))
    for reason in reasons:
        formatted += format_reason(reason)
    # issue
    formatted += f"issue: \"{issue}\"\n"
    # pros and cons block
    formatted += "pros_and_cons:\n"
    for root in proscons.roots:
        formatted += f"- root: \"({root.label}): {root.text}\"\n"
        formatted += "  pros:\n"
        for pro in root.pros:
            formatted += f"  - \"[{pro.label}]\"\n"
        formatted += "  cons:\n"
        for con in root.cons:
            formatted += f"  - \"[{con.label}]\"\n"
    formatted += "```\n"
    return formatted


def format_examples() -> str:
    formatted = [format_proscons(*example) for example in EXAMPLES_ISSUE_PROSCONS]
    formatted = ["<example>\n" + example + "</example>" for example in formatted]
    formatted_s = "\n".join(formatted)
    return formatted_s


### LMQL QUERIES ###


@lmql.query
def mine_reasons(prompt, completion, issue, prmpt_data: dict) -> List[Claim]:  # type: ignore
    '''lmql
    sample(temperature=.4, chunksize=10)
        prmpt = PromptTemplate(**prmpt_data)
        """
        {prmpt.sys_start}
        {lmql_queries.system_prompt()}{prmpt.sys_end}

        {prmpt.user_start}
        Your Assignment: Summarize all the arguments (pros and cons) presented in a text.

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
        - For each argument, sketch the argument's gist in one or two grammatically correct sentences, staying close to the original wording.
        - In addition, provide a short caption that flashlights the argument's key idea (2-4 words). 
        - Use the following format:
            ```
            - gist: "state here the argument's gist in 1-2 concise sentences (in total less than {MAX_LEN_GIST} chars)."
              title: "argument's title (2-4 words)"
            ```
        - Avoid repeating one and the same argument in different words.
        - You don't have to distinguish between pro and con arguments.
        - IMPORTANT: Stay faithful to the text! Don't invent your own reasons. Only provide reasons which are either presented or discussed in the text.
        - Use yaml syntax and "```" code fences to structure your answer.{prmpt.user_end}
        {prmpt.ass_start}
        The TEXT sets forth the following arguments:

        ```yaml
        arguments:"""
        reasons = []
        marker = ""
        n = 0
        while n<MAX_N_REASONS:
            n += 1
            "[MARKER]" where MARKER in ["\n```", "\n- "]
            marker = MARKER
            if marker == "\n```":
                break
            else:
                "gist: \"[GIST]" where STOPS_AT(GIST, "\"") and STOPS_AT(GIST, "\n") and len(GIST) < MAX_LEN_GIST
                if not GIST.endswith('\"'):
                    "\" "
                "\n  title: \"[TITLE]" where STOPS_AT(TITLE, "\"") and STOPS_AT(TITLE, "\n") and len(TITLE) < MAX_LEN_TITLE
                if not TITLE.endswith('\"'):
                    "\" "
                title = TITLE.strip(' \"\n')
                gist = trunk_to_sentence(GIST.strip(' \"\n'))
                reasons.append(Claim(label=title, text=gist))
        return reasons
    '''


@lmql.query
def build_pros_and_cons(reasons_data: list, issue: str, prmpt_data: dict):
    '''lmql
    sample(temperature=.4, chunksize=6)
        reasons = [Claim(**reason_data) for reason_data in reasons_data]
        prmpt = PromptTemplate(**prmpt_data)
        """
        {prmpt.sys_start}
        {lmql_queries.system_prompt()}{prmpt.sys_end}

        {prmpt.user_start}
        Assignment: Organize an unstructured set of reasons as a pros & cons list.

        Let's begin by thinking through the basic issue addressed by the reasons:

        <issue>{issue}</issue>

        What are the basic options available to an agent who needs to address this issue?

        Keep your answer short: Sketch each option in 3-6 words only. State one option per line. Enclose your bullet list with "<options>"/"</options>" tags.{prmpt.user_end}
        {prmpt.ass_start}
        The options available to an agent who faces the above issue are (one per line):

        <options>
        """
        options = []
        markero = ""
        while len(options)<MAX_N_ROOTS:
            "[MARKERO]" where MARKERO in ["</options>", "- "]
            markero = MARKERO
            if markero == "</options>":
                break
            else:
                "[OPTION]" where STOPS_AT(OPTION, "\n") and len(OPTION) < MAX_LEN_TITLE
                if not OPTION.endswith("\n"):
                    "\n"
                options.append(OPTION.strip("\n "))
        if markero != "</options>":
            "</options> "
        else:
            " "
        """
        {prmpt.ass_end}
        {prmpt.user_start}
        Thanks, let's keep that in mind.

        Let us now come back to the main assignment: constructing a pros & cons list from a set of reasons.

        You'll be given a set of reasons, which you're supposed to organize as a pros and cons list. To do so, you have to find a fitting target claim (root statement) the reasons are arguing for (pros) or against (cons).

        Use the following inputs (a list of reasons that address an issue) to solve your assignment.

        <inputs>
        <issue>{issue}</issue>
        <reasons>
        """
        for reason in reasons:
            f_reason = format_reason(reason, 50)
            "{f_reason}"
        """</reasons>
        </inputs>

        Let me show you a few examples to illustrate the task / intended output:

        {format_examples()}

        Please consider carefully the following further, more specific instructions:

        * Be bold: Your root claim(s) should be simple and unequivocal, and correspond to the basic options you have identified above.
        * No reasoning: Your root claim(s) must not contain any reasoning (or comments, or explanations).
        * Keep it short: Try to identify a single root claim. Add further root claims only if necessary (e.g., if reasons address three alternative decision options).
        * Recall options: Use the options you've identified above to construct the pros and cons list.
        * Be exhaustive: All reasons must figure in your pros and cons list.
        * !!Re-organize!!: Don't stick to the order of the original reason list.

        Moreover:

        * Use simple and plain language.
        * If you identify multiple root claims, make sure they are mutually exclusive alternatives.
        * Avoid repeating one and the same root claim in different words.
        * Use yaml syntax and "```" code fences to structure your answer.{prmpt.user_end}
        {prmpt.ass_start}
        Let me recall the basic options before producing the pros and cons list:
        """
        for option in options:
            "- {option}\n"
        """

        ```yaml
        reasons:
        """
        for reason in reasons:
            f_reason = format_reason(reason)
            "{f_reason}"
        "issue: \"{issue}\"\n"
        "pros_and_cons:"
        unused_reasons = copy.deepcopy(reasons)
        roots = []
        "[MARKER]" where MARKER in ["\n```", "\n- "]
        marker = MARKER
        while len(roots)<MAX_N_ROOTS and unused_reasons:
            if marker == "\n```":
                break
            elif marker == "\n- ":  # new root
                "root: \"([TITLE]" where STOPS_AT(TITLE, ")") and STOPS_AT(TITLE, ":") and len(TITLE)<MAX_LEN_TITLE
                if TITLE.endswith(")"):
                    ":"
                elif not TITLE.endswith(":"):
                    "):"
                "[CLAIM]" where STOPS_AT(CLAIM, '\"') and STOPS_AT(CLAIM, "\n") and len(CLAIM)<MAX_LEN_ROOTCLAIM
                if not CLAIM.endswith('\"'):
                    "\" "
                root = RootClaim(label=TITLE.strip('): '), text=CLAIM.strip('\n\"'))
                "  pros:"
                while unused_reasons:
                    "[MARKER]" where MARKER in ["\n  cons:", "\n  - "]
                    marker = MARKER
                    if marker == "\n  - ":  # new pro
                        "\"[[[REASON_TITLE]]]\" " where REASON_TITLE in [reason.label for reason in unused_reasons]
                        selected_reason = next(reason for reason in unused_reasons if reason.label == REASON_TITLE)
                        root.pros.append(selected_reason)
                        unused_reasons.remove(selected_reason)
                    else:
                        break
                # cons
                while unused_reasons:
                    "[MARKER]" where MARKER in ["\n```", "\n- ", "\n  - "]
                    marker = MARKER
                    if marker == "\n  - ":  # new con
                        "\"[[[REASON_TITLE]]]\" " where REASON_TITLE in [reason.label for reason in unused_reasons]
                        selected_reason = next(reason for reason in unused_reasons if reason.label == REASON_TITLE)
                        root.cons.append(selected_reason)
                        unused_reasons.remove(selected_reason)
                    else:
                        break

                roots.append(root)
            else:
                break  # invalid marker!

        return ProsConsList(roots=roots, options=options), unused_reasons

    '''

# TODO: use same query logic as above!
@lmql.query
def add_unused_reasons(
    reasons_data: list, issue: str, pros_and_cons_data: dict, unused_reasons_data: list, prmpt_data: dict
):
    '''lmql
    argmax(chunksize=6)
        reasons = [Claim(**reason_data) for reason_data in reasons_data]
        unused_reasons = [Claim(**ureason_data) for ureason_data in unused_reasons_data]
        pros_and_cons = ProsConsList(**pros_and_cons_data)
        formatted_pcl = format_proscons(issue, pros_and_cons, unused_reasons)
        prmpt = PromptTemplate(**prmpt_data)
        """
        {prmpt.sys_start}
        {lmql_queries.system_prompt()}{prmpt.sys_end}

        {prmpt.user_start}
        Assignment: Organize the aforementioned unstructured set of reasons as a pros & cons list.

        ### Assistant

        {formatted_pcl}

        ### User

        Thanks! However, I've realized that the following reasons haven't been integrated in the pros & cons list, yet:
        """
        for ureason in unused_reasons:
            f_ureason = format_reason(ureason, 50)
            "{f_ureason}"
        """
        Can you please carefully check the above pros & cons list, correct any errors and add the missing reasons?{prmpt.user_end}
        {prmpt.ass_start}
        ```yaml
        reasons:
        """
        for reason in reasons:
            f_reason = format_reason(reason)
            "{f_reason}"
        "issue: \"{issue}\"\n"
        "pros_and_cons:\n"
        unused_reasons = copy.deepcopy(reasons)
        roots = []
        "[MARKER]" where MARKER in ["```", "- "]
        marker = MARKER
        while len(roots)<MAX_N_ROOTS and unused_reasons:
            if marker == "```":
                break
            elif marker == "- ":  # new root
                "root: \"([TITLE]" where STOPS_AT(TITLE, ")") and STOPS_AT(TITLE, ":") and len(TITLE)<MAX_LEN_TITLE
                if TITLE.endswith(")"):
                    ":"
                elif not TITLE.endswith(":"):
                    "):"
                "[CLAIM]" where STOPS_AT(CLAIM, "\n") and len(CLAIM)<MAX_LEN_ROOTCLAIM
                if not CLAIM.endswith("\n"):
                    "\n"
                root = RootClaim(label=TITLE.strip('): '), text=CLAIM.strip('\n\"'))
                "  pros:\n"
                while unused_reasons:
                    "[MARKER]" where MARKER in ["  cons:\n", "  - "]
                    marker = MARKER
                    if marker == "  - ":  # new pro
                        "\"[[[REASON_TITLE]]]\"\n" where REASON_TITLE in [reason.label for reason in unused_reasons]
                        selected_reason = next(reason for reason in unused_reasons if reason.label == REASON_TITLE)
                        root.pros.append(selected_reason)
                        unused_reasons.remove(selected_reason)
                    else:
                        break
                # cons
                while unused_reasons:
                    "[MARKER]" where MARKER in ["```", "- ", "  - "]
                    marker = MARKER
                    if marker == "  - ":  # new con
                        "\"[[[REASON_TITLE]]]\"\n" where REASON_TITLE in [reason.label for reason in unused_reasons]
                        selected_reason = next(reason for reason in unused_reasons if reason.label == REASON_TITLE)
                        root.cons.append(selected_reason)
                        unused_reasons.remove(selected_reason)
                    else:
                        break

                roots.append(root)

        return ProsConsList(roots=roots, options=pros_and_cons.options), unused_reasons

    '''


class ProsConsBuilderLMQL(LMQLAnalyst):
    """ProsConsBuilderLMQL

    This LMQLAnalyst is responsible for reconstructing a pros and cons list for a given issue.

    """

    __pdescription__ = "Pros and cons list with multiple root claims"
    __product__ = "proscons"
    __requirements__ = ["issue"]

    # timeout handler
    def _timeout_handler(self, signum, frame):
        raise TimeoutError("LMQL query timed out.")

    def _mine_reasons(self, prompt, completion, issue) -> List[Claim]:
        """Internal wrapper (class-method) for lmql.query function."""
        #signal.signal(signal.SIGALRM, self._timeout_handler)
        #try:
        #signal.alarm(self._lmql_query_timeout)
        reasons: List[Claim] = mine_reasons(
            prompt,
            completion,
            issue,
            prmpt_data=self._prompt_template.to_dict(),
            model=self._model,
            **self._generation_kwargs,
        )
        # postprocess reasons
        for reason in reasons:
            reason.label = reason.label.strip(" \"\n")
            reason.text = trunk_to_sentence(reason.text.strip(" \"\n"))
        return reasons
        #except TimeoutError:
        #    self.logger.warning("LMQL query _mine_reasons timed out.")
        #    signal.alarm(0)
        #    return []
        #finally:
        #    signal.alarm(0)

    def _build_pros_and_cons(self, reasons_data: list[dict], issue: str) -> Tuple[ProsConsList, List[Claim]]:
        """Internal wrapper (class-method) for lmql.query function."""
        #signal.signal(signal.SIGALRM, self._timeout_handler)
        #try:
        #signal.alarm(self._lmql_query_timeout)
        return build_pros_and_cons(
            reasons_data,
            issue,
            prmpt_data=self._prompt_template.to_dict(),
            model=self._model,
            **self._generation_kwargs,
        )
        #except TimeoutError:
        #    self.logger.warning("LMQL query build_pros_and_cons timed out.")
        #    signal.alarm(0)
        #    return ProsConsList(roots=[]), []
        #finally:
        #    signal.alarm(0)

    def _add_unused_reasons(
        self,
        reasons_data: list[dict],
        issue: str,
        pros_and_cons_data: dict,
        unused_reasons_data: list,
    ) -> Tuple[ProsConsList, List[Claim]]:
        """Internal wrapper (class-method) for lmql.query function."""
        #signal.signal(signal.SIGALRM, self._timeout_handler)
        #try:
        #   signal.alarm(self._lmql_query_timeout)
        return add_unused_reasons(
            reasons_data,
            issue,
            pros_and_cons_data,
            unused_reasons_data,
            prmpt_data=self._prompt_template.to_dict(),
            model=self._model,
            **self._generation_kwargs,
        )
        #except TimeoutError:
        #    self.logger.warning("LMQL query add_unused_reasons timed out.")
        #    signal.alarm(0)
        #    return ProsConsList(roots=[]), []
        #finally:
        #    signal.alarm(0)

    def _ensure_unique_labels(self, reasons: List[Claim]) -> List[Claim]:
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
        for reason in unique_reasons:
            if reason.label in duplicate_labels:
                i = 1
                new_label = f"{reason.label}-{str(i)}"
                while new_label in labels:
                    if i >= MAX_N_REASONS:
                        self.logger.warning("Failed to ensure unique labels for reasons.")
                        break
                    i += 1
                    new_label = f"{reason.label}-{str(i)}"
                reason.label = new_label
                labels.append(new_label)

        return unique_reasons

    def _check_and_revise(self, pros_and_cons: ProsConsList, reasons: List[Claim], issue: str) -> ProsConsList:
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

        revisions: List[Revision] = []

        revised_pros_and_cons = copy.deepcopy(pros_and_cons)

        for enum, root in enumerate(revised_pros_and_cons.roots):
            for pro in root.pros:
                # check target
                lmql_result = lmql_queries.most_confirmed(
                    pro.dict(),
                    [r.dict() for r in revised_pros_and_cons.roots],
                    prmpt_data=self._prompt_template.to_dict(),
                    model=self._model,
                    **self._generation_kwargs,
                )
                if lmql_result is None:
                    continue
                probs_confirmed = lmql_queries.get_distribution(lmql_result)
                max_confirmed = max(probs_confirmed, key=lambda x: x[1])
                if max_confirmed[1] < 2 * probs_confirmed[enum][1]:
                    continue

                old_val = am.SUPPORT
                new_val = old_val
                old_target_idx = enum
                new_target_idx = lmql_queries.label_to_idx(max_confirmed[0])

                # sanity check 1
                lmql_result = lmql_queries.most_disconfirmed(
                    pro.dict(),
                    [r.dict() for r in revised_pros_and_cons.roots],
                    prmpt_data=self._prompt_template.to_dict(),
                    model=self._model,
                    **self._generation_kwargs,
                )
                if lmql_result is None:
                    continue
                probs_disconfirmed = lmql_queries.get_distribution(lmql_result)
                max_disconfirmed = max(probs_disconfirmed, key=lambda x: x[1])
                if max_confirmed[0] == max_disconfirmed[0]:
                    continue

                # sanity check 2
                lmql_result = lmql_queries.valence(
                    pro.dict(),
                    revised_pros_and_cons.roots[new_target_idx].dict(),
                    issue=issue,
                    prmpt_data=self._prompt_template.to_dict(),
                    model=self._model,
                    **self._generation_kwargs,
                )
                if lmql_result is None:
                    continue
                new_val = lmql_queries.label_to_valence(lmql_result.variables[lmql_result.distribution_variable])
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
                lmql_result = lmql_queries.most_disconfirmed(
                    con.dict(),
                    [r.dict() for r in revised_pros_and_cons.roots],
                    prmpt_data=self._prompt_template.to_dict(),
                    model=self._model,
                    **self._generation_kwargs,
                )
                if lmql_result is None:
                    continue
                probs_disconfirmed = lmql_queries.get_distribution(lmql_result)
                max_disconfirmed = max(probs_disconfirmed, key=lambda x: x[1])
                if max_disconfirmed[1] < 2 * probs_disconfirmed[enum][1]:
                    continue

                old_val = am.ATTACK
                new_val = old_val
                old_target_idx = enum
                new_target_idx = lmql_queries.label_to_idx(max_disconfirmed[0])

                # sanity check 1
                lmql_result = lmql_queries.most_confirmed(
                    con.dict(),
                    [r.dict() for r in revised_pros_and_cons.roots],
                    prmpt_data=self._prompt_template.to_dict(),
                    model=self._model,
                    **self._generation_kwargs,
                )
                if lmql_result is None:
                    continue
                probs_confirmed = lmql_queries.get_distribution(lmql_result)
                max_confirmed = max(probs_confirmed, key=lambda x: x[1])
                if max_disconfirmed[0] == max_confirmed[0]:
                    continue

                # sanity check 2
                lmql_result = lmql_queries.valence(
                    con.dict(),
                    revised_pros_and_cons.roots[new_target_idx].dict(),
                    issue=issue,
                    prmpt_data=self._prompt_template.to_dict(),
                    model=self._model,
                    **self._generation_kwargs,
                )
                if lmql_result is None:
                    continue
                new_val = lmql_queries.label_to_valence(lmql_result.variables[lmql_result.distribution_variable])
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

    def _analyze(self, analysis_state: AnalysisState):
        """Extract pros and cons of text (prompt/completion).

        Args:
            analysis_state (AnalysisState): current analysis_state to which new artifact is added

        Raises:
            ValueError: Failure to create pros and cons list

        Proceeds as follows:

        1. Mine (i.e., extract) all individual reasons from prompt/completion text
        2. Organize reasons into pros and cons list
        3. Double-check and revise pros and cons list

        """

        prompt, completion = analysis_state.get_prompt_completion()
        issue = next(a.data for a in analysis_state.artifacts if a.id == "issue")

        if prompt is None or completion is None:
            raise ValueError(
                f"Prompt or completion is None. {self.__class__} requires both prompt and completion to analyze."
            )

        # mine reasons
        reasons = self._mine_reasons(prompt=prompt, completion=completion, issue=issue)
        if not all(isinstance(reason, Claim) for reason in reasons):
            raise ValueError(f"Reasons are not of type Claim. Got {reasons}.")
        reasons = self._ensure_unique_labels(reasons)
        self.logger.debug(f"Mined reasons: {pprint.pformat(reasons)}")

        # build pros and cons list
        pros_and_cons, unused_reasons = self._build_pros_and_cons(reasons_data=[r.dict() for r in reasons], issue=issue)
        if not isinstance(pros_and_cons, ProsConsList):
            raise ValueError(f"Pros and cons list is not of type ProsConsList. Got {pros_and_cons}.")
        # add unused reasons
        if unused_reasons:
            self.logger.debug(f"Unused reasons: {pprint.pformat(unused_reasons)}")
            pros_and_cons, unused_reasons = self._add_unused_reasons(
                reasons_data=[r.dict() for r in reasons],
                issue=issue,
                pros_and_cons_data=pros_and_cons.dict(),
                unused_reasons_data=[r.dict() for r in unused_reasons],
            )
            if unused_reasons:
                self.logger.info(f"Failed to integrate the following reasons: {pprint.pformat(unused_reasons)}")
        # TODO: consider drafting alternative pros&cons lists and choosing best
        self.logger.debug(f"Built pros and cons list: {pprint.pformat(pros_and_cons.dict())}")

        # double-check and revise
        pros_and_cons = self._check_and_revise(pros_and_cons, reasons, issue)
        self.logger.debug(f"Revised pros and cons list: {pprint.pformat(pros_and_cons.dict())}")

        if pros_and_cons is None:
            self.logger.warning("Failed to build pros and cons list (pros_and_cons is None).")

        try:
            pros_and_cons_data = pros_and_cons.model_dump()  # type: ignore
        except AttributeError:
            pros_and_cons_data = pros_and_cons.dict()

        artifact = Artifact(
            id=self.get_product(),
            description=self.get_description(),
            data=pros_and_cons_data,
            metadata={"reasons_list": reasons, "unused_reasons_list": unused_reasons},
        )

        analysis_state.artifacts.append(artifact)
