"""Module with debugger for identifying text's central issue with LMQL

```mermaid
flowchart TD
    p["`prompt`"]
    c["`completion`"]
    di("`state issue
    :>_issue draft_`")
    i1["`issue draft-1`"]
    i2["`issue draft-2`"]
    in["`issue draft-n`"]
    q["`eval criteria`"]
    i["`issue`"]
    rs("`rate and select
    :>_reasons_`")
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

import lmql

from logikon.debuggers.reconstruction.lmql_debugger import LMQLDebugger
from logikon.schemas.results import Artifact, DebugState

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
    return text.strip("</ISSUE>").strip("\n ")


@lmql.query
def key_issue(prompt, completion):
    """
    sample(n=3, temperature=.4, chunksize=4)
        "### System\n\n"
        "You are a helpful argumentation analysis assistant.\n\n"
        "### User\n\n"
        "Assignment: Analyse and reconstruct a text's argumentation.\n\n"
        "The argumentative analysis proceeds in three steps:\n\n"
        "1. Identify central issue\n"
        "2. Identify key claims discussed\n"
        "3. Set up a pros & cons list\n\n"
        "Before we start, let's study the text to-be-analysed carefully.\n\n"
        "<TEXT>\n"
        "{prompt}{completion}\n"
        "</TEXT>\n\n"
        "## Step 1\n\n"
        "State the central issue / decision problem discussed in the TEXT in a few words.\n"
        "Be as brief and concise as possible. Think of your answer as the headline of an argument or debate.\n"
        "Enclose your answer in \"<ISSUE>\" / \"</ISSUE>\" tags.\n\n"
        "### Assistant\n\n"
        "<ISSUE>\n"
        "[@strip_issue_tag ISSUE]"
    where
        STOPS_AT(ISSUE, "</ISSUE>")
    """


@lmql.query
def rate_issue_drafts(alternatives, questions, prompt, completion):
    '''lmql
    argmax(chunksize=4)
        labels = [alternative.get('label') for alternative in alternatives]
        "### System\n\n"
        "You are a helpful argumentation analysis assistant.\n\n"
        "### User\n\n"
        "Assignment: Rate different summarizations of a text's key issue.\n\n"
        "Before we start, let's study the text to-be-analysed carefully.\n\n"
        "<TEXT>\n"
        "{prompt}{completion}\n"
        "</TEXT>\n\n"
        "Consider the following alternatives, which attempt to summarize the central issue / basic decision discussed in the TEXT in a single sentence.\n\n"
        "<ALTERNATIVES>\n"
        for alternative in alternatives:
            "({alternative.get('label')}) \"{alternative.get('text')}\"\n"
        "</ALTERNATIVES>\n\n"
        "Compare and evaluate the different alternatives according to {len(alternatives)} relevant criteria which are put as questions. (At this point, just answer each question with {'/'.join(labels)}; you'll be asked to explain your answers later.)\n"
        "Conclude with an aggregate assessment of the alternatives.\n\n"
        "### Assistant\n\n"
        for question in questions:
            "{question} \n"
            "Answer: ([ANSWER])\n\n" where ANSWER in set(labels)
        "So, all in all and given the above assessments, the best summarization of the text's key issue is which alternative?\n"
        "Answer: ([FINAL_ANSWER])" where FINAL_ANSWER in set(labels)
    '''


class IssueBuilderLMQL(LMQLDebugger):
    """IssueBuilderLMQL

    This LMQLDebugger is responsible for summarizing the issue discussed in a text.
    """

    __pdescription__ = "Issue or decision problem addressed in the deliberation"
    __product__ = "issue"

    def _key_issue(self, prompt, completion):  # TODO: add type hints
        """Internal (class-method) wrapper for lmql.query function."""
        return key_issue(
            prompt=prompt,
            completion=completion,
            model=self._model,
            **self._generation_kwargs,
        )

    def _rate_issue_drafts(self, alternatives, questions, prompt, completion):  # TODO: add type hints
        """Internal (class-method) wrapper for lmql.query function."""
        return rate_issue_drafts(
            alternatives=alternatives,
            questions=questions,
            prompt=prompt,
            completion=completion,
            model=self._model,
            **self._generation_kwargs,
        )

    def _debug(self, debug_state: DebugState):
        """Extract central issue of text (prompt/completion)."""

        prompt, completion = debug_state.get_prompt_completion()
        if prompt is None or completion is None:
            raise ValueError(
                f"Prompt or completion is None. {self.__class__} requires both prompt and completion to debug."
            )

        # draft summarizations
        results = self._key_issue(
            prompt=prompt,
            completion=completion,
        )
        # TODO: move LMQL logic in query function / wrapper
        if not all(isinstance(result, lmql.LMQLResult) for result in results):
            raise ValueError(f"Results are not of type lmql.LMQLResult. Got {results}.")
        issue_drafts = [
            {
                "text": result.variables.get("ISSUE", "").strip("\n "),
                "label": LABELS[enum],
            }
            for enum, result in enumerate(results)
        ]
        self.logger.info(f"Drafts: {issue_drafts}")

        # rate summarizations and choose best
        result = self._rate_issue_drafts(
            alternatives=issue_drafts,
            questions=QUESTIONS_EVAL,
            prompt=prompt,
            completion=completion,
        )
        label = result.variables.get("FINAL_ANSWER")
        issue = next((draft["text"] for draft in issue_drafts if draft["label"] == label), None)

        if issue is None:
            self.logger.warning("Failed to elicit issue (issue is None).")

        artifact = Artifact(
            id=self.get_product(),
            description=self.get_description(),
            data=issue,
        )

        debug_state.artifacts.append(artifact)
