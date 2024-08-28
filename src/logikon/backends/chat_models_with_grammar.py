from __future__ import annotations

import copy
import logging
import math
from abc import abstractmethod
from enum import Enum
from typing import Any, Dict

import requests  # type: ignore
from langchain_community.chat_models.huggingface import ChatHuggingFace
from langchain_community.llms.huggingface_endpoint import HuggingFaceEndpoint
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.utils import (
    get_from_dict_or_env,
    pre_init,
)
from langchain_openai import ChatOpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)

from logikon.backends.grammar_mixins import FireworksGrammarMixin, HFChatGrammarMixin, VLLMGrammarMixin

HF_ENDPOINT_TIMEOUT = 10

# TODO
# prepend "(" to labels in all get_labelprobs methods


class LogitsModel(BaseChatModel):
    @abstractmethod
    async def get_labelprobs(
        self, messages: list[BaseMessage], labels: list[str], top_logprobs: int
    ) -> dict[str, float]:
        pass


class LazyHuggingFaceEndpoint(HuggingFaceEndpoint):
    """LazyHuggingFaceEndpoint"""

    # We're using a lazy endpoint to avoid logging in with hf_token,
    # which might in fact be a hf_oauth token that does only permit inference,
    # not looging in.

    @pre_init
    def validate_environment(cls, values: Dict) -> Dict:  # noqa: UP006, N805
        """Validate that package is installed and that the API token is valid."""
        try:
            from huggingface_hub import AsyncInferenceClient, InferenceClient  # type: ignore

        except ImportError:
            msg = (
                "Could not import huggingface_hub python package. "
                "Please install it with `pip install huggingface_hub`."
            )
            raise ImportError(msg)  # noqa: B904

        huggingfacehub_api_token = get_from_dict_or_env(values, "huggingfacehub_api_token", "HUGGINGFACEHUB_API_TOKEN")

        values["client"] = InferenceClient(
            model=values["model"],
            timeout=values["timeout"],
            token=huggingfacehub_api_token,
            **values["server_kwargs"],
        )
        values["async_client"] = AsyncInferenceClient(
            model=values["model"],
            timeout=values["timeout"],
            token=huggingfacehub_api_token,
            **values["server_kwargs"],
        )

        return values


class LLMBackends(Enum):
    """LLMBackends

    Enum for LLMBackends.
    """

    VLLM = "VLLM"
    HFChat = "HFChat"
    Fireworks = "Fireworks"


class ChatVLLMWithGrammar(VLLMGrammarMixin, ChatOpenAI, LogitsModel):
    """ChatVLLMWithGrammar

    Chat model that uses Openai VLLM Endpoints for generating text with grammar support.
    """

    def _logits_to_labelprobs(self, labels: list[str], logprobs: dict[str, Any]) -> dict[str, float]:
        """Converts vllm/openai logits to labelprobs"""
        labels_logprobs = {
            token: logit for token, logit in logprobs.items() if any(f" {label}" == token for label in labels)
        }
        # if no label in top logprobs, return uniform distribution
        if not labels_logprobs:
            msg = f"No label from [{labels}] in top logprobs: {logprobs}. Returning uniform distribution."
            logging.getLogger(__name__).warning(msg)
            return {label: 1 / len(labels) for label in labels}

        labels_exps = {k: math.exp(v) for k, v in labels_logprobs.items()}
        labels_probs = {k: v / sum(labels_exps.values()) for k, v in labels_exps.items()}
        probs = {label: labels_probs.get(f" {label}", 0) for label in labels}
        return probs

    async def get_labelprobs(
        self, messages: list[BaseMessage], labels: list[str], top_logprobs: int
    ) -> dict[str, float]:
        # create new model interface for generating logprobs
        logits_model: BaseChatModel = ChatOpenAI(
            model=self.model_name,
            openai_api_key=self.openai_api_key,  # type: ignore
            openai_api_base=self.openai_api_base,  # type: ignore
            max_tokens=1,
            temperature=0,
            model_kwargs={"logprobs": True, "top_logprobs": top_logprobs},
        )

        # see https://github.com/langchain-ai/langchain/issues/17101
        gen_result = await logits_model.with_retry().agenerate([messages])  # type: ignore
        gen_result_d = gen_result.dict()

        try:
            logprobs = gen_result_d["generations"][0][0]["generation_info"]["logprobs"]["top_logprobs"][0]
        except Exception as err:
            msg = f"Failed to extract logprobs from generation result: {gen_result_d}"
            raise ValueError(msg) from err

        probs = self._logits_to_labelprobs(labels, logprobs)

        return probs


