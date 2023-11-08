"""Module with analyst for identifying text's central issue with LMQL

```mermaid
flowchart TD
    p["`prompt`"]
    c["`completion`"]
    di("`identify issue`")
    i1["`issue draft-1`"]
    i2["`issue draft-2`"]
    in["`issue draft-n`"]
    q["`eval criteria`"]
    i["`issue`"]
    rs("`rate and select`")
    subgraph artifact
    ad["`data`"]
    am["`metadata`"]
    end
    p --> di
    c --> di
    di --> i1 --> rs
    di --> i2 --> rs
    di --> in --> rs
    q --> rs
    rs --> i --> ad
```

"""
from __future__ import annotations

import re
from typing import Any

import lmql

from logikon.analysts import lmql_queries  # noqa: F401
from logikon.analysts.lmql_analyst import LMQLAnalyst
from logikon.schemas.results import AnalysisState, Artifact
from logikon.utils.prompt_templates_registry import PromptTemplate  # noqa: F401

MAX_LEN_ISSUE = 80
N_DRAFTS = 3
LABELS = "ABCDEFG"
QUESTIONS_EVAL = [
    "Which alternative captures best the text's overarching issue addressed?",
    "Which alternative is most clear and concise?",
    "Which alternative is most faithful to the text?",
]

# examples


# prompt templates


def strip_issue_tag(text: str) -> str:
    """Strip issue tag from text."""
    text = text.strip("\n ")
    if text.endswith("</ISSUE>"):
        text = text[: -len("</ISSUE>")].strip("\n ")
    if text[-1] not in [".", "!", "?"]:
        # split text at any of ".", "!", "?"
        splits = re.split(r"([.!?])", text)
        text = "".join(splits[:-1]) if len(splits) > 1 else text
    return text


@lmql.query
def key_issue(prompt, completion, prmpt_data: dict):  # noqa: ARG001
    '''lmql
    sample(n=3, temperature=.5, chunksize=4)
        prmpt = PromptTemplate(**prmpt_data)
        "{prmpt.sys_start}"
        "{lmql_queries.system_prompt()}{prmpt.sys_end}"
        "{prmpt.user_start}"
        "Assignment: Analyse and reconstruct a text's argumentation.\n\n"
        "The argumentative analysis proceeds in three steps:\n\n"
        "Step 1. Identify central issue\n"
        "Step 2. Identify key claims discussed\n"
        "Step 3. Set up a pros & cons list\n\n"
        "Before we start, let's study the text to-be-analysed carefully.\n\n"
        "<TEXT>\n"
        "{prompt}{completion}\n"
        "</TEXT>\n\n"
        "**Step 1**\n\n"
        "State the central issue / decision problem discussed in the TEXT in a few words.\n"
        "Be as brief and concise as possible. Think of your answer as the headline of an argument or debate.\n"
        "Enclose your answer in \"<ISSUE>\" / \"</ISSUE>\" tags.{prmpt.user_end}"
        "{prmpt.ass_start}"
        "<ISSUE> [@strip_issue_tag ISSUE]"
    where
        STOPS_AT(ISSUE, "</ISSUE>") and len(ISSUE) < MAX_LEN_ISSUE
    '''


