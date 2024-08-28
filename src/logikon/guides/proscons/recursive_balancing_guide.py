import logging
from typing import Any, AsyncGenerator, Dict, Tuple

import networkx as nx  # type: ignore
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

import logikon.schemas.argument_mapping as am
from logikon import ScoreConfig, ascore
from logikon.backends import multiple_choice
from logikon.backends.chat_models_with_grammar import LLMBackends, LogitsModel, create_logits_model
from logikon.guides.base import AbstractGuide, AbstractGuideConfig, GuideOutputType

PLAUSIBILITY_THRESHOLD = 0.5

PROMPT1 = (
    "Assignment: Think about how to solve a given decision problem.\n"
    "Your task is to carefully think about a problem and explore possible solutions / decision options. "
    "This will typically include identifying the pros and cons for and against alternative solutions. "
    "The problem is: <problem>{message}</problem>"
    "Please provide your structured reasoning below."
)

PROMPT2 = (
    "Assignment: Draft a clear and concise response that summarizes the solution of a decision problem.\n"
    "Your task is to draft a response that solves a given decision problem. "
    "Your answer must say unequivocally which is the best decision to take, or the correct answer to "
    "the problem.\n"
    "The reasoning is:\n<reasoning>{reasoning}</reasoning>\n"
    "The problem is:\n<problem>{message}</problem>\n"
    "Just provide your concise response below."
)

WEIGHING_PROMPT_INIT = (
    "Please read the following decision problem carefully.\n"
    "The problem is: <problem>{problem}</problem>\n"
    "I'll ask you to assess the plausibility of various claims and "
    "you should take the above problem into account when doing so.\n"
    "Understood?"
)

WEIGHING_PROMPT_PC = (
    "Assignment: Assess the plausibility of a claim.\n"
    "Your task is to assess the plausibility of the following claim by "
    "weighing the given pros and cons.\n"
    "The claim is: <claim>{claim}</claim>\n"
    "The following reasons are given in support of the claim:\n"
    "<pros>\n{pros}\n</pros>\n"
    "The following reasons are given against the claim:\n"
    "<cons>\n{cons}\n</cons>\n"
    "Remember that pro reasons increase the plausibility of the claim, while con reasons "
    "decrease it. For example, if a claim is disconfirmed by five very plausible con reasons and "
    "supported by a single pro reason only, the claim itself seems to be very implausible, "
    "too.\n"
    "So, in view of the reasons given, how plausible is the claim?\n"
    "(A) Very plausible\n"
    "(B) Rather plausible\n"
    "(C) Rather implausible\n"
    "(D) Very implausible\n"
    "Please provide your assessment by responding with A/B/C/D."
)

WEIGHING_PROMPT_LEAF = (
    "Assignment: Assess the plausibility of a claim.\n"
    "Your task is to assess the plausibility of the following claim in view "
    "of what has been said before.\n"
    "The claim is: <claim>{claim}</claim>\n"
    "How plausible is the claim?\n"
    "(A) Very plausible\n"
    "(B) Rather plausible\n"
    "(C) Rather implausible\n"
    "(D) Very implausible\n"
    "Please provide your assessment by responding with A/B/C/D."
)

PLAUSIBILITY_VALUES = {"A": 1, "B": 0.66, "C": 0.33, "D": 0}


class RecursiveBalancingGuideConfig(AbstractGuideConfig):
    """RecursiveBalancingGuideConfig

    Configuration for RecursiveBalancingGuide.

    """

    expert_model: str
    inference_server_url: str
    api_key: str = "EMPTY"
    llm_backend: str | LLMBackends = LLMBackends.VLLM
    generation_kwargs: dict | None = None
    classifier_kwargs: dict | None = None


