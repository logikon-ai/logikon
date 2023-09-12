from __future__ import annotations
from typing import Dict, List, Any, Optional, Tuple
import os
import re
import uuid

from langchain.chains.base import Chain
from langchain.chains import LLMChain, TransformChain
from langchain.callbacks.base import BaseCallbackHandler
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate

from logikon.debuggers.base import AbstractDebugger
from logikon.schemas.results import DebugResults, Artifact

KWARGS_LLM_CREATIVE = dict(temperature=0.9)
KWARGS_LLM_FAITHFUL = dict(temperature=0.4)


class PromptRegistry(Dict):
    """
    A registry of prompts to be used in the deliberation process.
    """
    def __init__(self):
        super().__init__()

    def register(self, name, prompt: PromptTemplate):
        """
        Register a prompt to the registry.
        """
        self[name] = prompt


class PromptRegistryFactory:
    """
    Creates Prompt Registries
    """
    @staticmethod
    def create() -> PromptRegistry:
        registry = PromptRegistry()

        registry.register("prompt_central_question", PromptTemplate(
                input_variables=["prompt","completion"],
                template=(
                    "## TASK\n"
                    "Identify the key question adressed in the following TEXT.\n\n"
                    "## CONTEXT\n"
                    "{prompt}\n"
                    "{completion}\n\n"
                    "## INSTRUCTION\n"
                    "What is the key question the above text (CONTEXT) raises and addresses?\n"
                    "State a single main question in a concise way:\n"
                )
            )
        )
        registry.register("prompt_binary_question_q", PromptTemplate(
                input_variables=["central_question"],
                template=(
                    "## TASK\n"
                    "Determine whether a question (A) is a binary question or (B) allows for more than two answers.\n\n"
                    "## CONTEXT\n"
                    "The TEXT addresses the following question: {central_question}\n\n"
                    "## INSTRUCTION\n"
                    "Is the question a binary question (i.e., a question that can be answered with yes or no)?\n"
                    "(A) binary question\n"
                    "(B) allows for more than two answers\n"
                    "Write 'A' or 'B' in the following line (and nothing else):\n"
                )
            )
        )
        registry.register("prompt_central_claim_bin", PromptTemplate(
                input_variables=["central_question","prompt","completion"],
                template=(
                    "## TASK\n"
                    "Identify the key claim discussed in a text.\n\n"
                    "## CONTEXT\n"
                    "The following text addresses as central question: {central_question}\n\n"
                    "{prompt}\n"
                    "{completion}\n\n"
                    "## INSTRUCTION\n"
                    "What is the key claim that is argued for, debated, or critically discussed?\n"
                    "Hint: The key claim is an answer to the central question: {central_question}.\n"
                    "State the central claim (one gramatically correct sentence) discussed in the "
                    "texts above in a clear, short and very concise way. Concentrate on the main assertion "
                    "and leave out any reasoning.\n"
                    "The central claim discussed in the text is:\n"
                )
            )
        )
        registry.register("prompt_central_claims_nonbin", PromptTemplate(
                input_variables=["central_question","prompt","completion"],
                template=(
                    "## TASK\n"
                    "Identify the central rivaling claims discussed in a text.\n\n"
                    "## CONTEXT\n"
                    "The following text addresses as central question: {central_question}\n\n"
                    "{prompt}\n"
                    "{completion}\n\n"
                    "## INSTRUCTION\n"
                    "What are the key claims that are argued for, debated, or critically discussed?\n"
                    "Hint: The key claims are mutually exclusive amd direct answers to the central question: {central_question}.\n"
                    "State each central claim (one gramatically correct sentence) discussed in the "
                    "texts above in a clear, short and very concise way. Concentrate on the main assertions "
                    "and leave out any reasoning. "
                    "Enumerate key claims (up to 4, fewer are ok) consecutively -- beginning with 1. -- and start each argument with a new line.\n"
                    "The key claims, directly answering the central question, are:\n"
                )
            )
        )
        registry.register("prompt_central_claims_add", PromptTemplate(
                input_variables=["central_question","prompt","completion","central_claim"],
                template=(
                    "## TASK\n"
                    "Identify additional alternative answers discussed in a text.\n\n"
                    "## CONTEXT\n"
                    "{prompt}\n"
                    "{completion}\n\n"
                    "The above text addresses as central (non-binary) question: {central_question}\n"
                    "The key claims that represent alternative answers to the central question and which are argued for are: {central_claim}\n\n"
                    "## INSTRUCTION\n"
                    "Are there any additional direct answers to the central question which are discussed in the text and not listed above?\n"
                    "Hint: Additional key claims are direct answers to the central question: {central_question}.\n"
                    "Hint: Additional key claims are mutually exclusive and differ from the key claims listed above.\n"
                    "State each, if any, additional central claim (one gramatically correct sentence) discussed in the "
                    "texts above in a clear, short and very concise way. Concentrate on the main assertions "
                    "and leave out any reasoning. Don't repeat yourself. "
                    "Enumerate additional key claims (up to 4, fewer are ok) consecutively -- beginning with 1. -- and start each claim with a new line. However, just write 'NONE' if there are no additional key claims and the abpove list is exhaustive.\n"
                    "Additional key claims, directly answering the central question, are:\n"
                )
            )
        )

        return registry





