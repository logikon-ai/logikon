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
B: I disagee. Private companies will charge more to use ATCs with more expensive equipment which will motivate airlines to move to less safe ATCs.
A: Still most air lines are in favor of privatization.
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

State a text's central claim that answers its overarching question.

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
What is the key claim that answers the overarching QUESTION, and that is at issue, argued for, debated, or critically discussed in the TEXT?

- State the key claim discussed in the text above in a clear, short and very concise way.
- Concentrate on the main assertion and don't reproduce the text's reasoning.
- Make sure that the key claim answers the QUESTION.
- Note that the key claim may be implicit in the text.
- Provide a SINGLE grammatically correct sentence.
- Don't add alternatives, comments or explanations.

Reminder: The text's overarching question is: {central_question}

# Answer
The TEXT discusses the following answer to the overarching QUESTION:"""
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
Identify the alternative answers to an overarching question discussed in a text.

# Inputs
Use the following inputs (a TEXT and a QUESTION) to solve your assignment.

TEXT:
:::
{prompt}
{completion}
:::

QUESTION:
:::
{central_question}
:::

# Detailed Instructions
What are the rivaling answers to the overarching QUESTION that are discussed in the TEXT?

- State the key answers that directly answer the question in a clear, short concise way.
- Make sure that every single answer directly responds to the QUESTION.
- Concentrate on the alternative answers to the QUESTION and don't reproduce any claims or reasons advanced in the text.
- Phrase the alternative answers such that they are mutually exclusive.
- Render each answer as a SINGLE grammatically correct sentence.
- Don't add comments or explanations.
- Enumerate alternative answers (up to four, fewer are ok) consecutively -- beginning with 1. -- and start each answer with a new line.

Reminder: The text's overarching question is: {central_question}.

# Answer
The alternative answers of the TEXT are:"""
                ),
            ),
        )
        registry.register(
            "prompt_central_claims_add",
            PromptTemplate(
                input_variables=["central_question", "prompt", "completion", "central_claims"],
                template=(
                    """
You are a helpful, honest and knowledgeable AI assistant with expertise in critical thinking and argumentation analysis. Always answer as helpfully as possible.

# Your Assignment
Identify additional answers to an overarching question discussed in a text (if any).

# Inputs
Use the following inputs (a QUESTION, a TEXT, and central ANSWERS) to solve your assignment.

TEXT:
:::
{prompt}
{completion}
:::

QUESTION:
:::
{central_question}
:::

ANSWERS:
:::
{central_claims}
:::

# Detailed Instructions
Are there any additional direct answers to the overarching QUESTION which are discussed in the TEXT and not already listed under ANSWERS above?

- State any additional answers to the QUESTION above in a clear, short and very concise way.
- Make sure that every single new answer directly addresses the QUESTION.
- Phrase the answers such that they are mutually exclusive.
- Importantly, only provide additional answers which differ from the ANSWERS listed above.
- Don't add comments or explanations.
- Enumerate any additional answers (up to four, fewer are ok) consecutively -- beginning with 1. -- and start each answer with a new line.
- However, just write 'NONE' if the above ANSWERS contain all relevant rival answers to the QUESTION.

Reminder: The text's overarching question is: {central_question}.

# Answer
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

    # depth = 2

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
        chain_central_claims_add = LLMChain(
            llm=self.llm, prompt=self.prompt_registry["prompt_central_claims_add"], verbose=self.verbose
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
            if "." in central_claim:
                central_claim = central_claim.split(".")[0] + "."
            central_claim = central_claim.strip(" \n")
            print(f"> Answer: {central_claim}")
            claims = [central_claim]

        if not binary:
            central_claims = chain_central_claims_nonbin.run(
                prompt=prompt, completion=completion, central_question=central_question
            )
            print(f"> Answer: {central_claims}")
            claims = parse_chain.run(list_text=central_claims)
            if claims:
                while len(claims) < self.max_claims:
                    n = len(claims)
                    central_claims = chain_central_claims_add.run(
                        prompt=prompt,
                        completion=completion,
                        central_question=central_question,
                        central_claims="* " + ("\n* ".join(claims)),
                    )
                    print(f"> Answer: {central_claims}")
                    claims.extend(parse_chain.run(list_text=central_claims))
                    if len(claims) == n:
                        break

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
