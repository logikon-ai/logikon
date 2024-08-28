"""Module with analyst for building a fuzzy (informal) argument map with LCEL

```mermaid
flowchart TD
    p["`pros cons list`"]
    i["`issue`"]
    ur("unpack reason")
    pu["`pros cons unpacked (nodes)`"]
    rore("`add root-reason links`")
    rwre("`add reason-reason links`")
    links["`relevence network (unweighted links)`"]
    mcqu1("elicit valence & weight")
    prune("`rm multi-links`")
    wlinks["`relevence network (weighted links)`"]
    subgraph artifact
    ad["`data`"]
    am["`metadata`"]
    end
    p --> ur
    i --> ur
    ur --> pu
    pu--> rore --> links
    pu--> rwre --> links
    links --> mcqu1 --> prune --> wlinks --> ad
    ur --> am
```

"""

from __future__ import annotations

import asyncio
import copy
import json
import pprint
import random
import uuid
from typing import ClassVar, Sequence

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import SimpleJsonOutputParser
from langchain_core.prompts import AIMessagePromptTemplate, ChatPromptTemplate
from langchain_core.prompts.chat import MessageLikeRepresentation

import logikon.schemas.argument_mapping as am
from logikon.analysts import classifier_queries, lcel_queries
from logikon.analysts.base import SYSTEM_MESSAGE_PROMPT, ArtifcatAnalystConfig
from logikon.analysts.lcel_analyst import LCELAnalyst, LCELAnalystConfig
from logikon.schemas.argument_mapping import ArgMapNode, FuzzyArgMap, FuzzyArgMapEdge
from logikon.schemas.pros_cons import Claim, ClaimList, ProsConsList, RootClaim
from logikon.schemas.results import AnalysisState, Artifact

MAX_N_RELATIONS = 20
MAX_LEN_TITLE = 32
MAX_LEN_GIST = 180
N_DRAFTS = 3
LABELS = "ABCDEFG"


### EXAMPLES ###

EXAMPLES_UNPACKING = [
    {
        "issue": "Eating animals?",
        "title": "Climate impact",
        "gist": (
            "Animal farming contributes to climate change because it is extremely energy intensive and causes the"
            " degradation of natural carbon sinks through land use change."
        ),
        "reasons": [
            {
                "label": "Climate impact",
                "text": "Animal farming contributes to climate change.",
            },
            {
                "label": "High energy consumption",
                "text": "Animal farming is extremely energy intensive.",
            },
            {
                "label": "Land use change",
                "text": "Animal farming causes the degradation of natural carbon sinks through land use change.",
            },
        ],
    },
    {
        "issue": "Should Bullfighting be Banned?",
        "title": "Economic benefit",
        "gist": "Bullfighting can benefit national economies with an underdeveloped industrial base.",
        "reasons": [
            {
                "label": "Economic benefit",
                "text": "Bullfighting can benefit national economies with an underdeveloped industrial base.",
            }
        ],
    },
    {
        "issue": "Video games: good or bad?",
        "title": "Toxic communities",
        "gist": (
            "Many video gaming communities are widely regarded as toxic since online games create opportunities for"
            " players to stalk and abuse each other."
        ),
        "reasons": [
            {
                "label": "Toxic communities",
                "text": "Many video gaming communities are widely regarded as toxic.",
            },
            {
                "label": "Opportunities for abuse",
                "text": "Online games create opportunities for players to stalk and abuse each other.",
            },
        ],
    },
    {
        "issue": "Pick best draft",
        "title": "Readability",
        "gist": "Draft 1 is easier to read and much more funny than the other drafts.",
        "reasons": [
            {
                "label": "Readability",
                "text": "Draft 1 is easier to read than the other drafts.",
            },
            {
                "label": "Engagement",
                "text": "Draft 1 is much more funny than the other drafts.",
            },
        ],
    },
]


### FORMATTERS ###


def format_input(input_data) -> str:
    input_data = {k: v for k, v in input_data.items() if k in ["issue", "title", "gist"]}
    return json.dumps(input_data, indent=4)


def format_example(example_data: dict) -> str:
    formatted = ""
    formatted += "argumentation:\n"
    formatted += f"{format_input(example_data)}\n"
    # reasons block
    formatted_reasons = json.dumps(example_data["reasons"], indent=4)
    formatted += "unpacked reasons:\n"
    formatted += f"{formatted_reasons}"
    return formatted


