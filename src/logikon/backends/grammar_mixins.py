from __future__ import annotations

import copy
import logging
from abc import abstractmethod
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import Runnable


class AbstractGrammarMixin(BaseChatModel):
    """AbstractGrammarMixin

    Defines how to bind grammars to gen_args through bind() in BaseChatModels.
    """

    @abstractmethod
    def bind_bnf(self, bnf: Any, gen_args: dict) -> dict:
        pass

    @abstractmethod
    def bind_json_schema(self, json_schema: Any, gen_args: dict) -> dict:
        pass

    @abstractmethod
    def bind_regex(self, regex: Any, gen_args: dict) -> dict:
        pass

    def bind(self, **kwargs: Any) -> Runnable:

        if not any(k in kwargs for k in ["bnf", "json_schema", "regex"]):
            return super().bind(**kwargs)

        gen_args = copy.deepcopy(kwargs)
        bnf = gen_args.pop("bnf", None)
        json_schema = gen_args.pop("json_schema", None)
        regex = gen_args.pop("regex", None)

        grammar_bound: bool = False
        if bnf is not None:
            try:
                gen_args = self.bind_bnf(bnf, gen_args)
                grammar_bound = True
            except NotImplementedError:
                pass
        if not grammar_bound and regex is not None:
            try:
                gen_args = self.bind_regex(regex, gen_args)
                grammar_bound = True
            except NotImplementedError:
                pass
        if not grammar_bound and json_schema is not None:
            try:
                gen_args = self.bind_json_schema(json_schema, gen_args)
                grammar_bound = True
            except NotImplementedError:
                pass
        if not grammar_bound:
            msg = (
                f"None of the provided guidance {[bnf, regex, json_schema]} "
                f"is supported for model {self} of type {self.__class__}."
                f"Proceeding without guidance."
            )
            logging.getLogger(__name__).warning(msg)

        return super().bind(**gen_args)


class VLLMGrammarMixin(AbstractGrammarMixin):
    """VLLMGrammarMixin

    Mixin for VLLM Chat models that use Openai VLLM Endpoints for generating text.
    """

    def bind_bnf(self, bnf: Any, gen_args: dict) -> dict:  # noqa: ARG002
        msg = "VLLM does not support BNF."
        raise NotImplementedError(msg)

    def bind_json_schema(self, json_schema: Any, gen_args: dict) -> dict:
        if "extra_body" not in gen_args:
            gen_args["extra_body"] = {}
        gen_args["extra_body"]["guided_json"] = json_schema
        return gen_args

    def bind_regex(self, regex: Any, gen_args: dict) -> dict:
        if "extra_body" not in gen_args:
            gen_args["extra_body"] = {}
        gen_args["extra_body"]["guided_regex"] = regex
        return gen_args


class FireworksGrammarMixin(AbstractGrammarMixin):
    """FireworksGrammarMixin

    Mixin for Fireworks Chat models that use Openai Fireworks Endpoints for generating text.
    """

    def bind_bnf(self, bnf: Any, gen_args: dict) -> dict:
        gen_args["response_format"] = {"type": "grammar", "grammar": bnf}
        return gen_args

    def bind_json_schema(self, json_schema: Any, gen_args: dict) -> dict:
        gen_args["response_format"] = {"type": "json_object", "schema": json_schema}
        return gen_args

    def bind_regex(self, regex: Any, gen_args: dict) -> dict:  # noqa: ARG002
        msg = "Fireworks does not support BNF."
        raise NotImplementedError(msg)


class HFChatGrammarMixin(AbstractGrammarMixin):
    """HFChatGrammarMixin

    Mixin for HF Chat models that use Hugging Face Endpoints for generating text.
    """

    def bind_bnf(self, bnf: Any, gen_args: dict) -> dict:  # noqa: ARG002
        msg = "HF TGI does not support BNF."
        raise NotImplementedError(msg)

    def bind_json_schema(self, json_schema: Any, gen_args: dict) -> dict:
        grammar = {"type": "json", "value": json_schema}
        gen_args["grammar"] = grammar
        return gen_args

    def bind_regex(self, regex: Any, gen_args: dict) -> dict:
        grammar = {"type": "regex", "value": regex}
        gen_args["grammar"] = grammar
        return gen_args
