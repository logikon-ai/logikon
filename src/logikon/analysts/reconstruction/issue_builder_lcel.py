"""Module with analyst for identifying text's central issue with LCEL

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
from typing import Any, Sequence

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.runnables import RunnableLambda

from logikon.analysts.lcel_analyst import LCELAnalyst
from logikon.schemas.results import AnalysisState, Artifact

MAX_LEN_ISSUE = 80
N_DRAFTS = 3
LABELS = "ABCDEFG"
QUESTIONS_EVAL = [
    "Which alternative captures best the text's overarching issue addressed?",
    "Which alternative is most clear and concise?",
    "Which alternative is most faithful to the text?",
]

# examples
# - NONE


def _strip_issue_tag(text: str) -> str:
    """Postprocessing function
    Strip issue tags from generated text.
    """
    text = text.strip("\n ")
    if text.startswith("<ISSUE>"):
        text = text[len("<ISSUE>") :].strip("\n ")
    if text.endswith("</ISSUE>"):
        text = text[: -len("</ISSUE>")].strip("\n ")
    if text[-1] not in [".", "!", "?"]:
        # split text at any of ".", "!", "?"
        splits = re.split(r"([.!?])", text)
        text = "".join(splits[:-1]) if len(splits) > 1 else text
    return text


class IssueBuilderLCEL(LCELAnalyst):
    """IssueBuilderLCEL

    This LCELAnalyst is responsible for summarizing the issue discussed in a text.
    """

    __pdescription__ = "Issue or decision problem addressed in the deliberation"
    __product__ = "issue"

    def _key_issue(self, prompt: str, completion: str) -> list[dict[str, Any]]:
        """Defines and executes LCEL chain for generating issue drafts."""

        prompt_template = ChatPromptTemplate.from_template(
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
            "Enclose your answer in \"<ISSUE>\" / \"</ISSUE>\" tags."  # noqa: Q003
        )
        regex = r"<ISSUE>[^\n]{1,%s}</ISSUE>" % MAX_LEN_ISSUE
        bnf = 'root  ::= "<ISSUE>" issue "</ISSUE>"\nissue ::= [^\n]+'
        stop = ["</ISSUE>"]
        gen_args = {
            "temperature": 0.5,
            "stop": stop,
            "bnf": bnf,
            "regex": regex,
        }

        # fmt: off
        chain = (
            prompt_template
            | self._model.bind(**gen_args).with_retry()
            | StrOutputParser()
            | RunnableLambda(_strip_issue_tag)
        )
        # fmt: on

        inputs = {
            "prompt": prompt,
            "completion": completion,
        }

        results = chain.batch(N_DRAFTS * [inputs])

        issue_drafts = [
            {
                "text": result,
                "label": LABELS[enum],
            }
            for enum, result in enumerate(results)
        ]
        return issue_drafts

    def _rate_issue_drafts(
        self, alternatives: list[dict[str, Any]], questions: list[str], prompt: str, completion: str
    ) -> str | None:
        """Rates and selects alternative issue drafts according to criteria (questions).

        Returns:
            str: label of best alternative
        """

        init_message = HumanMessagePromptTemplate.from_template(
            "Assignment: Rate different summarizations of a text's key issue.\n\n"
            "Before we start, let's study the text to-be-analysed carefully.\n\n"
            "<TEXT>\n"
            "{prompt}{completion}\n"
            "</TEXT>\n\n"
            "Consider the following alternatives, which attempt to summarize the central "
            "issue / basic decision discussed in the TEXT in a single sentence.\n\n"
            "<ALTERNATIVES>\n"
            "{formatted_alternatives}\n"
            "</ALTERNATIVES>\n\n"
            "I'll ask you to compare and evaluate these alternatives according to different "
            "criteria, which I'll put as a question each. In the end, I'll ask you aggregate your "
            "assessment. Understood?"
        )

        # Step 1 Dialogue

        prompt_template = ChatPromptTemplate.from_messages(
            [
                init_message,
                AIMessage(content="Understood. Can you please ask the first question?"),
                HumanMessagePromptTemplate.from_template(
                    "Q: {question}\n"
                    "(At this point, just answer each question with {formatted_labels}; "
                    "you'll be asked to explain your answers later.)"
                ),
            ]
        )

        labels = [alternative["label"] for alternative in alternatives]
        formatted_alternatives = "\n".join(
            f"({alternative['label']}) \"{alternative['text']}\"" for alternative in alternatives
        )
        formatted_labels = "/".join(labels)

        regex = "(" + "|".join(labels) + ")"
        bnf = "root ::= ({labels_bnf})".format(labels_bnf="|".join([f'"{label}"' for label in labels]))
        gen_args = {"temperature": 1.0, "regex": regex, "bnf": bnf}

        # fmt: off
        chain = (
            prompt_template
            | self._model.bind(**gen_args).with_retry()
            | StrOutputParser()
        )
        # fmt: on

        inputs1 = [
            {
                "prompt": prompt,
                "completion": completion,
                "formatted_alternatives": formatted_alternatives,
                "formatted_labels": formatted_labels,
                "question": question,
            }
            for question in questions
        ]

        results = chain.batch(inputs1)

        # Step 2 Dialogue

        messages: Sequence = [init_message, AIMessage(content="Understood. Let's start.")]
        for question, answer in zip(questions, results):
            messages = [*messages, HumanMessage(content=f"{question}"), AIMessage(content=f"{answer}")]
        messages = [
            *messages,
            HumanMessagePromptTemplate.from_template(
                "So, all in all and given the above assessments, the best summarization of the "
                "text's key issue is which alternative? (Answer with {formatted_labels}.)"
            ),
        ]
        prompt_template = ChatPromptTemplate.from_messages(messages)

        # fmt: off
        chain = (
            prompt_template
            | self._model.bind(**gen_args).with_retry()
            | StrOutputParser()
        )
        # fmt: on

        inputs2 = {
            "prompt": prompt,
            "completion": completion,
            "formatted_alternatives": formatted_alternatives,
            "formatted_labels": formatted_labels,
        }

        result = chain.invoke(inputs2)

        return result

    async def _analyze(self, analysis_state: AnalysisState):
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
