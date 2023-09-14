
from __future__ import annotations
from typing import List, Optional, Dict, Tuple

import copy
import re
import uuid

from langchain.chains.base import Chain
from langchain.chains import LLMChain, TransformChain
from langchain.llms import BaseLLM
from langchain.prompts import PromptTemplate

from logikon.debuggers.base import AbstractDebugger
from logikon.debuggers.utils import init_llm_from_config
from logikon.schemas.results import DebugResults, Artifact
from logikon.schemas.argument_mapping import InformalArgMap, ArgMapNode, ArgMapEdge, AnnotationSpan



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

        registry.register("prompt_q_supported", PromptTemplate(
                input_variables=["reason", "source_text", "ctype"],
                template=(
                    "You are a helpful assisstant and expert for critical thinking and argumentation analysis.\n\n"
                    "Your task: Assess whether it is argued for a certain {ctype}.\n"
                    "TEXT:\n\n{source_text}\n\n"
                    "The TEXT presents the following {ctype}:\n\n{reason}\n\n"
                    "Does the TEXT, beyond stating the {ctype}, present or discuss a justification for it? "
                    "That is, are there any arguments in the TEXT which primarily serve to support and back up the {ctype} (y/n)?"
                )
            )
        )
        registry.register("prompt_q_attacked", PromptTemplate(
                input_variables=["reason", "source_text", "ctype"],
                template=(
                    "You are a helpful assisstant and expert for critical thinking and argumentation analysis.\n\n"
                    "Your task: Assess whether it is argued against a certain {ctype}.\n"
                    "TEXT:\n\n{source_text}\n\n"
                    "The TEXT presents the following {ctype}:\n\n{reason}\n\n"
                    "Does the TEXT, beyond stating the {ctype}, present or discuss an objection against it? "
                    "That is, are there any arguments in the TEXT which primarily serve to refute the {ctype} (y/n)?"
                )
            )
        )
        registry.register("prompt_pros", PromptTemplate(
                input_variables=["claim","source_text"],
                template=(
                    "You are a helpful assisstant and expert for critical thinking and argumentation analysis.\n\n"
                    "Your task: Summarize specific pro arguments presented in the following text.\n"
                    "TEXT\n\n{source_text}\n\n"
                    "CLAIM\n\n{claim}\n\n"
                    "What are the main arguments presented in the TEXT that directly support the CLAIM?\n"
                    "- Sketch arguments in one or two grammatically correct sentences.\n"
                    "- Try to identify distinct reasons (at most four, but fewer is also ok), and avoid repeating one and the same argument in different words.\n"
                    "- Avoid merely restating the CLAIM in different words.\n"
                    "- IMPORTANT: Don't invent your own reasons. Don't write down arguments neither presented nor discussed in the text.\n"                    
                    "- Enumerate the text's arguments consecutively -- beginning with 1. -- and start each argument with a new line.\n"
                    "- (Write 'None' if the text doesn't contain any such arguments.)\n\n"
                    "I see the following arguments in the TEXT above:\n"
                )
            )
        )
        registry.register("prompt_cons", PromptTemplate(
                input_variables=["claim","source_text"],
                template=(
                    "You are a helpful assisstant and expert for critical thinking and argumentation analysis.\n\n"
                    "Your task: Summarize specific con arguments presented in the following text.\n"
                    "TEXT\n\n{source_text}\n\n"
                    "CLAIM\n\n{claim}\n\n"
                    "What are the main arguments presented in the TEXT that directly attack (i.e., refute, speak against or disconfirm) the CLAIM?\n"
                    "- Sketch arguments in one or two grammatically correct sentences.\n"
                    "- Try to identify distinct reasons (at most four, but fewer is also ok), and avoid repeating one and the same argument in different words.\n"
                    "- IMPORTANT: Don't invent your own reasons. Don't write down arguments neither presented nor discussed in the text.\n"                    
                    "- Enumerate the text's arguments consecutively -- beginning with 1. -- and start each argument with a new line.\n"
                    "- (Write 'None' if the text doesn't contain any such arguments.)\n\n"
                    "I see the following arguments in the TEXT above:\n"
                )
            )
        )
        registry.register("prompt_annotation", PromptTemplate(
                input_variables=["claim","source_text"],
                template=(
                    "You are a helpful assisstant and expert for critical thinking and argumentation analysis.\n\n"
                    "Your task: Identify the paragraph in the TEXT that expresses the CLAIM most clearly.\n"
                    "TEXT\n\n{source_text}\n\n"
                    "CLAIM\n\n{claim}\n\n"
                    "Give a verbatim quote from the TEXT that asserts or presents the CLAIM. Use quotation marks.\n\n"
                    "Here is my answer, a verbatim quote:"
                )
            )
        )
        registry.register("prompt_shorten", PromptTemplate(
                input_variables=["reason", "valence", "claim"],
                template=(
                    "You are a helpful assisstant and expert for critical thinking and argumentation analysis.\n\n"
                    "Your task: Shorten the presentation of an argument {valence} a given claim.\n\n"
                    "CLAIM\n\n{claim}\n\n"
                    "Shorten the following ARGUMENT (which speaks {valence} the above CLAIM).\n"
                    "ARGUMENT\n\n{reason}\n\n"
                    "Rephrase the ARGUMENT in a concise and shorter way, highlighting its gist."
                )
            )
        )
        registry.register("prompt_headline", PromptTemplate(
                input_variables=["reason", "valence", "claim"],
                template=(
                    "You are a helpful assisstant and expert for critical thinking and argumentation analysis.\n\n"
                    "Your task: Find a telling name for an argument.\n\n"
                    "CLAIM\n\n{claim}\n\n"
                    "Consider the following argument {valence} CLAIM.\n\n{reason}\n\nSummarize the argument in a concise headline (with 1-4 words)."
                )
            )
        )

        return registry


