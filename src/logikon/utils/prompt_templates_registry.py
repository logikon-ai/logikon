"""Prompt / chat templates used in LMQL queries."""

from __future__ import annotations

import logging

import pydantic


class PromptTemplate(pydantic.BaseModel):
    """PromptTemplate

    Prompt template for LMQL queries.

    """

    sys_start: str
    sys_end: str
    user_start: str
    user_end: str
    ass_start: str
    ass_end: str

    @classmethod
    def from_dict(cls, d: dict) -> PromptTemplate:
        return cls(**d)

    def to_dict(self) -> dict:
        return self.dict()

    def __getitem__(self, key: str) -> str:
        return getattr(self, key)


_DEFAULT_KEY = "llama"

_PROMPT_TEMPLATE_REGISTRY = {
    "llama": PromptTemplate(
        sys_start="### System\n",
        sys_end="",
        user_start="### User\n",
        user_end="",
        ass_start="### Assistant\n",
        ass_end="",
    ),
    "mistral_instruct": PromptTemplate(
        sys_start="<s>",
        sys_end="",
        user_start="[INST]",
        user_end="[/INST]",
        ass_start="",
        ass_end="",
    ),
    "chatml": PromptTemplate(
        sys_start="<|im_start|>system",
        sys_end="<|im_end|>",
        user_start="<|im_start|>user",
        user_end="<|im_end|>",
        ass_start="<|im_start|>assistant",
        ass_end="<|im_end|>",
    ),
}


def get_prompt_template(tmpl_key: str | None = None) -> PromptTemplate:
    """Returns prompt template to use with lmql queries"""
    if tmpl_key is None:
        tmpl_key = _DEFAULT_KEY
    if tmpl_key not in _PROMPT_TEMPLATE_REGISTRY:
        logging.getLogger("prompt_templates_registry").warning(
            f"Invalid prompt template key: {tmpl_key}, using default template {_DEFAULT_KEY}."
        )
        tmpl_key = _DEFAULT_KEY

    return _PROMPT_TEMPLATE_REGISTRY[tmpl_key]
