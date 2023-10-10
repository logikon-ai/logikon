# issue_builder_ol.py

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


@lmql.query
def key_issue(prompt, completion):
    """
    beam_sample(n=3, temperature=.4)
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
        "Summarize the central issue / decision problem discussed in the TEXT in a single sentence. Enclose your answer in \"<ISSUE>\" / \"</ISSUE>\" tags.\n\n"
        "### Assistant\n\n"
        "<ISSUE>\n"
        "[ISSUE]"
    where
        STOPS_AT(ISSUE, "</ISSUE>")
    """


@lmql.query
def rate_issue_drafts(alternatives, questions, prompt, completion):
    """
    argmax
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
            "Answer: ([ANSWER])\n\n"
        "So, all in all and given the above assessments, the best summarization of the text's key issue is which alternative?\n"
        "Answer: ([FINAL_ANSWER])"
    where
        ANSWER in set(labels) and FINAL_ANSWER in set(labels)
    """


class IssueBuilderLMQL(LMQLDebugger):
    """IssueBuilderLMQL

    This LMQLDebugger is responsible for summarizing the issue discussed in a text.
    """

    _KW_DESCRIPTION = "Issue or decision problem addressed in the deliberation"
    _KW_PRODUCT = "issue"

    @staticmethod
    def get_product() -> str:
        return IssueBuilderLMQL._KW_PRODUCT

    @staticmethod
    def get_description() -> str:
        return IssueBuilderLMQL._KW_DESCRIPTION

    def _debug(self, debug_state: DebugState):
        """Extract central issue of text (prompt/completion)."""

        prompt, completion = debug_state.get_prompt_completion()
        if prompt is None or completion is None:
            raise ValueError(f"Prompt or completion is None. {self.__class__} requires both prompt and completion to debug.")

        # draft summarizations
        results = key_issue(
            prompt=prompt,
            completion=completion,
            model=self._model,
            **self._model_kwargs,
        )
        issue_drafts = [
            {
                "text": result.variables.get("ISSUE").strip("\n "),
                "label": LABELS[enum],
            }
            for enum, result in enumerate(results)
        ]

        # rate summarizations and choose best
        result = rate_issue_drafts(
            alternatives=issue_drafts,
            questions=QUESTIONS_EVAL,
            prompt=prompt,
            completion=completion,
            model=self._model,
            **self._model_kwargs,
        )
        label = result.variables.get("FINAL_ANSWER")
        issue = next((draft["text"] for draft in issue_drafts if draft["label"] == label), None)

        if issue is None:
            self.logger.warning("Failed to elicit issue (issue is None).")

        artifact = Artifact(
            id=self._KW_PRODUCT,
            description=self._KW_DESCRIPTION,
            data=issue,
        )

        debug_state.artifacts.append(artifact)