class InformalArgMapChain(Chain):

    max_words_reason = 25
    max_words_claim = 25
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
    def input_keys(self) -> List[str]:
        return ['prompt', 'completion', 'claims']

    @property
    def output_keys(self) -> List[str]:
        return ['argmap']


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

    @staticmethod
    def parse_yn_answer(answer_text: str, default: bool) -> bool:
        answer_text = answer_text.strip(" \n(").lower()
        answer_text = answer_text.split("\n")[0]
        if (
            answer_text.startswith("y") or 
            ("(y)" in answer_text and not "(n)" in answer_text)
        ):
            return True
        if (
            answer_text.startswith("n") or 
            ("(n)" in answer_text and not "(y)" in answer_text)
        ):
            return True

        return default

    def _init_argmap(self, claims) -> InformalArgMap:
        """
        initializes argmap with central claims (mutually exclusive)
        """
        argmap = InformalArgMap()
        for e, claim in enumerate(claims):
            argmap.nodelist.append(ArgMapNode(
                id=str(uuid.uuid4()),
                text=claim,
                label=f"Claim-{e+1}",
                nodeType="proposition",
                annotationReferences=[],            
            ))
        for claim_a in argmap.nodelist:
            for claim_b in argmap.nodelist:
                if claim_a != claim_b:
                    argmap.edgelist.append(ArgMapEdge(
                        source=claim_a.id,
                        target=claim_b.id,
                        valence="con",
                    ))
        return argmap


    def _shorten_reason(self, reason:str, claim:str="", valence:str="for") -> str:
        """
        subcall: shorten reason if necessary
        """

        if not reason:
            return reason
        print(f"Word count current reason: {len(reason.split(' '))}")

        chain_shorten = LLMChain(llm=self.llm, prompt=self.prompt_registry["prompt_shorten"], verbose=self.verbose)
        if len(reason.split(" "))>self.max_words_reason:
            gist = chain_shorten.run(reason=reason, valence=valence, claim=claim)
            gist = gist.strip(" \n")
            print(f"Word count shortened gist: {len(gist.split(' '))}")
            reason = gist if len(gist.split(' '))<len(reason.split(' ')) else reason

        return reason


    def _process_reasons(self, reasons:str, claim:str="", valence:str="for") -> List[str]:
        """
        subcall: splits reasons list into individual reasons and shortnes each if necessary
        """

        parse_chain = TransformChain(input_variables=["list_text"], output_variables=["list_items"], transform=self.parse_list)
        reasons_l = parse_chain.run({"list_text": reasons})
        reasons_l = [
            self._shorten_reason(reason, valence=valence, claim=claim)
            for reason in reasons_l
            if reason
        ]
        return reasons_l


    def _add_argument(self, argmap: InformalArgMap, reason:str, label:str="", target_id:Optional[str]=None, valence:str="for", annotations:List[AnnotationSpan]=[]) -> ArgMapNode:
        """
        subcall: adds and returns node
        """
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
                valence="pro" if valence=="for" else "con",
            )
            argmap.edgelist.append(edge)     

        return node  


    def _match_quote(self, quote:str, source_text: str) -> List[AnnotationSpan]:
        """
        utility function:
        tries to match quote to a text spans
        returns list of text spans
        """
        quote = quote.strip(" \"\n")
        if not quote:
            return []

        # normalize quote
        quote = quote.lower()
        quote = re.sub(r'\W+', '', quote)

        # normalize source text
        source_text = source_text.lower()
        source_text = re.sub(r'\W+', '', source_text)

        annotations: List[AnnotationSpan] = []

        while quote in source_text:
            start = source_text.find(quote)
            end = start + len(quote)
            annotations.append(AnnotationSpan(start=start, end=end))
            source_text = source_text[end:]

        return annotations


    def _process_and_add_arguments(
            self,
            argmap: InformalArgMap,
            completion: str,
            reasons:str,
            target_node:ArgMapNode,
            valence:str="for"
        ) -> List[ArgMapNode]:
        """
        subcall:
        - splits and processes reasons,
        - adds arguments and edges to argmap,
        - returns newly added nodes
        """
        new_nodes = []
        claim = target_node.text
        reasons_l = self._process_reasons(reasons, claim=claim, valence=valence)
        reasons_l = reasons_l[:self.max_parallel_reasons] # cut off reasons

        chain_headline = LLMChain(llm=self.llm, prompt=self.prompt_registry["prompt_headline"], verbose=self.verbose)
        chain_annotation = LLMChain(llm=self.llm, prompt=self.prompt_registry["prompt_annotation"], verbose=self.verbose)


        for reason in reasons_l:
            headline = chain_headline.run(reason=reason, claim=claim, valence=valence)
            headline = headline.strip(" \n")
            quote = chain_annotation.run(source_text=completion, claim=reason)
            print(f"> Answer: {quote}")
            annotations = self._match_quote(quote, completion)
            new_node = self._add_argument(argmap=argmap, reason=reason, label=headline, target_id=target_node.id, valence=valence, annotations=annotations)
            new_nodes.append(new_node)

        return new_nodes


    def _call(self, inputs: Dict[str, str]) -> Dict[str, Dict]:


        # define subchains
        chain_pros = LLMChain(llm=self.llm, prompt=self.prompt_registry["prompt_pros"], verbose=self.verbose)
        chain_cons = LLMChain(llm=self.llm, prompt=self.prompt_registry["prompt_cons"], verbose=self.verbose)
        chain_q_supported = LLMChain(llm=self.llm, prompt=self.prompt_registry["prompt_q_supported"], verbose=self.verbose)
        chain_q_attacked = LLMChain(llm=self.llm, prompt=self.prompt_registry["prompt_q_attacked"], verbose=self.verbose)

        completion = inputs['completion']
        claims = inputs['claims']
        argmap = self._init_argmap(claims)

        new_nodes: List[ArgMapNode] = argmap.nodelist

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

                answer = chain_q_supported.run(reason=claim, source_text=completion, ctype="CLAIM")
                print(f"> Answer: {answer}")
                is_supported = self.parse_yn_answer(answer, False)

                answer = chain_q_attacked.run(reason=claim, source_text=completion, ctype="CLAIM")
                print(f"> Answer: {answer}")
                is_attacked = self.parse_yn_answer(answer, False)

                if is_supported:
                    pros = chain_pros.run(claim=claim, source_text=completion)
                    print(f"> Answer: {pros}")
                    new_pros = self._process_and_add_arguments(argmap=argmap, completion=completion, reasons=pros, target_node=target_node, valence="for")
                    new_nodes.extend(new_pros)

                if is_attacked:
                    cons = chain_cons.run(claim=claim, source_text=completion)
                    print(f"> Answer: {cons}")
                    new_cons = self._process_and_add_arguments(argmap=argmap, completion=completion, reasons=cons, target_node=target_node, valence="against")
                    new_nodes.extend(new_cons)


        return {"argmap": argmap.model_dump()}



class InformalArgMapBuilder(AbstractDebugger):
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

    @classmethod
    def get_product(cls) -> str:
        return cls._KW_PRODUCT

    @classmethod
    def get_requirements(cls) -> List[str]:
        return cls._KW_REQUIREMENTS    

    def _debug(self, prompt: str = "", completion: str = "", debug_results: Optional[DebugResults] = None):
        """Reconstruct reasoning as argmap."""

        assert debug_results is not None

        claims = next(
            artifact.data
            for artifact in debug_results.artifacts
            if artifact.id == "claims"
        )

        llm = init_llm_from_config(self._debug_config)
        generation_kwargs = self._debug_config.generation_kwargs
        llmchain = InformalArgMapChain(llm=llm, generation_kwargs=generation_kwargs)
        argmap = llmchain.run(
            prompt=prompt,
            completion=completion,
            claims=claims
        )

        artifact = Artifact(
            id=self._KW_PRODUCT,
            description=self._KW_DESCRIPTION,
            data=argmap,
        )

        debug_results.artifacts.append(artifact)