class ArgumentMiningChain(Chain):

    n_reasons_zo = 3
    n_reasons_ho = 2
    max_words_claim = 25
    verbose = True
    llm:OpenAI = None
    llm_faithful:OpenAI = None
    prompt_registry:PromptRegistry = None

    #depth = 2

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.llm = OpenAI(model_name="text-davinci-003", **KWARGS_LLM_CREATIVE)
        self.llm_faithful = OpenAI(model_name="text-davinci-003", **KWARGS_LLM_FAITHFUL)

        self.prompt_registry = PromptRegistryFactory().create()


    @staticmethod
    def parse_list(inputs: dict) -> List[str]:
        list_items = []
        list_text = inputs.get("list_text")
        text = list_text.strip(" \n")
        for line in text.split("\n"):
            line = line.strip()
            if line[:2] in ["1.","2.","3.","4.","5.","6.","7.","8.","9."]:
                line = line[2:]
                line = line.strip()
                if line:
                    list_items.append(line)
        return {"list_items": list_items}


    @property
    def input_keys(self) -> List[str]:
        return ['prompt', 'completion']

    @property
    def output_keys(self) -> List[str]:
        return ['claims']

    def _call(self, inputs: Dict[str, str]) -> Dict[str, str]:


        nodelist = []
        edgelist = []

        # subchains

        chain_central_question = LLMChain(llm=self.llm, prompt=self.prompt_registry["prompt_central_question"], verbose=self.verbose)
        chain_binary_question_q = LLMChain(llm=self.llm, prompt=self.prompt_registry["prompt_binary_question_q"], verbose=self.verbose)
        chain_central_claim_bin = LLMChain(llm=self.llm, prompt=self.prompt_registry["prompt_central_claim_bin"], verbose=self.verbose)
        chain_central_claims_nonbin = LLMChain(llm=self.llm, prompt=self.prompt_registry["prompt_central_claims_nonbin"], verbose=self.verbose)
        chain_central_claims_add = LLMChain(llm=self.llm, prompt=self.prompt_registry["prompt_central_claims_add"], verbose=self.verbose)
        parse_chain = TransformChain(input_variables=["list_text"], output_variables=["list_items"], transform=self.parse_list)


        prompt = inputs['prompt']
        completion = inputs['completion']

        central_question = chain_central_question.run(prompt=prompt, completion=completion)
        if "?" in central_question:
            central_question = central_question.split("?")[0]+"?"
        central_question = central_question.strip(" \n")
        print(f"> Answer: {central_question}")

        binary = chain_binary_question_q.run(central_question=central_question)
        binary = binary.strip(" \n()")
        binary = binary.upper()[0]=="A"
        print(f"> Answer: {binary}")

        if binary:
            central_claim = chain_central_claim_bin.run(prompt=prompt, completion=completion, central_question=central_question)
            if "." in central_claim:
                central_claim = central_claim.split(".")[0]+"."
            central_claim = central_claim.strip(" \n")
            print(f"> Answer: {central_claim}")
            claims = [central_claim]

        if not binary:
            central_claims = chain_central_claims_nonbin.run(prompt=prompt, completion=completion, central_question=central_question)
            claims = parse_chain.run(list_text=central_claims)
            if claims:
                
            print(f"> Answer: {central_claims}")
            claims = central_claims            

        argument_map = dict(
            nodelist = nodelist,
            edgelist = edgelist,
        )


        return {"argument_map": argument_map, "text_content_items": text_content_items}        
    



class ClaimExtractor(AbstractDebugger):
    """ClaimExtractor Debugger
    
    This debugger is responsible for extracting claims from the
    prompt and completion.    
    """
    
    _KW_DESCRIPTION = "Key claims in the deliberation"
    _KW_PRODUCT = "claims"


    @classmethod
    def get_product(cls) -> str:
        return cls._KW_PRODUCT


    def _debug(self, prompt: str = "", completion: str = "", debug_results: Optional[DebugResults] = None):
        """Debug completion."""
        assert debug_results is not None
        # Dummy

        llmchain = ArgumentMiningChain(max_words_claim=25)


        claims = Artifact(
            id=self._KW_PRODUCT,
            description=self._KW_DESCRIPTION,
            data=["claim1", "claim2"],
        )

        debug_results.artifacts.append(claims)


