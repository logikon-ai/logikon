"""Module with analyst for building a pros & cons list with LMQL

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

import copy
import pprint
import random
import re
from typing import ClassVar, TypedDict

import lmql

import logikon.schemas.argument_mapping as am
from logikon.analysts import lmql_queries
from logikon.analysts.lmql_analyst import LMQLAnalyst
from logikon.schemas.pros_cons import Claim, ProsConsList, RootClaim
from logikon.schemas.results import AnalysisState, Artifact
from logikon.utils.prompt_templates_registry import PromptTemplate

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
        # remove preceding marks
        text = text.strip(".!? ")
        # split text at any of ".", "!", "?"
        splits = re.split(r"([.!?])", text)
        text = "".join(splits[:-1]) if len(splits) > 1 else text
    return text


def format_reason(reason: Claim, max_len: int = -1, label_only: bool = False) -> str:  # noqa: FBT001, FBT002
    if label_only:
        label_text = f"[{reason.label}]"
    else:
        label_text = f"[{reason.label}]: {reason.text}"
    if max_len > 0 and len(label_text) > max_len:
        label_text = label_text[:max_len] + "..."
    return f'- "{label_text}"\n'


def format_reasons(reasons: list[Claim], **kwargs) -> str:
    formatted = "".join([format_reason(reason, **kwargs) for reason in reasons])
    return formatted


def format_proscons(issue: str, proscons: ProsConsList, extra_reasons: list | None = None) -> str:
    formatted = "```yaml\n"
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
    for reason in reasons:
        formatted += format_reason(reason)
    # issue
    formatted += f'issue: "{issue}"\n'
    # pros and cons block
    formatted += "pros_and_cons:\n"
    for root in proscons.roots:
        formatted += f'- root: "({root.label}): {root.text}"\n'
        formatted += "  pros:\n"
        for pro in root.pros:
            formatted += f'  - "[{pro.label}]"\n'
        formatted += "  cons:\n"
        for con in root.cons:
            formatted += f'  - "[{con.label}]"\n'
    formatted += "```\n"
    return formatted


def format_examples() -> str:
    formatted = [format_proscons(*example) for example in EXAMPLES_ISSUE_PROSCONS]
    formatted = ["<example>\n" + example + "</example>" for example in formatted]
    formatted_s = "\n".join(formatted)
    return formatted_s


def format_options(options: list[str]) -> str:
    formatted = "\n".join([f"- {o}" for o in options])
    return formatted


### PROMPT TEMPLATES ###


def pros_and_cons_preamble(reasons: list[Claim], issue: str, options: list[str], prmpt: PromptTemplate) -> str:
    "Prompt preamble (template) for building pros and cons list."
    return f"""
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
{format_options(options)}
<options/>
{prmpt.ass_end}
{prmpt.user_start}
Thanks, let's keep that in mind.

Let us now come back to the main assignment: constructing a pros & cons list from a set of reasons.

You'll be given a set of reasons, which you're supposed to organize as a pros and cons list. To do so, you have to find a fitting target claim (root statement) the reasons are arguing for (pros) or against (cons).

Use the following inputs (a list of reasons that address an issue) to solve your assignment.

<inputs>
<issue>{issue}</issue>
<reasons>
{format_reasons(reasons)}
</reasons>
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
{format_options(options)}
"""


def add_reasons_preamble(
    formatted_proscons: str, formatted_unused_reasons: str, options: list[str], prmpt: PromptTemplate  # noqa: ARG001
) -> str:
    """Prompt preamble (template) for adding unused reasons to pros and cons list."""
    return f"""
{prmpt.sys_start}
{lmql_queries.system_prompt()}{prmpt.sys_end}

{prmpt.user_start}
Assignment: Organize the aforementioned unstructured set of reasons as a pros & cons list.

### Assistant

{formatted_proscons}

### User

Thanks! However, I've realized that the following reasons haven't been integrated in the pros & cons list, yet:

{formatted_unused_reasons}

