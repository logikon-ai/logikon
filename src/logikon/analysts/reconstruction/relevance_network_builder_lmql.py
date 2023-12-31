"""Module with analyst for building a fuzzy (informal) argument map with LMQL

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

import copy
import pprint
import random
import uuid
from typing import ClassVar

import lmql
import tqdm

import logikon.schemas.argument_mapping as am
from logikon.analysts import lmql_queries
from logikon.analysts.base import ArtifcatAnalystConfig
from logikon.analysts.lmql_analyst import LMQLAnalyst, LMQLAnalystConfig
from logikon.schemas.argument_mapping import ArgMapNode, FuzzyArgMap, FuzzyArgMapEdge
from logikon.schemas.pros_cons import Claim, ProsConsList
from logikon.schemas.results import AnalysisState, Artifact
from logikon.utils.prompt_templates_registry import PromptTemplate  # noqa: F401

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
        "claims": [
            {
                "title": "Climate impact",
                "claim": "Animal farming contributes to climate change.",
            },
            {
                "title": "High energy consumption",
                "claim": "Animal farming is extremely energy intensive.",
            },
            {
                "title": "Land use change",
                "claim": "Animal farming causes the degradation of natural carbon sinks through land use change.",
            },
        ],
    },
    {
        "issue": "Should Bullfighting be Banned?",
        "title": "Economic benefit",
        "gist": "Bullfighting can benefit national economies with an underdeveloped industrial base.",
        "claims": [
            {
                "title": "Economic benefit",
                "claim": "Bullfighting can benefit national economies with an underdeveloped industrial base.",
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
        "claims": [
            {
                "title": "Toxic communities",
                "claim": "Many video gaming communities are widely regarded as toxic.",
            },
            {
                "title": "Opportunities for abuse",
                "claim": "Online games create opportunities for players to stalk and abuse each other.",
            },
        ],
    },
    {
        "issue": "Pick best draft",
        "title": "Readability",
        "gist": "Draft 1 is easier to read and much more funny than the other drafts.",
        "claims": [
            {
                "title": "Readability",
                "claim": "Draft 1 is easier to read than the other drafts.",
            },
            {
                "title": "Engagement",
                "claim": "Draft 1 is much more funny than the other drafts.",
            },
        ],
    },
]


### FORMATTERS ###


def format_example(example_data: dict) -> str:
    formatted = "```yaml\n"
    formatted += "argumentation:\n"
    formatted += f"  issue: \"{example_data['issue']}\"\n"
    formatted += f"  title: \"{example_data['title']}\"\n"
    formatted += f"  gist: \"{example_data['gist']}\"\n"
    # claims block
    formatted += "reasons:\n"
    for claim in example_data["claims"]:
        formatted += f"  - title: \"{claim['title']}\"\n"
        formatted += f"    reason: \"{claim['claim']}\"\n"
    formatted += "```\n"
    return formatted


def format_examples() -> str:
    formatted = [format_example(example) for example in EXAMPLES_UNPACKING]
    formatted = ["<example>\n" + example + "</example>" for example in formatted]
    formatted_s = "\n".join(formatted)
    return formatted_s


### LMQL QUERIES ###


@lmql.query
def unpack_reason(reason_data: dict, issue: str, prmpt_data: dict) -> list[Claim]:  # type: ignore  # noqa: ARG001
    '''lmql
    sample(temperature=.3, chunksize=10)
        reason = Claim(**reason_data)
        prmpt = PromptTemplate(**prmpt_data)
        """
        {prmpt.sys_start}
        {lmql_queries.system_prompt()}{prmpt.sys_end}

        {prmpt.user_start}
        Your Assignment: Unpack the individual reasons contained in an argumentation.

        Use the following inputs (the title and gist of an argumentation that addresses an issue) to solve your assignment.

        <inputs>
        <issue>{issue}</issue>
        <argumentation>
        <title>{reason.label}</title>
        <gist>{reason.text}</gist>
        </argumentation>
        </inputs>

        What are the basic reasons contained in this argumentation?

        Let me give you more detailed instructions:

        - Read the gist carefully and extract all individual reasons it sets forth.
        - State each reason clearly in simple and plain language.
        - Each individual reason should be self-contained and unambiguous; avoid in particular anaphora and other context-dependent references (such as "it", "that", "this", "the previous", ...).
        - The basic reason-statements you extract must themselves not contain any reasoning (as indicated, e.g., by "because", "since", "therefore" ...).
        - State every reason in one grammatically correct sentence, staying close to the original wording. Provide a distinct title, too. I.e.:
            ```
            argumentation:
              issue: "repeat argumentation issue"
              title: "repeat argumentation title"
              gist: "repeat argumentation gist"
              reasons:
              - title: "first reason title"
                reason: "state first reason in one sentence."
              - ...
            ```
        - The individual reasons you extract may mutually support each other, or represent independent reasons for one and the same conclusion; yet such argumentative relations need not be recorded (at this point).
        - If the argumentation gist contains a single reason, just include that very reason in your list.
        - Feel free to improve (e.g., shorten) the title(s).
        - Avoid repeating one and the same reason in different words.
        - IMPORTANT: Stay faithful to the gist! Don't invent your own reasons. Don't uncover implicit assumptions. Only provide reasons which are explicitly contained in the gist.
        - Use yaml syntax and "```" code fences to structure your answer.

        I'll give you a few examples that illustrate the task.

        {format_examples()}

        Please, process the above inputs and unpack the individual reasons contained in the argumentation.{prmpt.user_end}
        {prmpt.ass_start}
        The argumentation contains the following basic reasons:

        ```yaml
        argumentation:
          issue: "{issue}"
          title: "{reason.label}"
          gist: "{reason.text}"
          reasons:"""
        claims = []
        marker = ""
        n = 0
        while n<10:
            n += 1
            "[MARKER]" where MARKER in set(["\n```", "\n  - "])
            marker = MARKER
            if marker == "\n```":
                break
            else:
                "title: \"[TITLE]" where STOPS_AT(TITLE, "\"") and STOPS_AT(TITLE, "\n") and len(TITLE) < MAX_LEN_TITLE
                if not TITLE.endswith('\"'):
                    "\" "
                title = TITLE.strip('\"')
                "\n    reason: \"[CLAIM]" where STOPS_AT(CLAIM, "\"") and STOPS_AT(CLAIM, "\n") and len(CLAIM) < MAX_LEN_GIST
                if not CLAIM.endswith('\"'):
                    "\" "
                claim = CLAIM.strip('\"')
                claims.append(Claim(label=title, text=claim))
        return claims

    '''


class RelevanceNetworkBuilderConfig(LMQLAnalystConfig):
    """RelevanceNetworkBuilderConfig

    Configuration for RelevanceNetworkBuilder.

    Fields:
        keep_pcl_valences (bool): keep (i.e. don't revise) global valences from pros and cons list
    """

    keep_pcl_valences: bool = True


class RelevanceNetworkBuilderLMQL(LMQLAnalyst):
    """RelevanceNetworkBuilderLMQL

    This LMQLAnalyst is responsible for creating a relevance network,
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

    def _unpack_reason(self, reason_data: dict, issue: str) -> list[Claim]:
        """Internal (class method) wrapper for lmql query function."""
        return unpack_reason(
            reason_data=reason_data,
            issue=issue,
            prmpt_data=self._prompt_template.to_dict(),
            model=self._model,
            **self._generation_kwargs,
        )

    def _unpack_reasons(
        self, pros_and_cons: ProsConsList, issue: str
    ) -> tuple[ProsConsList, list[tuple[dict, list[dict]]]]:
        """Unpacks each individual reason in a pros and cons list

        Args:
            pros_and_cons (ProsConsList): pros and cons list with reason to be unpacked
            issue (str): overarching issue addressed by pros and cons

        Returns:
            ProsConsList, unpacking: pros and cons list with unpacked reasons; list of tuples with original and unpacked claims
        """

        pros_and_cons = copy.deepcopy(pros_and_cons)
        unpacking = []

        for root in pros_and_cons.roots:
            to_be_added = []
            to_be_removed = []
            for pro in root.pros:
                unpacked_pros = self._unpack_reason(reason_data=pro.dict(), issue=issue)
                if len(unpacked_pros) > 1:
                    unpacking.append((pro.dict(), [claim.dict() for claim in unpacked_pros]))
                    to_be_removed.append(pro)
                    to_be_added.extend(unpacked_pros)
            for pro in to_be_removed:
                root.pros.remove(pro)
            root.pros.extend(to_be_added)
            to_be_added = []
            to_be_removed = []
            for con in root.cons:
                unpacked_cons = self._unpack_reason(reason_data=con.dict(), issue=issue)
                if len(unpacked_cons) > 1:
                    unpacking.append((con.dict(), [claim.dict() for claim in unpacked_cons]))
                    to_be_removed.append(con)
                    to_be_added.extend(unpacked_cons)
            for con in to_be_removed:
                root.cons.remove(con)
            root.cons.extend(to_be_added)

        return pros_and_cons, unpacking

    # the following function calculates the strength of the argumentative relation between tow claims
    def _relation_strength(
        self, source_node: ArgMapNode, target_node: ArgMapNode, valence: str | None = None, issue: str = ""
    ) -> tuple[float, str]:
        """Calculate the valence and strength of an argumentative relation

        Calculate the valence and strength of the argumentative relation between two
        argument map nodes (from source to target).

        Args:
            target_node (ArgMapNode): target
            source_node (ArgMapNode): source
            valence (str, optional): calculate strength between source and target for this valence

        Returns:
            Tuple[float, str]: strength, valence
        """

        # step 1: valence probs
        lmql_result = lmql_queries.valence(
            {"label": source_node.label, "text": source_node.text},
            {"label": target_node.label, "text": target_node.text},
            issue=issue,
            prmpt_data=self._prompt_template.to_dict(),
            model=self._model,
            **self._generation_kwargs,
        )
        # self.logger.debug(f"Eliciting valence with lmql query: '{lmql_result.prompt}'")
        if valence is None:
            valence = lmql_queries.label_to_valence(lmql_result.variables[lmql_result.distribution_variable])
        prob_1 = next(
            prob
            for label, prob in lmql_queries.get_distribution(lmql_result)
            if lmql_queries.label_to_valence(label) == valence
        )

        # step 2: strength probs
        query_fn = lmql_queries.supports_q if valence == am.SUPPORT else lmql_queries.attacks_q
        lmql_result = query_fn(
            {"label": source_node.label, "text": source_node.text},
            {"label": target_node.label, "text": target_node.text},
            prmpt_data=self._prompt_template.to_dict(),
            model=self._model,
            **self._generation_kwargs,
        )
        prob_2 = next(prob for label, prob in lmql_queries.get_distribution(lmql_result) if label == "A")

        return prob_1 * prob_2, valence

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

    def _add_fuzzy_edge(
        self,
        argmap: FuzzyArgMap,
        source_node: ArgMapNode,
        target_node: ArgMapNode,
        valence: str | None = None,
        issue: str = "",
    ) -> FuzzyArgMapEdge:
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
        w, val = self._relation_strength(source_node, target_node, valence=valence, issue=issue)
        if valence is not None:
            val = valence
        edge = FuzzyArgMapEdge(source=source_node.id, target=target_node.id, valence=val, weight=w)
        argmap.edgelist.append(edge)
        return edge

    def _analyze(self, analysis_state: AnalysisState):
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
        pros_and_cons, unpacking = self._unpack_reasons(pros_and_cons, issue)
        self.logger.debug(f"Unpacked pros and cons list: {pprint.pformat(pros_and_cons.dict())}")

        # create fuzzy argmap from fuzzy pros and cons list (reason-root edges)
        relevance_network = FuzzyArgMap()
        for root in tqdm.tqdm(pros_and_cons.roots, desc="Reason-root edges"):
            target_node = self._add_node(relevance_network, root, node_type=am.CENTRAL_CLAIM)
            for pro in root.pros:
                source_node = self._add_node(relevance_network, pro, node_type=am.REASON)
                self._add_fuzzy_edge(
                    relevance_network, source_node=source_node, target_node=target_node, valence=am.SUPPORT, issue=issue
                )
            for con in root.cons:
                source_node = self._add_node(relevance_network, con, node_type=am.REASON)
                self._add_fuzzy_edge(
                    relevance_network, source_node=source_node, target_node=target_node, valence=am.ATTACK, issue=issue
                )

        # TODO: improve naive sampling
        # add fuzzy reason-reason edges
        for target_node in tqdm.tqdm(relevance_network.nodelist, desc="Reason-reason edges"):
            if target_node.node_type == am.CENTRAL_CLAIM:
                continue

            source_nodes = [
                node for node in relevance_network.nodelist if node.id != target_node.id and node.node_type == am.REASON
            ]
            if len(source_nodes) > MAX_N_RELATIONS:
                source_nodes = random.sample(source_nodes, MAX_N_RELATIONS)

            for source_node in source_nodes:
                valence = None
                if self._keep_pcl_valences:
                    valence = (
                        am.SUPPORT
                        if self._dialectically_equivalent(relevance_network, source_node, target_node)
                        else am.ATTACK
                    )
                self._add_fuzzy_edge(
                    relevance_network, source_node=source_node, target_node=target_node, valence=valence
                )

        if relevance_network is None:
            self.logger.warning("Failed to build relevance network (relevance_network is None).")

        try:
            relevance_network_data = relevance_network.model_dump()  # type: ignore
        except AttributeError:
            relevance_network_data = relevance_network.dict()

        artifact = Artifact(
            id=self.get_product(),
            description=self.get_description(),
            data=relevance_network_data,
            metadata={"unpacking": unpacking},
        )

        analysis_state.artifacts.append(artifact)
