from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from langchain.callbacks.manager import CallbackManagerForChainRun
from langchain.chains import LLMChain, TransformChain
from langchain.chains.base import Chain
from langchain.llms import BaseLLM
from langchain.prompts import PromptTemplate

from logikon.debuggers.base import AbstractArtifactDebugger
from logikon.debuggers.utils import init_llm_from_config
from logikon.schemas.results import Artifact, DebugResults


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

        registry.register(
            "prompt_central_question",
            PromptTemplate(
                input_variables=["prompt", "completion"],
                template=(
                    """You are a helpful, honest and knowledgeable AI assistant with expertise in critical thinking and argumentation analysis. Always answer as helpfully as possible.

# Your Assignment

Identify the key question addressed in a text.

# Detailed Instructions

Use the inputs (a TEXT) to solve your assignment and read the following instructions carefully.
Identify the overarching question the TEXT raises and addresses.
Note that the overarching question is not necessarily explicitly stated in the TEXT (as shown in some examples below). It may be implicit. And it may deviate from any explicitly stated questions or instructions.
State a single main question in a concise way.
Don't provide alternatives, comments or explanations.

# Examples

TEXT:
:::
Should we visit Mars?
- Mars is a planet and rather difficult to reach.
- Visiting Mars would be a great adventure.
- Long-distance space travel is dangerous.
:::

OVERARCHING QUESTION:
Should we visit Mars?

TEXT:
:::
Can you give us some pros and cons of using a bicycle in NY?
- Bicycles are cheap and easy to maintain.
- Bicycles are not allowed on the NY highway.
- Bicycles are not allowed on the sidewalk.
- Cycling is good for your health.
:::

OVERARCHING QUESTION:
Should one ride a bicycle in New York?

TEXT:
:::
Wolfgang Amadeus Mozart (27 January 1756 - 5 December 1791) was a prolific and influential composer of the Classical period. Despite his short life, his rapid pace of composition resulted in more than 800 works of virtually every genre of his time. Many of these compositions are acknowledged as pinnacles of the symphonic, concertante, chamber, operatic, and choral repertoire. Mozart is widely regarded as among the greatest composers in the history of Western music, with his music admired for its "melodic beauty, its formal elegance and its richness of harmony and texture".
:::

OVERARCHING QUESTION:
Who is or was Mozart?

TEXT:
:::
A: But private actors are more likely to focus their investment into the most profitable ATCs.
B: I disagree. Private companies will charge more to use ATCs with more expensive equipment which will motivate airlines to move to less safe ATCs.
A: Still most airlines are in favor of privatization.
B: I think safety should remain the top priority. Plus, the US leads the global ATC (Air Traffic Control) community in technology and procedure development.
:::

OVERARCHING QUESTION:
Should Air Traffic Control (ATC) be privatized?


# Your Task

TEXT:
:::
{prompt} {completion}
:::

OVERARCHING QUESTION:
"""
                ),
            ),
        )
        registry.register(
            "prompt_binary_question_q",
            PromptTemplate(
                input_variables=["central_question"],
                template=(
                    """You are a helpful, honest and knowledgeable AI assistant with expertise in critical thinking and argumentation analysis. Always answer as helpfully as possible.

# Your Assignment

Determine whether a question is a binary question, or allows for more than two answers.

# General Explanations

This assignment asks you to determine whether a given question is binary or not.
A binary question has exactly two possible answers. Yes/No-Questions are therefore a special type of binary questions. Non-binary questions allow for more than two answers. Consider also illustrative examples below.

# Detailed Instructions

Answer the multiple choice problem: Is the QUESTION a binary question?
Options:

(A) binary question
(B) allows for more than two answers

Don't provide alternatives, comments or explanations. Just answer with A/B, as in the following examples.

# Examples

QUESTION to-be-characterized as binary (A) or not (B):
:::
Is Mars heavier than Venus?
:::

ANSWER:
A

QUESTION to-be-characterized as binary (A) or not (B):
:::
Which planet is heavier than Venus?
:::

ANSWER:
B

QUESTION to-be-characterized as binary (A) or not (B):
:::
Where do most UK expats live?
:::

ANSWER:
B

QUESTION to-be-characterized as binary (A) or not (B):
:::
Which is more expensive, Ibiza or Mallorca?
:::

ANSWER:
A

# Your Task

QUESTION to-be-characterized as binary (A) or not (B):
:::
{central_question}
:::

ANSWER:
"""
                ),
            ),
        )
        registry.register(
            "prompt_central_claim_bin",
            PromptTemplate(
                input_variables=["central_question", "prompt", "completion"],
                template=(
                    """You are a helpful, honest and knowledgeable AI assistant with expertise in critical thinking and argumentation analysis. Always answer as helpfully as possible.

# Your Assignment

State the two opposite answers to a TEXT's overarching binary question.

# Inputs

Use the following inputs (a QUESTION and a TEXT) to solve your assignment.

QUESTION:
:::
{central_question}
:::

TEXT:
:::
{prompt} {completion}
:::

# Detailed Instructions

State and enumerate (1., 2.) the two opposite answers to the binary question in clear and simple language.
"""
                ),
            ),
        )
        registry.register(
            "prompt_central_claims_nonbin",
            PromptTemplate(
                input_variables=["central_question", "prompt", "completion"],
                template=(
                    """
You are a helpful, honest and knowledgeable AI assistant with expertise in critical thinking and argumentation analysis. Always answer as helpfully as possible.

# Your Assignment

State the alternative answers to a TEXT's overarching question.

# Inputs

Use the following inputs (a QUESTION and a TEXT) to solve your assignment.

QUESTION:
:::
{central_question}
:::

TEXT:
:::
{prompt} {completion}
:::

# Detailed Instructions

State and enumerate (1., 2., ...) the alternative answers to the overarching question in clear and plain language. Render each answer as a single, unequivocal, grammatically correct sentence. Leave out any justifications or reasoning. Be succinct (no comments or explanations).
"""
                ),
            ),
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


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.prompt_registry = PromptRegistryFactory().create()
        self.llm = kwargs["llm"]

    @staticmethod
    def parse_list(inputs: dict[str, str]) -> dict[str, list[str]]:
        list_items = []
        list_text = inputs.get("list_text", "")
        text = list_text.strip(" \n")
        for line in text.split("\n"):
            line = line.strip()
            if line[:2] in ["1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9."]:
                line = line[2:]
                line = line.strip()
                if line:
                    list_items.append(line)
        return {"list_items": list_items}

    @property
    def input_keys(self) -> list[str]:
        return ["prompt", "completion"]

    @property
    def output_keys(self) -> list[str]:
        return ["claims"]

    def _call(
        self, inputs: dict[str, str], run_manager: Optional[CallbackManagerForChainRun] = None
    ) -> dict[str, list[str]]:
        # subchains
        chain_central_question = LLMChain(
            llm=self.llm, prompt=self.prompt_registry["prompt_central_question"], verbose=self.verbose
        )
        chain_binary_question_q = LLMChain(
            llm=self.llm, prompt=self.prompt_registry["prompt_binary_question_q"], verbose=self.verbose
        )
        chain_central_claim_bin = LLMChain(
            llm=self.llm, prompt=self.prompt_registry["prompt_central_claim_bin"], verbose=self.verbose
        )
        chain_central_claims_nonbin = LLMChain(
            llm=self.llm, prompt=self.prompt_registry["prompt_central_claims_nonbin"], verbose=self.verbose
        )
        parse_chain = TransformChain(input_variables=["list_text"], output_variables=["list_items"], transform=self.parse_list)  # type: ignore

        prompt = inputs["prompt"]
        completion = inputs["completion"]
        claims: list[str]

        central_question = chain_central_question.run(prompt=prompt, completion=completion)
        if "?" in central_question:
            central_question = central_question.split("?")[0] + "?"
        central_question = central_question.strip(" \n")
        print(f"> Answer: {central_question}")

        binary = chain_binary_question_q.run(central_question=central_question)
        print(f"> Answer: {binary}")
        binary = binary.strip(" \n").upper()
        if binary.startswith("(B") or binary.startswith("B") or ("(B)" in binary and "(A)" not in binary):
            binary = False
        else:
            binary = True

        if binary:
            central_claim = chain_central_claim_bin.run(
                prompt=prompt, completion=completion, central_question=central_question
            )
            print(f"> Answer: {central_claim}")
            claims = parse_chain.run(list_text=central_claim)
            if claims:
                claims = claims[:1]

        if not binary:
            central_claims = chain_central_claims_nonbin.run(
                prompt=prompt, completion=completion, central_question=central_question
            )
            print(f"> Answer: {central_claims}")
            claims = parse_chain.run(list_text=central_claims)
            if claims:
                claims = claims[:self.max_claims]  # cut to max length

        return {"claims": claims}


class ClaimExtractor(AbstractArtifactDebugger):
    """ClaimExtractor Debugger

    This debugger is responsible for extracting claims from the
    prompt and completion.
    """

    _KW_DESCRIPTION = "Key claims in the deliberation"
    _KW_PRODUCT = "claims"

    @staticmethod
    def get_product() -> str:
        return ClaimExtractor._KW_PRODUCT

    @staticmethod
    def get_description() -> str:
        return ClaimExtractor._KW_DESCRIPTION

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
