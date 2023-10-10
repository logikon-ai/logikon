# issue_builder_ol.py

from __future__ import annotations
from typing import List, Dict

import functools as ft

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




class ProsConsBuilderLMQL(LMQLDebugger):
    """ProsConsBuilderLMQL

    This LMQLDebugger is responsible for reconstructing a pros and cons list for a given issue.
    """

    _KW_DESCRIPTION = "Pros and cons list with multiple root claims"
    _KW_PRODUCT = "proscons"
    _KW_REQUIREMENTS = ["issue"]


    @staticmethod
    def get_product() -> str:
        return ProsConsBuilderLMQL._KW_PRODUCT

    @staticmethod
    def get_requirements() -> list[str]:
        return ProsConsBuilderLMQL._KW_REQUIREMENTS

    @staticmethod
    def get_description() -> str:
        return ProsConsBuilderLMQL._KW_DESCRIPTION

    def doublecheck(self, pros_and_cons: List[Dict], reasons: List[Dict], issue: str) -> List[Dict]:
        """Checks and revises a pros & cons list

        Args:
            pros_and_cons (List[Dict]): the pros and cons list to be checked and revised
            issue (str): the overarching issue addressed by the pros and cons

        Returns:
            List[Dict]: the revised pros and cons list

        For each pro (con) reason *r* targeting root claim *c*:

        - Checks if *r* supports (attacks) another root claim *c'* more strongly
        - Revises map accordingly

        """
        pass


    def _debug(self, debug_state: DebugState):
        """Extract pros and cons of text (prompt/completion)."""

        prompt, completion = debug_state.get_prompt_completion()
        issue = next(a.data for a in debug_state.artifacts if a.id == "issue")

        if prompt is None or completion is None:
            raise ValueError(f"Prompt or completion is None. {self.__class__} requires both prompt and completion to debug.")

        # mine reasons
        reasons = reason_mining(prompt=prompt, completion=completion, issue=issue, model=self._model)
        reasons = reasons[0]

        # build pros and cons list
        pros_and_cons = build_pros_and_cons(reasons=reasons, issue=issue, model=self._model)
        # TODO: consider drafting alternative pros&cons lists and choosing best
        pros_and_cons = pros_and_cons[0]

        # double-check and revise
        pros_and_cons = self.doublecheck(pros_and_cons, reasons, issue)

        if pros_and_cons is None:
            self.logger.warning("Failed to build pros and cons list (pros_and_cons is None).")

        artifact = Artifact(
            id=self._KW_PRODUCT,
            description=self._KW_DESCRIPTION,
            data=issue,
        )

        debug_state.artifacts.append(artifact)