def format_examples() -> str:
    formatted = [format_example(example) for example in EXAMPLES_UNPACKING]
    formatted = ["<example>\n" + example + "</example>" for example in formatted]
    formatted_s = "\n".join(formatted)
    return formatted_s


### LCEL QUERIES ###


_MESSAGES_UNPACK_REASONS: Sequence[MessageLikeRepresentation] = [
    SystemMessage(content=SYSTEM_MESSAGE_PROMPT),
    HumanMessage(
        content=(
            "Your Assignment: Unpack the individual reasons contained in an argumentation.\n\n"
            "Use the following inputs (the title and gist of an argumentation that addresses "
            "an issue) to solve your assignment.\n\n"
            "<inputs>\n"
            "{formatted_input}\n"
            "</inputs>\n\n"
            "What are the basic reasons contained in this argumentation?\n"
            "Let me give you more detailed instructions:\n"
            "- Read the gist carefully and extract all individual reasons it sets forth.\n"
            "- State each reason clearly in simple and plain language.\n"
            "- Each individual reason should be self-contained and unambiguous; avoid in "
            "particular anaphora and other context-dependent references (such as 'it', "
            "'that', 'this', 'the previous', ...).\n"
            "- The basic reason-statements you extract must themselves not contain any "
            "reasoning (as indicated, e.g., by 'because', 'since', 'therefore' ...).\n"
            "- State every reason in one grammatically correct sentence, staying close to "
            "the original wording. Provide a distinct title, too."
            "- The individual reasons you extract may mutually support each other, or "
            "represent independent reasons for one and the same conclusion; yet such "
            "argumentative relations need not be recorded (at this point).\n"
            "- If the argumentation gist contains a single reason, just include that very "
            "reason in your list.\n"
            "- Feel free to improve (e.g., shorten) the title(s).\n"
            "- Avoid repeating one and the same reason in different words.\n"
            "- IMPORTANT: Stay faithful to the gist! Don't invent your own reasons. Don't "
            "uncover implicit assumptions. Only provide reasons which are explicitly "
            "contained in the gist.\n"
            "- Use valid JSON syntax to structure your answer.\n\n"
            "I'll give you a few examples that illustrate the task.\n"
            "{formatted_examples}\n"
            "Before we start, can you please recall the input argumentation you're supposed to unpack?"
        )
    ),
    AIMessagePromptTemplate.from_template("{formatted_input}"),
    HumanMessage(
        content=(
            "Excellent. Now, process the above inputs and unpack the individual reasons contained "
            "in the argumentation.\n"
        )
    ),
]


class RelevanceNetworkBuilderConfig(LCELAnalystConfig):
    """RelevanceNetworkBuilderConfig

    Configuration for RelevanceNetworkBuilder.

    Fields:
        keep_pcl_valences (bool): keep (i.e. don't revise) global valences from pros and cons list
    """

    keep_pcl_valences: bool = True


