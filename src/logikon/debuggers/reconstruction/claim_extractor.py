from __future__ import annotations
from typing import Dict, List, Any, Optional, Tuple


from langchain.chains.base import Chain
from langchain.chains import LLMChain, TransformChain
from langchain.llms import BaseLLM
from langchain.prompts import PromptTemplate

from logikon.debuggers.base import AbstractDebugger
from logikon.schemas.results import DebugResults, Artifact
from logikon.debuggers.utils import init_llm_from_config


KWARGS_LLM_FAITHFUL = dict(temperature=0.7, max_tokens=256)


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
"""
You are a helpful, honest and knowledgable AI assisstant with expertise in critical thinking and argumentation analysis. Always answer as helpfully as possible.

# Your Assignment
Identify the key question adressed in a text.

# Inputs
Use the following inputs (a TEXT) to solve your assignment.

TEXT:
:::
{prompt}
{completion}
:::

# Detailed Instructions
What is the overarching question the above TERXT raises and addresses?
State a single main question in a concise way.
Don't provide alternatives, comments or explanations.

# Answer
The text's overarching question is:"""
                )
            )
        )
        registry.register("prompt_binary_question_q", PromptTemplate(
                input_variables=["central_question"],
                template=(
"""
You are a helpful, honest and knowledgable AI assisstant with expertise in critical thinking and argumentation analysis. Always answer as helpfully as possible.

# Your Assignment
Determine whether a question is a binary question, or allows for more than two answers.

# Inputs
Use the following inputs (a QUESTION) to solve your assignment.

QUESTION:
:::
{central_question}
:::

# Detailed Instructions
Answer the following multiple choice answer:
Is the question a binary question (i.e., a question that can be answered with yes or no)? Options:
(A) binary question
(B) allows for more than two answers

Don't provide alternatives, comments or explanations. Just answer with "My answer: (A/B)".

# Answer
My answer:"""
                )
            )
        )
        registry.register("prompt_central_claim_bin", PromptTemplate(
                input_variables=["central_question","prompt","completion"],
                template=(
"""
You are a helpful, honest and knowledgable AI assisstant with expertise in critical thinking and argumentation analysis. Always answer as helpfully as possible.

# Your Assignment
Summarize a text's answer to an overarching question.

# Inputs
Use the following inputs (a QUESTION and a TEXT) to solve your assignment.

QUESTION:
:::
{central_question}
:::

TEXT:
:::
{prompt}
{completion}
:::

# Detailed Instructions
What is the key claim that answers the overarching QUESTION, and that is at issue, argued for, debated, or critically discussed in the TEXT?

- State the key claim discussed in the text above in a clear, short and very concise way.
- Concentrate on the main assertion and don't reproduce the text's reasoning.
- Make sure that the key claim answers the QUESTION.
- Provide a SINGLE gramatically correct sentence.
- Don't add alternatives, comments or explanations.

Reminder: The text's overarching question is: {central_question}.

# Answer
The key claim of the TEXT is:"""
                )
            )
        )
        registry.register("prompt_central_claims_nonbin", PromptTemplate(
                input_variables=["central_question","prompt","completion"],
                template=(
"""
You are a helpful, honest and knowledgable AI assisstant with expertise in critical thinking and argumentation analysis. Always answer as helpfully as possible.

# Your Assignment
Identify the alternative answers to an overarching question discussed in a text.

# Inputs
Use the following inputs (a QUESTION and a TEXT) to solve your assignment.

QUESTION:
:::
{central_question}
:::

TEXT:
:::
{prompt}
{completion}
:::

# Detailed Instructions
What are the rivaling key claim that answer the overarching QUESTION, and that are at issue, argued for, debated, or critically discussed in the TEXT?

- State the key claims discussed in the text above in a clear, short and very concise way.
- Concentrate on the main assertions and don't reproduce the text's reasoning.
- Make sure that every single key claim is an answer to the QUESTION.
- Phrase the key claims such that they are mutually exclusive.
- Render each key claim as a SINGLE gramatically correct sentence.
- Don't add comments or explanations.
- Enumerate key claims (up to four, fewer are ok) consecutively -- beginning with 1. -- and start each claim with a new line.

Reminder: The text's overarching question is: {central_question}.

# Answer
The key claims of the TEXT are:"""

                )
            )
        )
        registry.register("prompt_central_claims_add", PromptTemplate(
                input_variables=["central_question","prompt","completion","central_claims"],
                template=(
"""
You are a helpful, honest and knowledgable AI assisstant with expertise in critical thinking and argumentation analysis. Always answer as helpfully as possible.

# Your Assignment
Identify additional answers to an overarching question discussed in a text (if any).

# Inputs
Use the following inputs (a QUESTION, a TEXT, and central CLAIMS) to solve your assignment.

QUESTION:
:::
{central_question}
:::

TEXT:
:::
{prompt}
{completion}
:::

CLAIMS:
:::
{central_claims}
:::

# Detailed Instructions
Are there any additional direct answers to the overarching QUESTION which are discussed in the TEXT and not listed under CLAIMS above?

- State any additional key claims discussed in the text above in a clear, short and very concise way.
- Concentrate on the main assertions and don't reproduce the text's reasoning.
- Make sure that every single key claim is an answer to the QUESTION.
- Phrase the key claims such that they are mutually exclusive.
- Importantly, only provide additional key claims differ from the key CLAIMS listed above.
- Render each additional key claim as a SINGLE gramatically correct sentence.
- Don't add comments or explanations.
- Enumerate any additional key claims (up to four, fewer are ok) consecutively -- beginning with 1. -- and start each claim with a new line.
- However, just write 'NONE' if there are no additional answers to the QUESTION and the above list of CLAIMS is exhaustive.

Reminder: The text's overarching question is: {central_question}.

# Answer
"""
                )
            )
        )

        return registry