class ChatFireworksWithGrammar(FireworksGrammarMixin, ChatOpenAI, LogitsModel):
    """ChatVLLMWithGrammar

    Chat model that uses Openai-compatible Fireworks Endpoints for generating text with grammar support.
    """

    def _logits_to_labelprobs(self, labels: list[str], logprobs: list[dict[str, Any]]) -> dict[str, float]:
        """Converts fireworks/openai logits to labelprobs"""
        logprobs = copy.deepcopy(logprobs)

        # helper function
        def _match_token_to_label(token_: str, labels_: list[str]) -> str | None:
            matched = next((label for label in labels_ if label == token_), None)
            if matched is None:
                matched = next((label for label in labels_ if f"({label}" == token_), None)
            if matched is None:
                matched = next((label for label in labels_ if f" {label}" == token_), None)
            return matched

        for record in logprobs:
            record["matched_label"] = _match_token_to_label(record["token"], labels)
        logprobs = [record for record in logprobs if record["matched_label"] is not None]

        labels_logprobs = {
            label: next(record["logprob"] for record in logprobs if record["matched_label"] == label)
            for label in labels
            if any(record["matched_label"] == label for record in logprobs)
        }

        # if no label in top logprobs, return uniform distribution
        if not labels_logprobs:
            msg = f"No label from [{labels}] in top logprobs: {logprobs}. Returning uniform distribution."
            logging.getLogger(__name__).warning(msg)
            return {label: 1 / len(labels) for label in labels}

        labels_exps = {k: math.exp(v) for k, v in labels_logprobs.items()}
        labels_probs = {k: v / sum(labels_exps.values()) for k, v in labels_exps.items()}
        probs = {label: labels_probs.get(label, 0) for label in labels}
        return probs

    async def get_labelprobs(
        self, messages: list[BaseMessage], labels: list[str], top_logprobs: int  # noqa: ARG002
    ) -> dict[str, float]:
        """Get label probabilities for the given messages and labels

        We're forcing model to generate answer with opening bracket. Experiments suggest that,
        without bracket, LLMs are biased towards generating "A"-label, as in "A: Yes" or "A: No".
        """

        if not all(bool(label) for label in labels):
            msg = f"Labels must be non-empty strings: {labels}"
            raise ValueError(msg)

        mc_bnf = ("root      ::= choices\nchoices   ::= ({label_choice})").format(
            label_choice="|".join([f'"({label}"' for label in labels])
        )

        @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
        async def logits_with_backoff(**kwargs):
            result = await self.bind(**kwargs).ainvoke(messages)
            return result.response_metadata["logprobs"]["content"][-1]["top_logprobs"]

        try:
            logprobs = await logits_with_backoff(
                max_tokens=2, logprobs=True, top_logprobs=5, response_format={"type": "grammar", "grammar": mc_bnf}
            )
        except Exception as err:
            msg = f"Failed to generate logprobs (Error: {err}). Returning uniform distribution."
            raise ValueError(msg) from err

        probs = self._logits_to_labelprobs(labels, logprobs)

        return probs