class RelevanceNetworkBuilderLCEL(LCELAnalyst):
    """RelevanceNetworkBuilderLCEL

    This LCELAnalyst is responsible for creating a relevance network,
    i.e. a (quasi-) complete fuzzy argmap, from a pros and cons list and a given issue.

    """

    __product__ = "relevance_network"
    __requirements__: ClassVar[list[str | set]] = ["issue", "proscons"]
    __pdescription__ = (
        "Relevance network describing comprehensively the strengths of pairwise support and attack relations"
    )
    __configclass__: type[ArtifcatAnalystConfig] = RelevanceNetworkBuilderConfig

    def __init__(self, config: RelevanceNetworkBuilderConfig):
        super().__init__(config)
        self._keep_pcl_valences = config.keep_pcl_valences

    def _unpack_reasons(self, reasons: list[Claim], issue: str) -> list[list[Claim]]:
        """Unpacks all reasons and returns list of unpacked reasons"""

        messages = _MESSAGES_UNPACK_REASONS
        prompt = ChatPromptTemplate.from_messages(messages)
        guided_json = ClaimList.model_json_schema()
        gen_args = {"temperature": 0.4, "json_schema": guided_json}

        # fmt: off
        chain = (
            prompt
            | self._model.bind(**gen_args).with_retry()
            | SimpleJsonOutputParser()
        )
        # fmt: on

        inputs = [
            {
                "formatted_input": format_input({"issue": issue, "title": reason.label, "gist": reason.text}),
                "formatted_examples": format_examples(),
            }
            for reason in reasons
        ]

        result = chain.batch(inputs)

        def safe_cast(claim_data: list[dict]) -> list[Claim]:
            checked_claims: list[Claim] = []
            for data in claim_data:
                if "text" not in data:
                    continue
                if not data["text"]:
                    continue
                if data["text"] in [claim.text for claim in checked_claims]:
                    continue
                if "label" not in data:
                    data["label"] = "-".join(data["text"].strip().split(" ")[:3])
                checked_claims.append(Claim(**data))
            return checked_claims

        return [safe_cast(claim_list) for claim_list in result]

    def _unpack_pros_and_cons(
        self, pros_and_cons: ProsConsList, issue: str
    ) -> tuple[ProsConsList, list[tuple[dict, list[dict]]]]:
        """Unpacks each individual reason in a pros and cons list

        Args:
            pros_and_cons (ProsConsList): pros and cons list with reason to be unpacked
            issue (str): overarching issue addressed by pros and cons

        Returns:
            ProsConsList, unpacking: pros and cons list with unpacked reasons; list of
            tuples with original and unpacked claims
        """

        pros_and_cons = copy.deepcopy(pros_and_cons)
        unpacking = []

        # collect and unpack all reasons in one batch
        reasons = []
        for root in pros_and_cons.roots:
            reasons.extend(root.pros)
            reasons.extend(root.cons)
        unpacked_reasons = self._unpack_reasons(reasons=reasons, issue=issue)
        unpacked_dict = dict(zip(reasons, unpacked_reasons))

        for root in pros_and_cons.roots:
            to_be_added = []
            to_be_removed = []
            for pro in root.pros:
                unpacked_pros = unpacked_dict[pro]
                if len(unpacked_pros) > 1:
                    unpacking.append((pro.model_dump(), [claim.model_dump() for claim in unpacked_pros]))
                    to_be_removed.append(pro)
                    to_be_added.extend(unpacked_pros)
            for pro in to_be_removed:
                root.pros.remove(pro)
            root.pros.extend(to_be_added)
            to_be_added = []
            to_be_removed = []
            for con in root.cons:
                unpacked_cons = unpacked_dict[con]
                if len(unpacked_cons) > 1:
                    unpacking.append((con.model_dump(), [claim.model_dump() for claim in unpacked_cons]))
                    to_be_removed.append(con)
                    to_be_added.extend(unpacked_cons)
            for con in to_be_removed:
                root.cons.remove(con)
            root.cons.extend(to_be_added)

        return pros_and_cons, unpacking

    def _remove_duplicates(self, pros_and_cons: ProsConsList) -> ProsConsList:
        """Remove duplicate reasons from pros and cons list

        This is required becuase in a multi-root pros and cons list,
        one and the same reason may appear under different root claims,
        e.g. as a pro for one root claim and a con for another.
        """

        roots = []
        reasontexts_seen = set()

        for root in pros_and_cons.roots:
            pros = []
            for pro in root.pros:
                if pro.text not in reasontexts_seen:
                    pros.append(pro.model_copy())
                reasontexts_seen.add(pro.text)
            cons = []
            for con in root.cons:
                if con.text not in reasontexts_seen:
                    cons.append(con.model_copy())
                reasontexts_seen.add(con.text)
            roots.append(RootClaim(text=root.text, label=root.label, pros=pros, cons=cons))

        return ProsConsList(roots=roots, options=pros_and_cons.options)

    # the following function calculates the strength of the argumentative relation between two claims
    async def _relation_strength2(
        self,
        source_nodes: list[ArgMapNode],
        target_nodes: list[ArgMapNode],
        valences: Sequence[str | None] | None = None,
        issue: str = "",
    ) -> tuple[list[float], list[str]]:
        """Calculate the valence and strength of argumentative relations

        Calculate the valence and strength of the pairwise argumentative relations
        between two argument map nodes (from source to target).

        Args:
            target_nodes (ArgMapNode): targets
            source_nodes (ArgMapNode): sources
            valences (str, optional): calculate each strength between source and target for corresp. valence

        Returns:
            list[Tuple[float, str]]: list of (strength, valence) pairs
        """

        if len(source_nodes) != len(target_nodes):
            msg = "source_nodes and target_nodes must have the same length"
            raise ValueError(msg)

        if valences is None:
            valences = [None] * len(source_nodes)

        if len(valences) != len(source_nodes):
            msg = "valences must have the same length as source_nodes"
            raise ValueError(msg)

        source_claims = [Claim(label=node.label, text=node.text) for node in source_nodes]
        target_claims = [Claim(label=node.label, text=node.text) for node in target_nodes]

        self.logger.debug("Nodes cast as source_claims: %s ..." % source_claims[:3])
        self.logger.debug("Nodes cast as target_claims: %s ..." % target_claims[:3])

        # step 1: valence probs
        results = await lcel_queries.valence(
            arguments=source_claims,
            claims=target_claims,
            issue=issue,
            model=self._model,
        )

        valences = [
            result.choices[result.idx_max] if valence is None else valence for result, valence in zip(results, valences)
        ]
        self.logger.debug("Valences: %s ..." % valences[:3])

        probs_1 = [result.prob_choice(valence) for result, valence in zip(results, valences)]
        self.logger.debug("Probs_1: %s ..." % probs_1[:3])

        # step 2: strength probs
        partition = {
            am.SUPPORT: [idx for idx, val in enumerate(valences) if val == am.SUPPORT],
            am.ATTACK: [idx for idx, val in enumerate(valences) if val == am.ATTACK],
        }

        coros = [
            lcel_queries.supports_q(
                arguments=[source_claims[idx] for idx in partition[am.SUPPORT]],
                claims=[target_claims[idx] for idx in partition[am.SUPPORT]],
                model=self._model,
            ),
            lcel_queries.attacks_q(
                arguments=[source_claims[idx] for idx in partition[am.ATTACK]],
                claims=[target_claims[idx] for idx in partition[am.ATTACK]],
                model=self._model,
            ),
        ]
        results_partitioned = dict(zip([am.SUPPORT, am.ATTACK], await asyncio.gather(*coros)))
        # merge and sort partitioned results
        # dummy results
        results = [lcel_queries.MultipleChoiceResult(probs={}, label_max="", idx_max=0)] * len(source_nodes)
        for val_key in partition.keys():
            for idx, result in zip(partition[val_key], results_partitioned[val_key]):
                results[idx] = result
        if any(result is None for result in results):
            msg = "Internal error: couldn't merge partitioned results."
            raise ValueError(msg)

        probs_2 = [result.probs["A"] for result in results]
        self.logger.debug("Probs_2: %s ..." % probs_2[:3])

        aggregated_probs = [p * q for p, q in zip(probs_1, probs_2)]

        return aggregated_probs, valences  # type: ignore

    # the following function calculates the strength of the argumentative relation between two claims
    async def _relation_strength(
        self,
        source_nodes: list[ArgMapNode],
        target_nodes: list[ArgMapNode],
        valences: Sequence[str | None] | None = None,
        issue: str = "",
    ) -> tuple[list[float], list[str]]:
        """Calculate the valence and strength of argumentative relations

        Calculate the valence and strength of the pairwise argumentative relations
        between two argument map nodes (from source to target).

        Args:
            target_nodes (ArgMapNode): targets
            source_nodes (ArgMapNode): sources
            valences (str, optional): calculate each strength between source and target for corresp. valence

        Returns:
            list[Tuple[float, str]]: list of (strength, valence) pairs
        """

        if not self._classifier:
            self.logger.warning("No classifier found, using old logic for relation strength calculation.")
            return await self._relation_strength2(source_nodes, target_nodes, valences, issue)

        if len(source_nodes) != len(target_nodes):
            msg = "source_nodes and target_nodes must have the same length"
            raise ValueError(msg)

        if valences is not None and len(valences) != len(source_nodes):
            msg = "valences must have the same length as source_nodes"
            raise ValueError(msg)

        source_claims = [Claim(label=node.label, text=node.text) for node in source_nodes]
        target_claims = [Claim(label=node.label, text=node.text) for node in target_nodes]

        self.logger.debug("Nodes cast as source_claims: %s ..." % source_claims[:3])
        self.logger.debug("Nodes cast as target_claims: %s ..." % target_claims[:3])

        results = await classifier_queries.dialectic_relations(
            arguments=source_claims,
            claims=target_claims,
            classifier=self._classifier,
        )

        if valences is None:
            valences = []
            for mcr in results:
                valence = am.SUPPORT if mcr.probs[am.SUPPORT] > mcr.probs[am.ATTACK] else am.ATTACK
                valences.append(valence)

        strengths: list[float] = []
        for valence, mcr in zip(valences, results):  # type: ignore
            strength = mcr.probs[valence]
            strengths.append(strength)

        return strengths, valences  # type: ignore

    def _dialectically_equivalent(self, relevance_network: FuzzyArgMap, node1: ArgMapNode, node2: ArgMapNode) -> bool:
        """Checks whether two reasons are dialectically equivalent relative to central claims

        If two reasons have common parent central claims, they are dialectically equivalent
        iff they have identical argumentative relations to each common root claim.
        If two reasons have no common root claims, they are dialectically equivalent
        iff one is only supporting and the other only attacking central claims.

        This function is hence assuming that the central claims are mutually exclusive (contrary).

        Args:
            relevance_network (FuzzyArgMap): argmap relative to which dialectic equivalence is assessed
            source_node (ArgMapNode): first node
            target_node (ArgMapNode): second node

        Returns:
            bool: true if two nodes are dialectically equivalent, false otherwise
        """
        # determine parent central claims of two nodes
        node1_parents = {
            edge.target
            for edge in relevance_network.edgelist
            if edge.source == node1.id and relevance_network.get_node_type(edge.target) == am.CENTRAL_CLAIM
        }
        node2_parents = {
            edge.target
            for edge in relevance_network.edgelist
            if edge.source == node2.id and relevance_network.get_node_type(edge.target) == am.CENTRAL_CLAIM
        }

        common_parents = node1_parents.intersection(node2_parents)

        # Case 1: there are common parents
        if len(common_parents) > 0:
            equivalent = True
            for parent in common_parents:
                node1_valence = next(
                    edge.valence
                    for edge in relevance_network.edgelist
                    if edge.source == node1.id and edge.target == parent
                )
                node2_valence = next(
                    edge.valence
                    for edge in relevance_network.edgelist
                    if edge.source == node2.id and edge.target == parent
                )
                if node1_valence != node2_valence:
                    equivalent = False
                    break
            return equivalent

        # Case 2: there are no common parents
        node1_valences = {
            edge.valence
            for edge in relevance_network.edgelist
            if edge.source == node1.id and edge.target in node1_parents
        }
        node2_valences = {
            edge.valence
            for edge in relevance_network.edgelist
            if edge.source == node2.id and edge.target in node2_parents
        }
        equivalent = len(node1_valences.intersection(node2_valences)) == 0

        return equivalent

    def _add_node(self, argmap: FuzzyArgMap, claim: Claim, node_type: str = am.REASON) -> ArgMapNode:
        """Add node to fuzzy argmap

        Args:
            argmap (FuzzyArgMap): fuzzy argmap
            claim (Claim): claim to be added

        Returns:
            ArgMapNode: node added to fuzzy argmap
        """
        node = ArgMapNode(
            id=str(uuid.uuid4()),
            label=claim.label,
            text=claim.text,
            node_type=node_type,
        )
        argmap.nodelist.append(node)
        return node

    async def _add_fuzzy_edges(
        self,
        argmap: FuzzyArgMap,
        source_nodes: list[ArgMapNode],
        target_nodes: list[ArgMapNode],
        valences: Sequence[str | None] | None = None,
        issue: str = "",
    ) -> list[FuzzyArgMapEdge]:
        """Add fuzzy edge to fuzzy argmap

        Args:
            argmap (FuzzyArgMap): fuzzy argmap
            target_node (ArgMapNode): target node
            source_node (ArgMapNode): source node
            valence (str, optional): fixed valence to assume, automatically determines most likely val if None
            issue (str, optional): issue addressed by arguments

        Returns:
            FuzzyArgMapEdge: newly added edge
        """
        self.logger.debug("Measuring relation strength for %s edges..." % len(source_nodes))
        weights, vals = await self._relation_strength(source_nodes, target_nodes, valences=valences, issue=issue)
        edges: list[FuzzyArgMapEdge] = []
        for i in range(len(source_nodes)):
            if valences and valences[i] is not None:
                val = valences[i]
            else:
                val = vals[i]
            w = weights[i]
            source_node = source_nodes[i]
            target_node = target_nodes[i]
            edge = FuzzyArgMapEdge(source=source_node.id, target=target_node.id, valence=val, weight=w)
            argmap.edgelist.append(edge)
            edges.append(edge)
        return edges

    async def _analyze(self, analysis_state: AnalysisState):
        """Build fuzzy argmap from pros and cons.

        Args:
            analysis_state (AnalysisState): current analysis_state to which new artifact is added

        Raises:
            ValueError: Failure to create Fuzzy argument map

        Proceeds as follows:

        1. Unpack each individual pro / con in pros cons list into separate claims (if possible)
        2. Determine reason - root weights for all reasons subsumed under a root claim
        3. Determine reason - reason weights for all reason pairs

        """

        issue = next((a.data for a in analysis_state.artifacts if a.id == "issue"), None)
        if issue is None:
            msg = f"Missing required artifact: issue. Available artifacts: {analysis_state.artifacts!s}"
            raise ValueError(msg)

        pros_and_cons_data = next((a.data for a in analysis_state.artifacts if a.id == "proscons"), None)
        if pros_and_cons_data is None:
            msg = f"Missing required artifact: proscons. Available artifacts: {analysis_state.artifacts!s}"
            raise ValueError(msg)
        try:
            pros_and_cons = ProsConsList(**pros_and_cons_data)
        except Exception as err:
            msg = f"Missing required artifact: issue. Available artifacts: {analysis_state.artifacts!s}"
            raise ValueError(msg) from err

        # unpack individual reasons
        pros_and_cons, unpacking = self._unpack_pros_and_cons(pros_and_cons, issue)
        self.logger.debug(f"Unpacked pros and cons list: {pprint.pformat(pros_and_cons.model_dump())}")

        # remove duplicate reasons
        pros_and_cons = self._remove_duplicates(pros_and_cons)
        self.logger.debug(f"Cleaned pros and cons list w/o duplicates: {pprint.pformat(pros_and_cons.model_dump())}")

        # create fuzzy argmap from fuzzy pros and cons list
        relevance_network = FuzzyArgMap()
        source_nodes = []
        target_nodes = []
        valences: list[str | None] = []
        # add nodes, collect reason-root edges
        self.logger.debug("Adding nodes and collecting reason-root edges...")
        for root in pros_and_cons.roots:
            target_node = self._add_node(relevance_network, root, node_type=am.CENTRAL_CLAIM)
            for pro in root.pros:
                source_node = self._add_node(relevance_network, pro, node_type=am.REASON)
                source_nodes.append(source_node)
                target_nodes.append(target_node)
                valences.append(am.SUPPORT)
            for con in root.cons:
                source_node = self._add_node(relevance_network, con, node_type=am.REASON)
                source_nodes.append(source_node)
                target_nodes.append(target_node)
                valences.append(am.ATTACK)

        # # we add these reason-root edges together with reason reason edges later on
        # self._add_fuzzy_edges(
        #     relevance_network,
        #     source_nodes=source_nodes,
        #     target_nodes=target_nodes,
        #     valences=valences,
        #     issue=issue
        # )

        # collect reason-reason edges
        self.logger.debug("Collecting reason-reason edges...")
        for target_node in relevance_network.nodelist:
            if target_node.node_type == am.CENTRAL_CLAIM:
                continue

            reason_nodes = [
                node for node in relevance_network.nodelist if node.id != target_node.id and node.node_type == am.REASON
            ]
            # TODO: improve naive sampling
            if len(reason_nodes) > MAX_N_RELATIONS:
                reason_nodes = random.sample(reason_nodes, MAX_N_RELATIONS)

            for source_node in reason_nodes:
                valence = None
                if self._keep_pcl_valences:
                    valence = (
                        am.SUPPORT
                        if self._dialectically_equivalent(relevance_network, source_node, target_node)
                        else am.ATTACK
                    )
                source_nodes.append(source_node)
                target_nodes.append(target_node)
                valences.append(valence)

        # add edges
        self.logger.info("Adding %s fuzzy edges edges...", len(source_nodes))
        self.logger.debug("Edges to weigh and add: %s" % list(zip(source_nodes, target_nodes, valences)))
        await self._add_fuzzy_edges(
            relevance_network, source_nodes=source_nodes, target_nodes=target_nodes, valences=valences, issue=issue
        )

        if relevance_network is None:
            self.logger.warning("Failed to build relevance network (relevance_network is None).")

        try:
            relevance_network_data = relevance_network.model_dump()  # type: ignore
        except AttributeError:
            relevance_network_data = relevance_network.model_dump()

        artifact = Artifact(
            id=self.get_product(),
            description=self.get_description(),
            data=relevance_network_data,
            metadata={"unpacking": unpacking},
        )

        analysis_state.artifacts.append(artifact)