class ClaimExtractionChain(Chain):

    n_reasons_zo = 3
    max_claims = 10
    n_reasons_ho = 2
    max_words_claim = 25
    verbose = True
    prompt_registry: PromptRegistry = PromptRegistry()
    llm: BaseLLM

    #depth = 2

    def __init__(self, **kwargs):
        super().__init__(**kwargs)        
        self.prompt_registry = PromptRegistryFactory().create()
        self.llm = kwargs["llm"]

    @staticmethod
    def parse_list(inputs: dict) -> Dict[str, List[str]]:
        list_items = []
        list_text = inputs.get("list_text", "")
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

    def _call(self, inputs: Dict[str, str]) -> Dict[str, List[str]]:

        # subchains
        chain_central_question = LLMChain(llm=self.llm, prompt=self.prompt_registry["prompt_central_question"], verbose=self.verbose)
        chain_binary_question_q = LLMChain(llm=self.llm, prompt=self.prompt_registry["prompt_binary_question_q"], verbose=self.verbose)
        chain_central_claim_bin = LLMChain(llm=self.llm, prompt=self.prompt_registry["prompt_central_claim_bin"], verbose=self.verbose)
        chain_central_claims_nonbin = LLMChain(llm=self.llm, prompt=self.prompt_registry["prompt_central_claims_nonbin"], verbose=self.verbose)
        chain_central_claims_add = LLMChain(llm=self.llm, prompt=self.prompt_registry["prompt_central_claims_add"], verbose=self.verbose)
        parse_chain = TransformChain(input_variables=["list_text"], output_variables=["list_items"], transform=self.parse_list)


        prompt = inputs['prompt']
        completion = inputs['completion']
        claims: List[str]

        central_question = chain_central_question.run(prompt=prompt, completion=completion)
        if "?" in central_question:
            central_question = central_question.split("?")[0]+"?"
        central_question = central_question.strip(" \n")
        print(f"> Answer: {central_question}")

        binary = chain_binary_question_q.run(central_question=central_question)
        print(f"> Answer: {binary}")
        binary = binary.strip(" \n").upper()
        if (
            binary.startswith("(B") or
            binary.startswith("B") or
            ("(B)" in binary and not "(A)" in binary)
        ):
            binary = False
        else:
            binary = True

        if binary:
            central_claim = chain_central_claim_bin.run(prompt=prompt, completion=completion, central_question=central_question)
            if "." in central_claim:
                central_claim = central_claim.split(".")[0]+"."
            central_claim = central_claim.strip(" \n")
            print(f"> Answer: {central_claim}")
            claims = [central_claim]

        if not binary:
            central_claims = chain_central_claims_nonbin.run(prompt=prompt, completion=completion, central_question=central_question)
            print(f"> Answer: {central_claims}")
            claims = parse_chain.run(list_text=central_claims)
            if claims:
                while len(claims) < self.max_claims:
                    n = len(claims)
                    central_claims = chain_central_claims_add.run(
                        prompt=prompt,
                        completion=completion,
                        central_question=central_question,
                        central_claims="* " + ("\n* ".join(claims))
                    )
                    print(f"> Answer: {central_claims}")
                    claims.extend(parse_chain.run(list_text=central_claims))
                    if len(claims) == n:
                        break

        return {"claims": claims}
    



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
        """Extract central claims tha address and answer key question of trace."""

        assert debug_results is not None

        llm = init_llm_from_config(self._debug_config)
        generation_kwargs = self._debug_config.generation_kwargs
        llmchain = ClaimExtractionChain(llm=llm, generation_kwargs=generation_kwargs, max_words_claim=25)
        claims = llmchain.run(prompt=prompt, completion=completion)

        artifact = Artifact(
            id=self._KW_PRODUCT,
            description=self._KW_DESCRIPTION,
            data=claims,
        )

        debug_results.artifacts.append(artifact)