class RecursiveBalancingGuide(AbstractGuide):

    __configclass__: type[AbstractGuideConfig] = RecursiveBalancingGuideConfig

    def __init__(self, tourist_llm: LogitsModel, config: RecursiveBalancingGuideConfig):
        super().__init__(tourist_llm, config)
        # set global kwargs for logikon analysts
        analyst_kwargs: dict[str, Any] = {
            "expert_model": config.expert_model,
            "inference_server_url": config.inference_server_url,
            "api_key": config.api_key,
            "llm_backend": config.llm_backend,
        }
        if config.generation_kwargs is not None:
            analyst_kwargs["generation_kwargs"] = config.generation_kwargs
        if config.classifier_kwargs is not None:
            analyst_kwargs["classifier_kwargs"] = config.classifier_kwargs

        self.analyst_kwargs = analyst_kwargs
        # FIXME
        # Check that tourist_llm is suitable for multiple_choice_querying!

    def deliberate(self, message):
        """LCEL Chain for internal deliberation."""
        # fmt: off
        chain = (
            ChatPromptTemplate.from_template(PROMPT1)
            | self.tourist_llm.with_retry()
            | StrOutputParser()
        )
        # fmt: on
        reasoning = chain.invoke(message)
        return reasoning

    def draft_response(self, message, reasoning):
        """LCEL Chain for drafting response."""
        # fmt: off
        chain = (
            ChatPromptTemplate.from_template(PROMPT2)
            | self.tourist_llm.with_retry()
            | StrOutputParser()
        )
        # fmt: on
        response = chain.invoke({"message": message, "reasoning": reasoning})
        response = response.strip(" \n")
        return response

    async def weigh_reasons(self, problem: str, argmap: nx.DiGraph) -> str:
        """Weighs reasons in argmap and produces a reasoning trace."""

        arggraph = am.FuzzyArgGraph(argmap)
        history = []
        visited = []
        assessments: dict[str, float] = {}

        async def assess_node(node) -> float:
            nonlocal history
            nonlocal assessments
            if node in assessments:
                return assessments[node]
            visited.append(node)
            pros = []
            cons = []
            for pro in arggraph.supporting_reasons(node):
                if pro not in visited:
                    assess = await assess_node(pro)
                    if assess >= PLAUSIBILITY_THRESHOLD:
                        label = arggraph.nodes[pro]["label"]
                        text = arggraph.nodes[pro]["text"]
                        pros.append(f"* [{label}]: {text}")
            for con in arggraph.attacking_reasons(node):
                if con not in visited:
                    assess = await assess_node(con)
                    if assess >= PLAUSIBILITY_THRESHOLD:
                        label = arggraph.nodes[con]["label"]
                        text = arggraph.nodes[con]["text"]
                        cons.append(f"* [{label}]: {text}")

            pros_ = "\n".join(pros) if pros else "None."
            cons_ = "\n".join(cons) if cons else "None."

            node_label = arggraph.nodes[node]["label"]
            node_text = arggraph.nodes[node]["text"]
            claim_ = f"[{node_label}]: {node_text}"

            if not pros and not cons:
                messages = [
                    HumanMessage(content=WEIGHING_PROMPT_INIT.format(problem=problem)),
                    AIMessage(content="Yes. Let's start."),
                    HumanMessage(content=WEIGHING_PROMPT_LEAF.format(claim=claim_)),
                ]
            else:
                messages = [
                    HumanMessage(content=WEIGHING_PROMPT_INIT.format(problem=problem)),
                    AIMessage(content="Yes. Let's start."),
                    HumanMessage(content=WEIGHING_PROMPT_PC.format(claim=claim_, pros=pros_, cons=cons_)),
                ]

            result = await multiple_choice.multiple_choice_query(
                question=messages,
                labels=["A", "B", "C", "D"],
                model=self.tourist_llm,
            )

            logging.debug(f"Probs: {result.probs}")

            expected_plausibility = sum([pr * PLAUSIBILITY_VALUES[la] for la, pr in result.probs.items()])
            assessments[node] = expected_plausibility

            if not pros and not cons:
                reasoning_trace = (
                    f"In view of the initial problem description, the claim '{claim_}' "
                    f"is assessed as {self.plausibility_to_str(expected_plausibility)}."
                )
            else:
                reasoning_trace = (
                    f"In view of the above considerations, the claim '{claim_}' "
                    f"is assessed as {self.plausibility_to_str(expected_plausibility)}, "
                    f"since it is supported by the following plausible reasons:\n{pros_}\n\n"
                    f"and disconfirmed by the following plausible reasons:\n{cons_}"
                )

            if expected_plausibility < PLAUSIBILITY_THRESHOLD:
                reasoning_trace += (
                    "\n\nFor lack of plausibility, this claim will not be "
                    "considered when balancing pros and cons below."
                )

            history.append(reasoning_trace)

            return expected_plausibility

        for root in arggraph.central_claims():
            assess = await assess_node(root)
            label = arggraph.nodes[root]["label"]
            text = arggraph.nodes[root]["text"]
            history.append(
                f"So, all in all, the central claim '[{label}]: {text}' "
                f"is assessed as {self.plausibility_to_str(assess)}."
            )

        logging.debug(f"Plausibility assessments: {assessments}")
        logging.debug(f"Reasoning trace: {history}")

        return "\n\n".join(history)

    async def guide(self, problem: str, **kwargs) -> AsyncGenerator[Tuple[GuideOutputType, Any], None]:  # type: ignore  # noqa: ARG002

        protocol = ""

        # Brainstorming pros and cons
        protocol += (
            "Let's start by brainstorming relevant considerations and think through the problem I've been given.\n\n"
        )

        yield GuideOutputType.progress, "Brainstorming ..."
        brainstorming = self.deliberate(problem)
        self.logger.debug(f"Deliberation: {brainstorming}")
        protocol += brainstorming

        # Argument Mapping
        yield GuideOutputType.progress, "Argument mapping ..."
        score_config = ScoreConfig(
            artifacts=["fuzzy_argmap_nx", "svg_argmap"],
            global_kwargs=self.analyst_kwargs,
        )
        score = await ascore(prompt=problem, completion=brainstorming, config=score_config)

        if score:
            # get SVG
            svg_artifact = score.get_artifact("svg_argmap")
            svg = svg_artifact.data if svg_artifact else ""
            self.logger.debug(f"SVG: {svg}")
            yield GuideOutputType.svg_argmap, svg

            # Guided balancing
            argmap_artifact = score.get_artifact("fuzzy_argmap_nx")
            if argmap_artifact:
                argmap = argmap_artifact.data
                self.logger.debug(f"FuzzyArgmapNX: {nx.node_link_data(argmap)}")
                yield GuideOutputType.nx_argmap, nx.node_link_data(argmap)

                yield GuideOutputType.progress, "Evaluating arguments ..."
                balancing_trace = await self.weigh_reasons(problem=problem, argmap=argmap)
                protocol += (
                    "\n\nNow, let's reconsider this step by step, and systematically balance the different reasons.\n\n"
                )
                protocol += balancing_trace
            yield GuideOutputType.protocol, protocol

        # Response drafting
        yield GuideOutputType.progress, "Drafting response ..."
        response = self.draft_response(problem, protocol)
        yield GuideOutputType.response, response

    async def health_check(self) -> Dict[str, Any]:
        status = {}

        # 1. Check if tourist model is available and healthy
        message = HumanMessage(content="(A) happy, or (B) sad?")
        try:
            res = await self.tourist_llm.get_labelprobs(messages=[message], labels=["A", "B"], top_logprobs=5)
            if all(label in res for label in ["A", "B"]):
                status["tourist_llm"] = "ok"
            else:
                status["tourist_llm"] = "error"
                self.logger.error(f"Tourist model health check failed: {res}")
        except Exception as e:
            status["tourist_llm"] = "error"
            self.logger.error(f"Tourist model health check failed: {e}")

        # 2. Check if expert model is available and healthy
        try:
            guide_llm: LogitsModel = create_logits_model(
                model_id=self.analyst_kwargs["expert_model"],
                inference_server_url=self.analyst_kwargs["inference_server_url"],
                api_key=self.analyst_kwargs["api_key"],
                llm_backend=self.analyst_kwargs["llm_backend"],
            )
            message = HumanMessage(content="(A) happy, or (B) sad?")
            res = await guide_llm.get_labelprobs(messages=[message], labels=["A", "B"], top_logprobs=5)
            if all(label in res for label in ["A", "B"]):
                status["expert_llm"] = "ok"
            else:
                status["expert_llm"] = "error"
                self.logger.error(f"Expert model health check failed: {res}")
        except Exception as e:
            status["expert_llm"] = "error"
            self.logger.error(f"Expert model health check failed: {e}")

        # 3. Check if classifier model is healthy
        try:
            if "classifier_kwargs" in self.analyst_kwargs:

                from logikon.backends.classifier import HfClassification, HfClassifier

                classifier = HfClassifier(**self.analyst_kwargs["classifier_kwargs"])
                clres = await classifier(
                    inputs="Exciting, let's have some fun!",
                    classes_verbalized=["sad", "fun"],
                    hypothesis_template="This text is about {}.",
                    batch_size=1,
                )
                if isinstance(clres[0], HfClassification) and all(label in clres[0].labels for label in ["sad", "fun"]):
                    status["classifier_llm"] = "ok"
                else:
                    status["classifier_llm"] = "error"
                    self.logger.error(f"Classifier server health check failed: {clres}")
        except Exception as e:
            status["classifier_llm"] = "error"
            self.logger.error(f"Classifier server health check failed: {e}")

        status["status"] = "ok" if all(v == "ok" for v in status.values()) else "error"

        return status

    @staticmethod
    def plausibility_to_str(plausibility: float) -> str:
        high = 0.75
        medium = 0.5
        low = 0.25
        if plausibility >= high:
            return "very plausible"
        elif plausibility >= medium:
            return "rather plausible"
        elif plausibility >= low:
            return "rather implausible"
        else:
            return "very implausible"