Can you please carefully check the above pros & cons list, correct any errors and add the missing reasons?{prmpt.user_end}
{prmpt.ass_start}
"""


### LMQL QUERIES ###

# TODO: Check redundancy of mined reason claims
# TODO: Check if every root claim has a text, if not, provide one.
# TODO: Revise and improve root claims in pros cons list


@lmql.query
def mine_reasons(prompt: str, completion: str, issue: str, prmpt_data: dict) -> list[Claim]:  # type: ignore  # noqa: ARG001
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
def describe_options(issue: str, prmpt_data: dict):  # noqa: ARG001
    '''lmql
    sample(temperature=.4, chunksize=6)
        prmpt = PromptTemplate(**prmpt_data)
        """
        {prmpt.sys_start}
        {lmql_queries.system_prompt()}{prmpt.sys_end}

        {prmpt.user_start}
        Assignment: Build a pros & cons list for a given issue.

        **Plan**
        Step 1: State the central issue.
        Step 2: Identify the basic options available to an agent who faces the issue.
        Step 3: Construct a pros & cons list for the issue.


        **Step 1**
        Let's begin by stating our central issue clearly and concisely:{prmpt.user_end}
        {prmpt.ass_start}

        <issue>
        {issue}
        </issue> {prmpt.ass_end}

        {prmpt.user_start}
        **Step 2**
        What are the basic options available to an agent who needs to address the above issue?

        Keep your answer short: Sketch each option in 2-6 words only. State one option per line. Prefer imperative mood. Enclose your bullet list with "<options>"/"</options>" tags.{prmpt.user_end}
        {prmpt.ass_start}
        The options available to an agent who faces the above issue are (one per line, 2-6 words each):

        <options>
        """
        options = []
        marker = ""
        while len(options)<MAX_N_ROOTS:
            "[MARKER]" where MARKER in ["</options>", "- "]
            marker = MARKER
            if marker == "</options>":
                break
            else:
                "[OPTION]" where STOPS_AT(OPTION, "\n") and len(OPTION) < MAX_LEN_TITLE
                if not OPTION.endswith("\n"):
                    "\n"
                options.append(OPTION.strip("\n "))
        return options
    '''


@lmql.query
def build_pros_and_cons(
    reasons_data: list, issue: str, options: list[str], prompt_preamble: str, prmpt_data: dict  # noqa: ARG001
):
    '''lmql
    sample(temperature=.4, chunksize=6)
        reasons = [Claim(**reason_data) for reason_data in reasons_data]
        prmpt = PromptTemplate(**prmpt_data)
        """
        {prompt_preamble}
        ```yaml
        reasons:
        """
        for reason in reasons:
            f_reason = format_reason(reason)
            "{f_reason}"
        "issue: \"{issue}\"\n"
        unused_reasons = copy.deepcopy(reasons)
        roots = []
        marker = "\n- "
        "pros_and_cons:{marker}"
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
                root = RootClaim(label=TITLE.strip('): '), text=CLAIM.strip('\n\" '))
                "\n  pros:"
                while unused_reasons:
                    "[MARKER]" where MARKER in ["\n  cons:", "\n  -"]
                    marker = MARKER
                    if marker == "\n  -":  # new pro
                        " \"[[[REASON_TITLE]]]\" " where REASON_TITLE in [reason.label for reason in unused_reasons]
                        selected_reason = next(reason for reason in unused_reasons if reason.label == REASON_TITLE)
                        root.pros.append(selected_reason)
                        unused_reasons.remove(selected_reason)
                    else:
                        break
                # cons
                while unused_reasons:
                    "[MARKER]" where MARKER in ["\n```", "\n- ", "\n  -"]
                    marker = MARKER
                    if marker == "\n  -":  # new con
                        " \"[[[REASON_TITLE]]]\" " where REASON_TITLE in [reason.label for reason in unused_reasons]
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