@lmql.query
def rate_issue_drafts(alternatives, questions, prompt, completion, prmpt_data: dict):  # noqa: ARG001
    '''lmql
    argmax(chunksize=4)
        labels = [alternative.get('label') for alternative in alternatives]
        prmpt = PromptTemplate(**prmpt_data)
        "{prmpt.sys_start}"
        "{lmql_queries.system_prompt()}{prmpt.sys_end}"
        "{prmpt.user_start}"
        "Assignment: Rate different summarizations of a text's key issue.\n\n"
        "Before we start, let's study the text to-be-analysed carefully.\n\n"
        "<TEXT>\n"
        "{prompt}{completion}\n"
        "</TEXT>\n\n"
        "Consider the following alternatives, which attempt to summarize the central "
        "issue / basic decision discussed in the TEXT in a single sentence.\n\n"
        "<ALTERNATIVES>\n"
        for alternative in alternatives:
            "({alternative.get('label')}) \"{alternative.get('text')}\"\n"
        "</ALTERNATIVES>\n\n"
        "Compare and evaluate the different alternatives according to {len(alternatives)} "
        "relevant criteria which are put as questions. (At this point, just answer each "
        "question with {'/'.join(labels)}; you'll be asked to explain your answers later.)\n"
        "Conclude with an aggregate assessment of the alternatives.{prmpt.user_end}"
        "{prmpt.ass_start}"
        for question in questions:
            "{question} \n"
            "Answer: ([ANSWER])\n\n" where ANSWER in set(labels)
        "So, all in all and given the above assessments, the best summarization of the "
        "text's key issue is which alternative?\n"
        "Answer: ([FINAL_ANSWER])" where FINAL_ANSWER in set(labels)
    '''


class IssueBuilderLMQL(LMQLAnalyst):
    """IssueBuilderLMQL

    This LMQLAnalyst is responsible for summarizing the issue discussed in a text.
    """

    __pdescription__ = "Issue or decision problem addressed in the deliberation"
    __product__ = "issue"

    def _key_issue(self, prompt: str, completion: str) -> list[dict[str, Any]]:
        """Internal (class-method) wrapper for lmql.query function."""
        results = key_issue(
            prompt=prompt,
            completion=completion,
            prmpt_data=self._prompt_template.to_dict(),
            model=self._model,
            **self._generation_kwargs,
        )
        if not all(isinstance(result, lmql.LMQLResult) for result in results):
            msg = f"Results are not of type lmql.LMQLResult. Got {results}."
            raise ValueError(msg)
        issue_drafts = [
            {
                "text": result.variables.get("ISSUE", "").strip("\n "),
                "label": LABELS[enum],
            }
            for enum, result in enumerate(results)
        ]
        return issue_drafts

    def _rate_issue_drafts(
        self, alternatives: list[dict[str, Any]], questions: list[str], prompt: str, completion: str
    ) -> str | None:
        """Internal (class-method) wrapper for lmql.query function.

        Returns:
            str: label of best alternative
        """
        result = rate_issue_drafts(
            alternatives=alternatives,
            questions=questions,
            prompt=prompt,
            completion=completion,
            prmpt_data=self._prompt_template.to_dict(),
            model=self._model,
            **self._generation_kwargs,
        )
        if not isinstance(result, lmql.LMQLResult):
            msg = f"Results are not of type lmql.LMQLResult. Got {result}."
            raise ValueError(msg)
        label = result.variables.get("FINAL_ANSWER")
        return label

    def _analyze(self, analysis_state: AnalysisState):
        """Extract central issue of text (prompt/completion)."""

        prompt, completion = analysis_state.get_prompt_completion()
        if prompt is None or completion is None:
            msg = f"Prompt or completion is None. {self.__class__} requires both prompt and completion to analyse."
            raise ValueError(msg)

        # draft summarizations
        issue_drafts = self._key_issue(
            prompt=prompt,
            completion=completion,
        )
        self.logger.debug(f"Drafts: {issue_drafts}")

        # rate summarizations and choose best
        label = self._rate_issue_drafts(
            alternatives=issue_drafts,
            questions=QUESTIONS_EVAL,
            prompt=prompt,
            completion=completion,
        )
        issue = next((draft["text"] for draft in issue_drafts if draft["label"] == label), None)

        if issue is None:
            if issue_drafts:
                self.logger.warning("Failed to rate issue drafts, picking first alternative.")
                issue = issue_drafts[0]["text"]
            else:
                self.logger.warning("Failed to elicit issue (issue is None).")

        artifact = Artifact(
            id=self.get_product(),
            description=self.get_description(),
            data=issue,
        )

        analysis_state.artifacts.append(artifact)
