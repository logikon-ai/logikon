from __future__ import annotations

import copy
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

from langchain.callbacks.manager import CallbackManagerForChainRun
from langchain.chains import LLMChain, TransformChain
from langchain.chains.base import Chain
from langchain.prompts import PromptTemplate
from langchain.llms import BaseLLM
from langchain.llms import (
    OpenAI,
)

from logikon.debuggers.base import AbstractArtifactDebugger
from logikon.debuggers.utils import init_llm_from_config
from logikon.schemas.argument_mapping import AnnotationSpan, ArgMapEdge, ArgMapNode, InformalArgMap
from logikon.schemas.results import Artifact, DebugResults


class PromptRegistry(Dict):
    """
    A registry of prompts to be used in building an informal argmap.
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
            "prompt_q_equivalent",
            PromptTemplate(
                input_variables=["reason1", "reason2"],
                template=(
                    """You are a helpful, honest and knowledgeable AI assistant with expertise in critical thinking and argumentation analysis. Always answer as helpfully as possible.

                    Consider the following arguments:

<Argument-1>
{reason1}
</Argument-1>
<Argument-2>
{reason2}
</Argument-2>

Are these two arguments making roughly the same point?

Answer with Yes/No, first. Then, give a concise explanation of your answer (one sentence). 
"""
                ),
            ),
        )
        registry.register(
            "prompt_q_supports",
            PromptTemplate(
                input_variables=["premise", "hypothesis"],
                template=(
                    """You are a helpful, honest and knowledgeable AI assistant with expertise in critical thinking and argumentation analysis. Always answer as helpfully as possible.

Decide whether a given PREMISE represents a reason for (entails or backs) a given HYPOTHESIS. 

Read the PREMISE and HYPOTHESIS carefully.

PREMISE
:::
{premise}
:::

HYPOTHESIS
:::
{hypothesis}
:::

Which of the following is the most appropriate description of the relation between PREMISE and HYPOTHESIS?

A) The PREMISE paraphrases and is roughly equivalent with the HYPOTHESIS
B) The PREMISE is different from but supports the HYPOTHESIS
C) Neither A nor B

Just answer in the line below with A, B or C. No comments, no explanation.
"""
                ),
            ),
        )
        registry.register(
            "prompt_q_attacks",
            PromptTemplate(
                input_variables=["premise", "hypothesis"],
                template=(
                    """You are a helpful, honest and knowledgeable AI assistant with expertise in critical thinking and argumentation analysis. Always answer as helpfully as possible.

Decide whether a given PREMISE represents a reason against (attacks or disconfirms) a given HYPOTHESIS. 

Read the PREMISE and HYPOTHESIS carefully.

PREMISE
:::
{premise}
:::

HYPOTHESIS
:::
{hypothesis}
:::

Which of the following is the most appropriate description of the relation between PREMISE and HYPOTHESIS?

A) The PREMISE merely states that the HYPOTHESIS is (partly) false or wrong.
B) The PREMISE provides an independent reason for why the HYPOTHESIS is false or wrong.
C) Neither A nor B

Just answer with A, B or C in the line below. No comments, no explanation.
"""
                ),
            ),
        )
        registry.register(
            "prompt_pro_quote",
            PromptTemplate(
                input_variables=["claim", "source_text"],
                template=(
                    """You are a helpful, honest and knowledgeable AI assistant with expertise in critical thinking and argumentation analysis. Always answer as helpfully as possible.

Identify a text span that represents a reason for a given claim. 

Read the TEXT and CLAIM carefully.

TEXT
:::
{source_text}
:::

CLAIM
:::
{claim}
:::

What is the TEXT's strongest reason for the CLAIM? Produce a verbatim quote from the TEXT containing at most three sentences. Use quotation marks, don't comment, no explanations.
"""
                ),
            ),
        )
        registry.register(
            "prompt_con_quote",
            PromptTemplate(
                input_variables=["claim", "source_text"],
                template=(
                    """You are a helpful, honest and knowledgeable AI assistant with expertise in critical thinking and argumentation analysis. Always answer as helpfully as possible.