class ProsConsBuilderLMQL(LMQLAnalyst):
    """ProsConsBuilderLMQL

    This LMQLAnalyst is responsible for reconstructing a pros and cons list for a given issue.

    """

    __pdescription__ = "Pros and cons list with multiple root claims"
    __product__ = "proscons"
    __requirements__: ClassVar[list[str | set]] = ["issue"]

    @LMQLAnalyst.timeout
    def _mine_reasons(self, prompt, completion, issue) -> list[Claim]:
        """Internal wrapper (class-method) for lmql.query function."""
        reasons: list[Claim] = mine_reasons(
            prompt=prompt,
            completion=completion,
            issue=issue,
            prmpt_data=self._prompt_template.to_dict(),
            model=self._model,
            **self._generation_kwargs,
        )
        # postprocess reasons
        for reason in reasons:
            reason.label = reason.label.strip(' "\n')
            reason.text = trunk_to_sentence(reason.text.strip(' "\n'))
        return reasons

    @LMQLAnalyst.timeout
    def _describe_options(self, issue) -> list[str]:
        """Internal wrapper (class-method) for lmql.query function."""
        options: list[str] = describe_options(
            issue=issue,
            prmpt_data=self._prompt_template.to_dict(),
            model=self._model,
            **self._generation_kwargs,
        )
        return options

    @LMQLAnalyst.timeout
    def _build_pros_and_cons(
        self, reasons_data: list[dict], issue: str, options: list[str]
    ) -> tuple[ProsConsList, list[Claim]]:
        """Internal wrapper (class-method) for lmql.query function."""
        preamble = pros_and_cons_preamble(
            reasons=[Claim(**r) for r in reasons_data],
            issue=issue,
            options=options,
            prmpt=self._prompt_template,
        )

        return build_pros_and_cons(
            reasons_data=reasons_data,
            issue=issue,
            options=options,
            prompt_preamble=preamble,
            prmpt_data=self._prompt_template.to_dict(),
            model=self._model,
            **self._generation_kwargs,
        )

    @LMQLAnalyst.timeout
    def _add_unused_reasons(
        self,
        reasons_data: list[dict],
        issue: str,
        options: list[str],
        pros_and_cons: ProsConsList,
        unused_reasons: list[Claim],
    ) -> tuple[ProsConsList, list[Claim]]:
        """Internal wrapper (class-method) for lmql.query function."""
        formatted_proscons: str = format_proscons(
            issue=issue,
            proscons=pros_and_cons,
            extra_reasons=unused_reasons,
        )
        formatted_unused_reasons: str = format_reasons(unused_reasons)
        preamble = add_reasons_preamble(
            formatted_proscons=formatted_proscons,
            formatted_unused_reasons=formatted_unused_reasons,
            options=options,
            prmpt=self._prompt_template,
        )
        self.logger.debug(f"Prompt preamble:\n{preamble}")

        return build_pros_and_cons(
            reasons_data=reasons_data,
            issue=issue,
            options=options,
            prompt_preamble=preamble,
            prmpt_data=self._prompt_template.to_dict(),
            model=self._model,
            **self._generation_kwargs,
        )

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
        for reason in unique_reasons:
            if reason.label in duplicate_labels:
                i = 1
                new_label = f"{reason.label}-{i!s}"
                while new_label in labels:
                    if i >= MAX_N_REASONS:
                        self.logger.warning("Failed to ensure unique labels for reasons.")
                        break
                    i += 1
                    new_label = f"{reason.label}-{i!s}"
                reason.label = new_label
                labels.append(new_label)

        return unique_reasons

    def _check_and_revise(
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
        options = self._describe_options(issue=issue)
        self.logger.debug(f"Identified options: {pprint.pformat(options)}")

        # build pros and cons list
        pros_and_cons, unused_reasons = self._build_pros_and_cons(
            reasons_data=[r.dict() for r in reasons],
            issue=issue,
            options=options,
        )
        if not isinstance(pros_and_cons, ProsConsList):
            msg = f"Pros and cons list is not of type ProsConsList. Got {pros_and_cons}."
            raise ValueError(msg)

        # add unused reasons
        if unused_reasons:
            self.logger.debug(f"Incomplete pros and cons list: {pprint.pformat(pros_and_cons.dict())}")
            self.logger.debug(f"Unused reasons: {pprint.pformat(unused_reasons)}")
            pros_and_cons, unused_reasons = self._add_unused_reasons(
                reasons_data=[r.dict() for r in reasons],
                issue=issue,
                options=options,
                pros_and_cons=pros_and_cons,
                unused_reasons=unused_reasons,
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