class ChatHFWithGrammar(HFChatGrammarMixin, ChatHuggingFace, LogitsModel):
    """ChatHFWithGrammar

    Chat model that uses Hugging Face Endpoints for generating text with grammar support.
    """

    def __init__(self, **kwargs: Any):
        BaseChatModel.__init__(self, **kwargs)

        from transformers import AutoTokenizer  # type: ignore

        # resolve model_id if not provided
        # (resolving model id will not work with HF oauth tokens)
        if not self.model_id:
            self._resolve_model_id()

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id) if self.tokenizer is None else self.tokenizer

    def _logits_to_labelprobs(self, labels: list[str], logits: list[dict[str, Any]]) -> dict[str, float]:

        labels_logprobs = {
            label: next(lg["logprob"] for lg in logits if lg["text"] == label)
            for label in labels
            if label in [lg["text"] for lg in logits]
        }

        # if no label in top logprobs, return uniform distribution
        if not labels_logprobs:
            msg = f"No label from [{labels}] in top logprobs: {logits}. Returning uniform distribution."
            logging.getLogger(__name__).warning(msg)
            return {label: 1 / len(labels) for label in labels}

        labels_exps = {k: math.exp(v) for k, v in labels_logprobs.items()}
        labels_probs = {k: v / sum(labels_exps.values()) for k, v in labels_exps.items()}
        probs = {label: labels_probs.get(label, 0) for label in labels}
        return probs

    async def get_labelprobs(
        self, messages: list[BaseMessage], labels: list[str], top_logprobs: int  # noqa: ARG002
    ) -> dict[str, float]:

        prompt = self._to_chat_prompt(messages)
        regex = "(" + "|".join(labels) + ")"

        data = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 1,
                "grammar": {"type": "regex", "value": regex},
                "details": True,
                "top_n_tokens": 5,
            },
        }

        headers = {
            "Authorization": f"Bearer {self.llm.huggingfacehub_api_token}",  # type: ignore
            "Content-Type": "application/json",
        }

        @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
        def logits_with_backoff(url, **kwargs):
            response = requests.post(url, **kwargs)  # noqa: S113
            return response.json()[0]["details"]["top_tokens"][0]

        logits = None
        try:
            logits = logits_with_backoff(
                self.llm.endpoint_url,  # type: ignore
                headers=headers,
                json=data,
                timeout=HF_ENDPOINT_TIMEOUT,
            )
        except Exception as err:
            msg = f"No logits returned (Error: {err}). Returning uniform distribution."
            logging.getLogger(__name__).error(msg)

        if logits:
            probs = self._logits_to_labelprobs(labels, logits)
        else:
            probs = {label: 1 / len(labels) for label in labels}

        return probs


def _load_hf_tokenizer(model_id: str, api_key: str):

    from transformers import AutoTokenizer  # type: ignore

    tokenizer = AutoTokenizer.from_pretrained(model_id, token=api_key)
    return tokenizer


def create_logits_model(
    model_id: str, inference_server_url: str, api_key: str, llm_backend: str | LLMBackends, **model_init_kwargs
) -> LogitsModel:

    if isinstance(llm_backend, str):
        llm_backend = LLMBackends(llm_backend)

    logits_model: LogitsModel

    if llm_backend == LLMBackends.VLLM:
        logits_model = ChatVLLMWithGrammar(
            model=model_id,
            openai_api_base=inference_server_url,  # type: ignore
            openai_api_key=api_key,  # type: ignore
            **model_init_kwargs,
        )
    elif llm_backend == LLMBackends.Fireworks:
        logits_model = ChatFireworksWithGrammar(
            model=model_id,  # e.g., "accounts/fireworks/models/llama-v2-7b-chat"
            openai_api_base=inference_server_url,  # type: ignore
            openai_api_key=api_key,  # type: ignore
            **model_init_kwargs,
        )
    elif llm_backend == LLMBackends.HFChat:
        llm = LazyHuggingFaceEndpoint(
            endpoint_url=inference_server_url,
            task="text-generation",
            huggingfacehub_api_token=api_key,
            **model_init_kwargs,
        )
        tokenizer = _load_hf_tokenizer(model_id, api_key=api_key)
        logits_model = ChatHFWithGrammar(llm=llm, model_id=model_id, tokenizer=tokenizer)
    else:
        msg = f"Unsupported LLM backend: {llm_backend}"
        raise ValueError(msg)

    logging.getLogger(__name__).info(f"Created logits model: {logits_model}")

    return logits_model