Identify a text span that represents a reason against (an objection to) a given claim.

Read the TEXT and CLAIM carefully.

TEXT
:::
{source_text}
:::

CLAIM
:::
{claim}
:::

What is the TEXT's strongest reason against the CLAIM? Produce a verbatim quote from the TEXT containing at most three sentences. Use quotation marks, don't comment, no explanations.
"""
                ),
            ),
        )
        registry.register(
            "prompt_pros",
            PromptTemplate(
                input_variables=["claim", "source_text"],
                template=(
                    """
You are a helpful, honest and knowledgeable AI assistant with expertise in critical thinking and argumentation analysis. Always answer as helpfully as possible.

# Your Assignment
Summarize particular pro arguments presented in a text.

# Inputs
Use the following inputs (a TEXT which contains a certain CLAIM) to solve your assignment.

TEXT:
:::
{source_text}
:::

CLAIM:
:::
{claim}
:::

# Detailed Instructions
What are the main arguments presented in the TEXT that directly support the CLAIM?

- Sketch arguments in one or two grammatically correct sentences.
- Try to identify distinct reasons (at most four, but fewer is also ok), and avoid repeating one and the same argument in different words.
- Avoid merely restating the CLAIM in different words.
- IMPORTANT: Stay faithful to the text! Don't invent your own reasons. Don't provide reasons which are neither presented nor discussed in the text.
- Enumerate the text's arguments for the CLAIM consecutively -- beginning with 1. -- and start each argument with a new line.
- (Write 'None' if the TEXT doesn't contain any such arguments.)

# Answer
I see the following arguments for the CLAIM in the TEXT above:
"""
                ),
            ),
        )
        registry.register(
            "prompt_cons",
            PromptTemplate(
                input_variables=["claim", "source_text"],
                template=(
                    """
You are a helpful, honest and knowledgeable AI assistant with expertise in critical thinking and argumentation analysis. Always answer as helpfully as possible.

# Your Assignment
Summarize particular con arguments (objections) presented in a text.

# Inputs
Use the following inputs (a TEXT which contains a certain CLAIM) to solve your assignment.

TEXT:
:::
{source_text}
:::

CLAIM:
:::
{claim}
:::

# Detailed Instructions
What are the main arguments presented in the TEXT that directly attack (i.e., refute, speak against or disconfirm) the CLAIM?

- Sketch arguments in one or two grammatically correct sentences.
- Try to identify distinct reasons (at most four, but fewer is also ok), and avoid repeating one and the same argument in different words.
- Avoid merely negating the CLAIM.
- IMPORTANT: Stay faithful to the text! Don't invent your own con reasons. Don't provide reasons which are neither presented nor discussed in the text.
- Enumerate the text's objections against the CLAIM consecutively -- beginning with 1. -- and start each argument with a new line.
- (Write 'None' if the TEXT doesn't contain any such arguments.)

# Answer
I see the following arguments against the CLAIM in the TEXT above:
"""
                ),
            ),
        )
        registry.register(
            "prompt_annotation",
            PromptTemplate(
                input_variables=["claim", "source_text"],
                template=(
                    """
You are a helpful, honest and knowledgeable AI assistant with expertise in critical thinking and argumentation analysis. Always answer as helpfully as possible.

# Your Assignment
Identify the text-span in a text that expresses a given claim most clearly.

# Inputs
Use the following inputs (a TEXT and a certain CLAIM) to solve your assignment.

TEXT:
:::
{source_text}
:::

CLAIM:
:::
{claim}
:::

# Detailed Instructions
Give a single verbatim quote from the TEXT that asserts or presents the CLAIM most clearly.
Use quotation marks. Don't provide alternatives, comments or explanations.

# Answer
Here is my answer, a verbatim quote from the TEXT:"""
                ),
            ),
        )
        registry.register(
            "prompt_shorten",
            PromptTemplate(
                input_variables=["reason", "valence", "claim"],
                template=(
                    """
You are a helpful, honest and knowledgeable AI assistant with expertise in critical thinking and argumentation analysis. Always answer as helpfully as possible.

# Your Assignment
Shorten the presentation of an argument {valence} a given claim.

# Inputs
Use the following inputs (an ARGUMENT that speaks {valence} a CLAIM) to solve your assignment.

ARGUMENT:
:::
{reason}
:::

CLAIM:
:::
{claim}
:::

# Detailed Instructions
Rephrase the ARGUMENT in a concise and shorter way, highlighting its gist.
Don't provide alternatives, comments or explanations.

# Answer
My shortened paraphrase:"""
                ),
            ),
        )
        registry.register(
            "prompt_headline",
            PromptTemplate(
                input_variables=["reason", "valence", "claim"],
                template=(
                    """
You are a helpful, honest and knowledgeable AI assistant with expertise in critical thinking and argumentation analysis. Always answer as helpfully as possible.

# Your Assignment
Find a telling title for an argument.

# Inputs
Use the following inputs (an ARGUMENT that speaks {valence} a CLAIM) to solve your assignment.

CLAIM:
:::
{claim}
:::

ARGUMENT:
:::
{reason}
:::

# Detailed Instructions
Provide a single, very concise title for the ARGUMENT (not more than 4 words).
While keeping it short, make sure that your title captures the specifics of the ARGUMENT (and not just the CLAIM).
A good title highlights the argument's key point in a few catchy words.
Don't provide alternatives, comments or explanations. Just a good title.

# Answer
Concise title of the ARGUMENT:
"""
                ),
            ),
        )

        return registry


class InformalArgMapChain(Chain):
    max_words_reason = 25
    max_words_claim = 25
    max_words_title = 6
    max_parallel_reasons = 3  # max number of parallel reasons
    verbose = True
    prompt_registry: PromptRegistry = PromptRegistry()
    llm: BaseLLM
    argmap_depth = 2

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.prompt_registry = PromptRegistryFactory().create()
        self.llm = kwargs["llm"]

    @property
    def input_keys(self) -> list[str]:
        return ["prompt", "completion", "claims"]

    @property
    def output_keys(self) -> list[str]:
        return ["argmap"]

    @staticmethod
    def parse_list(inputs: dict[str, str]) -> dict[str, list[str]]:
        list_items: list[str] = []
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

    def _init_argmap(self, claims) -> InformalArgMap:
        """
        initializes argmap with central claims (mutually exclusive)
        """
        argmap = InformalArgMap()
        for e, claim in enumerate(claims):
            argmap.nodelist.append(
                ArgMapNode(
                    id=str(uuid.uuid4()),
                    text=claim,
                    label=f"Claim-{e+1}",
                    nodeType="proposition",
                    annotationReferences=[],
                )
            )
        for claim_a in argmap.nodelist:
            for claim_b in argmap.nodelist:
                if claim_a != claim_b:
                    argmap.edgelist.append(
                        ArgMapEdge(
                            source=claim_a.id,
                            target=claim_b.id,
                            valence="con",
                        )
                    )
        return argmap

    def _is_pro_reason(self, claim: str, reason: str) -> bool:
        if isinstance(self.llm, OpenAI):
            llm_kwargs = {"max_tokens": 4, "temperature": 0.4}
        else:
            llm_kwargs = {}
        chain_q_supports = LLMChain(
            llm=self.llm, prompt=self.prompt_registry["prompt_q_supports"], verbose=self.verbose, llm_kwargs=llm_kwargs
        )
        answer = chain_q_supports.run(premise=reason, hypothesis=claim)
        print(f"> Answer: {answer}")
        answer = answer.strip(" \n")
        is_pro = (
            answer.lower().startswith("b")
            or "b)" in answer.lower()
            and "a)" not in answer.lower()
            and "c)" not in answer.lower()
        )
        return is_pro

    def _is_con_reason(self, claim: str, reason: str) -> bool:
        if isinstance(self.llm, OpenAI):
            llm_kwargs = {"max_tokens": 4, "temperature": 0.4}
        else:
            llm_kwargs = {}
        chain_q_attacks = LLMChain(
            llm=self.llm, prompt=self.prompt_registry["prompt_q_attacks"], verbose=self.verbose, llm_kwargs=llm_kwargs
        )
        answer = chain_q_attacks.run(premise=reason, hypothesis=claim)
        print(f"> Answer: {answer}")
        answer = answer.strip(" \n")
        is_con = (
            answer.lower().startswith("b")
            or "b)" in answer.lower()
            and "a)" not in answer.lower()
            and "c)" not in answer.lower()
        )
        return is_con

    def _is_supported(self, claim: str, source_text: str) -> bool:
        # get quote that represents strongest pro reason
        chain_pro_quote = LLMChain(llm=self.llm, prompt=self.prompt_registry["prompt_pro_quote"], verbose=self.verbose)
        quote = chain_pro_quote.run(claim=claim, source_text=source_text)
        print(f"> Answer: {quote}")
        quote = quote.strip(" \n")
        quote = quote.split("\n")[0]
        quote = quote.strip("\"")

        if not quote or not quote in source_text:
            return False

        # check if quote is actually pro reason
        is_supported = self._is_pro_reason(claim=claim, reason=quote)
        return is_supported

    def _is_attacked(self, claim: str, source_text: str) -> bool:
        # get quote that represents strongest con reason
        chain_con_quote = LLMChain(llm=self.llm, prompt=self.prompt_registry["prompt_con_quote"], verbose=self.verbose)
        quote = chain_con_quote.run(claim=claim, source_text=source_text)
        print(f"> Answer: {quote}")
        quote = quote.strip(" \n")
        quote = quote.split("\n")[0]
        quote = quote.strip("\"")

        if not quote or not quote in source_text:
            return False

        # check if quote is actually con reason
        is_attacked = self._is_con_reason(claim=claim, reason=quote)
        return is_attacked

    def _are_equivalent(self, reason1: str, reason2: str) -> bool:
        """checks if two reasons are equivalent"""
        if isinstance(self.llm, OpenAI):
            llm_kwargs = {"max_tokens": 4, "temperature": 0.4}
        else:
            llm_kwargs = {}
        chain_q_equivalent = LLMChain(
            llm=self.llm,
            prompt=self.prompt_registry["prompt_q_equivalent"],
            verbose=self.verbose,
            llm_kwargs=llm_kwargs,
        )
        answer = chain_q_equivalent.run(reason1=reason1, reason2=reason2)
        answer = str(answer)
        print(f"> Answer: {answer}")
        answer = answer.strip(" \n")
        answer = answer.split("\n")[0]
        answer = answer.strip("\" ")

        if answer.lower().startswith("yes"):
            return True

        return False

    def _is_redundant(self, argmap: InformalArgMap, reason: str, annotations: List[AnnotationSpan]) -> bool:
        """
        checks if reason is redundant, i.e. equivalent to a reason already in the argmap
        """
        if not reason:
            return True

        # check redundancy only for nodes with overlapping annotation span
        overlapping_nodes = []
        for node in argmap.nodelist:
            overlaps = False
            for span1 in annotations:
                for span2 in node.annotations:
                    if span1.start < span2.end and span2.start < span1.end:
                        overlaps = True
                        break
            if overlaps:
                overlapping_nodes.append(node)

        for node in overlapping_nodes:
            if self._are_equivalent(reason, node.text):
                return True

        return False

    def _shorten_reason(self, reason: str, claim: str = "", valence: str = "for") -> str:
        """
        subcall: shorten reason if necessary
        """

        if not reason:
            return reason
        print(f"Word count current reason: {len(reason.split(' '))}")

        chain_shorten = LLMChain(llm=self.llm, prompt=self.prompt_registry["prompt_shorten"], verbose=self.verbose)
        if len(reason.split(" ")) > self.max_words_reason:
            gist = chain_shorten.run(reason=reason, valence=valence, claim=claim)
            gist = gist.strip(" \n")
            print(f"Word count shortened gist: {len(gist.split(' '))}")
            reason = gist if len(gist.split(" ")) < len(reason.split(" ")) else reason

        return reason

    def _process_reasons(self, reasons: str, claim: str = "", valence: str = "for") -> list[str]:
        """
        subcall: splits reasons list into individual reasons and shortnes each if necessary
        """

        parse_chain = TransformChain(input_variables=["list_text"], output_variables=["list_items"], transform=self.parse_list)  # type: ignore
        reasons_l = parse_chain.run({"list_text": reasons})
        reasons_l = [self._shorten_reason(reason, valence=valence, claim=claim) for reason in reasons_l if reason]
        return reasons_l

    def _add_argument(
        self,
        argmap: InformalArgMap,
        reason: str,
        label: str = "",
        target_id: Optional[str] = None,
        valence: str = "for",
        annotations: Optional[list[AnnotationSpan]] = None,
    ) -> ArgMapNode:
        """
        subcall: adds and returns node
        """
        if annotations is None:
            annotations = []
        node_id = str(uuid.uuid4())
        node = ArgMapNode(
            id=node_id,
            text=reason,
            label=label,
            nodeType="proposition",
            annotations=annotations,
        )
        argmap.nodelist.append(node)

        if target_id:
            edge = ArgMapEdge(
                source=node.id,
                target=target_id,
                valence="pro" if valence == "for" else "con",
            )
            argmap.edgelist.append(edge)

        return node

    def _match_quote(self, quote: str, source_text: str) -> list[AnnotationSpan]:
        """
        utility function:
        tries to match quote to a text spans
        returns list of text spans
        """
        quote = quote.strip(' "\n')
        if not quote:
            return []

        # normalize quote
        quote = quote.lower()
        quote = re.sub(r"\W+", "", quote)

        # normalize source text
        source_text = source_text.lower()
        source_text = re.sub(r"\W+", "", source_text)

        annotations: list[AnnotationSpan] = []

        while quote in source_text:
            start = source_text.find(quote)
            end = start + len(quote)
            annotations.append(AnnotationSpan(start=start, end=end))
            source_text = source_text[end:]

        return annotations

    def _process_and_add_arguments(
        self, argmap: InformalArgMap, completion: str, reasons: str, target_node: ArgMapNode, valence: str = "for"
    ) -> list[ArgMapNode]:
        """
        subcall:
        - splits and processes reasons,
        - adds arguments and edges to argmap,
        - returns newly added nodes
        """
        new_nodes = []
        claim = target_node.text
        reasons_l = self._process_reasons(reasons, claim=claim, valence=valence)

        doublecheck = self._is_pro_reason if valence == "for" else self._is_con_reason
        reasons_l = [reason for reason in reasons_l if doublecheck(claim=claim, reason=reason)]
        reasons_l = reasons_l[: self.max_parallel_reasons]  # cut off reasons

        chain_headline = LLMChain(llm=self.llm, prompt=self.prompt_registry["prompt_headline"], verbose=self.verbose)
        chain_annotation = LLMChain(
            llm=self.llm, prompt=self.prompt_registry["prompt_annotation"], verbose=self.verbose
        )

        for reason in reasons_l:
            headline: str = chain_headline.run(reason=reason, claim=claim, valence=valence)
            headline = headline.strip(" \n")
            headline = headline.split("\n")[0]
            headline = " ".join(headline.split()[: self.max_words_title])
            quote = chain_annotation.run(source_text=completion, claim=reason)
            print(f"> Answer: {quote}")
            annotations = self._match_quote(quote, completion)
            # only add argument if a match has been found
            if annotations:
                if not self._is_redundant(argmap=argmap, reason=reason, annotations=annotations):
                    new_node = self._add_argument(
                        argmap=argmap,
                        reason=reason,
                        label=headline,
                        target_id=target_node.id,
                        valence=valence,
                        annotations=annotations,
                    )
                    new_nodes.append(new_node)

        return new_nodes

    def _call(
        self, inputs: dict[str, Any], run_manager: Optional[CallbackManagerForChainRun] = None
    ) -> dict[str, dict]:
        # define subchains
        chain_pros = LLMChain(llm=self.llm, prompt=self.prompt_registry["prompt_pros"], verbose=self.verbose)
        chain_cons = LLMChain(llm=self.llm, prompt=self.prompt_registry["prompt_cons"], verbose=self.verbose)

        completion = inputs["completion"]
        claims = inputs["claims"]
        argmap = self._init_argmap(claims)

        new_nodes: list[ArgMapNode] = argmap.nodelist

        for depth in range(self.argmap_depth):
            target_nodes = copy.deepcopy(new_nodes)
            new_nodes = []

            print("###")
            print(f"Mining arguments at depth {depth+1}.")
            print(f" Number of target nodes: {len(target_nodes)}.")
            print(f" Number of nodes in argmap: {len(argmap.nodelist)}.")
            print("###")

            for enum, target_node in enumerate(target_nodes):
                print(f"### Processing target node {enum} of {len(target_nodes)} at depth {depth+1}. ###")
                claim = target_node.text

                is_supported = self._is_supported(claim=claim, source_text=completion)
                is_attacked = self._is_attacked(claim=claim, source_text=completion)

                if is_supported:
                    pros = chain_pros.run(claim=claim, source_text=completion)
                    print(f"> Answer: {pros}")
                    new_pros = self._process_and_add_arguments(
                        argmap=argmap, completion=completion, reasons=pros, target_node=target_node, valence="for"
                    )
                    new_nodes.extend(new_pros)

                if is_attacked:
                    cons = chain_cons.run(claim=claim, source_text=completion)
                    print(f"> Answer: {cons}")
                    new_cons = self._process_and_add_arguments(
                        argmap=argmap, completion=completion, reasons=cons, target_node=target_node, valence="against"
                    )
                    new_nodes.extend(new_cons)

        return {"argmap": argmap.model_dump()}


class InformalArgMapBuilder(AbstractArtifactDebugger):
    """InformalArgMap Debugger

    This debugger is responsible for extracting informal argument maps from the
    deliberation in the completion. It uses plain and non-technical successive LLM
    calls to gradually sum,m,arize reasons and build an argmap.

    It requires the following artifacts:
    - claims
    """

    _KW_DESCRIPTION = "Informal Argument Map"
    _KW_PRODUCT = "informal_argmap"
    _KW_REQUIREMENTS = ["claims"]

    @staticmethod
    def get_product() -> str:
        return InformalArgMapBuilder._KW_PRODUCT

    @staticmethod
    def get_requirements() -> list[str]:
        return InformalArgMapBuilder._KW_REQUIREMENTS

    @staticmethod
    def get_description() -> str:
        return InformalArgMapBuilder._KW_DESCRIPTION

    def _debug(self, prompt: str, completion: str, debug_results: DebugResults):
        """Reconstruct reasoning as argmap."""

        claims = next(artifact.data for artifact in debug_results.artifacts if artifact.id == "claims")

        llm = init_llm_from_config(self._debug_config)
        generation_kwargs = self._debug_config.generation_kwargs
        llmchain = InformalArgMapChain(llm=llm, generation_kwargs=generation_kwargs)
        argmap = llmchain.run(prompt=prompt, completion=completion, claims=claims)

        artifact = Artifact(
            id=self._KW_PRODUCT,
            description=self._KW_DESCRIPTION,
            data=argmap,
        )

        debug_results.artifacts.append(artifact)
