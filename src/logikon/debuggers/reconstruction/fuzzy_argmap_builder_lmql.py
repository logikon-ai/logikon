"""Module with debugger for building a fuzzy (informal) argument map with LMQL

```mermaid
flowchart TD
    p["`prompt`"]
    c["`completion`"]
    i["`issue`"]
    r["`reasons (unstructured)`"]
    pcl["`pros cons list`"]
    ur["`reasons (unused)`"]
    rm("`reason mining
    >_reasons_`")
    pco("`pros cons organizing
    >_pros cons list_`")
    add("`add unused reasons
    >_pros cons list_`")
    cr("`check and revise
    >_pros cons list_`")
    subgraph artifact
    ad["`data`"]
    am["`metadata`"]
    end
    p --> rm
    c --> rm
    i --> rm
    rm --> r --> am
    i --> pco
    r --> pco --> add --> pco
    i --> cr
    pco --> cr --> pcl --> ad
    pco --> ur --> am
```

"""

from __future__ import annotations
from typing import List, Tuple, Optional

import copy
import functools as ft
import pprint
import random
import uuid

import lmql

from logikon.debuggers.reconstruction.lmql_debugger import LMQLDebugger
import logikon.debuggers.reconstruction.lmql_queries as lmql_queries
from logikon.schemas.results import Artifact, DebugState
from logikon.schemas.pros_cons import ProsConsList, RootClaim, Claim
from logikon.schemas.argument_mapping import FuzzyArgMap, FuzzyArgMapEdge, ArgMapNode

from logikon.schemas.argument_mapping import ATTACK, SUPPORT, REASON, CENTRAL_CLAIM

MAX_N_REASONS = 50
MAX_N_ROOTS = 10
MAX_LEN_TITLE = 32
MAX_LEN_GIST = 180
N_DRAFTS = 3
LABELS = "ABCDEFG"

### EXAMPLES ###


EXAMPLES_UNPACKING = [
    {
        "issue": "Eating animals?",
        "title": "Climate impact",
        "gist": "Animal farming contributes to climate change because it is extremely energy intensive and causes the degradation of natural carbon sinks through land use change.",
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
        "gist": "Many video gaming communities are widely regarded as toxic since online games create opportunities for players to stalk and abuse each other.",
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
    formatted += "claims:\n"
    for claim in example_data['claims']:
        formatted += f"  - title: \"{claim['title']}\"\n"
        formatted += f"    claim: \"{claim['claim']}\"\n"
    formatted += "```\n"
    return formatted


def format_examples() -> str:
    formatted = [format_example(example) for example in EXAMPLES_UNPACKING]
    formatted = ["<example>\n" + example + "</example>" for example in formatted]
    formatted_s = "\n".join(formatted)
    return formatted_s


### LMQL QUERIES ###


@lmql.query
def unpack_reason(reason_data: dict, issue: str) -> List[Claim]:  # type: ignore
    '''lmql
    sample(temperature=.4, top_k=100, top_p=0.95)
        reason = Claim(**reason_data)
        """
        {lmql_queries.system_prompt()}

        ### User

        Your Assignment: Unpack the individual claims contained in an argumentation.

        Use the following inputs (the title and gist of an argumentation that addresses an issue) to solve your assignment.

        <inputs>
        <issue>{issue}</issue>
        <argumentation>
        <title>{reason.label}</title>
        <gist>{reason.text}</gist>
        </argumentation>
        </inputs>

        What are the individual claims and basic reasons contained in this argumentation?

        Let me give you more detailed instructions:

        - Read the gist carefully and extract all individual claims it sets forth.
        - State each claim clearly in simple and plain language.
        - The basic claims you extract must not contain any reasoning (as indicated, e.g., by "because", "since", "therefore" ...).
        - For each argumentation, state all the claims it makes in one grammatically correct sentences, staying close to the original wording. Provide a distinct title, too. I.e.:
            ```
            argumentation:
              issue: "repeat argumentation issue"
              title: "repeat argumentation title"
              gist: "repeat argumentation gist"
              claims:
              - title: "first claim title"
                claim: "state first claim in one sentence."
              - ...
            ```
        - The individual claims you extract may mutually support each other, or represent independent reasons for one and the same conclusion; yet such argumentative relations need not be recorded (at this point).
        - If the argumentation gist contains a single claim, just include that very claim in your list.
        - Avoid repeating one and the same claim in different words.
        - IMPORTANT: Stay faithful to the gist! Don't invent your own claims. Don't uncover implicit assumptions. Only provide claims which are explicitly contained in the gist.
        - Use yaml syntax and "```" code fences to structure your answer.

        I'll give you a few examples that illustrate the task.

        {format_examples()}

        Please, process the above inputs and unpack the individual claims contained in the argumentation.

        ### Assistant

        The argumentation makes the following basic claims:

        ```yaml
        argumentation:
          issue: "{issue}"
          title: "{reason.label}"
          gist: "{reason.text}"
          claims:"""
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
                "\n    claim: \"[CLAIM]" where STOPS_AT(CLAIM, "\"") and STOPS_AT(CLAIM, "\n") and len(CLAIM) < MAX_LEN_GIST
                if not CLAIM.endswith('\"'):
                    "\" "
                claim = CLAIM.strip('\"')
                claims.append(Claim(label=title, text=claim))
        return claims

    '''


class FuzzyArgMapBuilderLMQL(LMQLDebugger):
    """ProsConsBuilderLMQL

    This LMQLDebugger is responsible for creating a fuzzy argument map from a pros and cons list and a given issue.

    """

    __product__ = "fuzzy_argmap"
    __requirements__ = ["issue", "proscons"]
    __pdescription__ = "Fuzzy argument map with weighted support and attack relations"

    def _unpack_reasons(self, pros_and_cons: ProsConsList, issue: str) -> ProsConsList:
        """Unpacks each individual reason in a pros and cons list

        Args:
            pros_and_cons (ProsConsList): pros and cons list with reason to be unpacked
            issue (str): overarching issue addressed by pros and cons

        Returns:
            ProsConsList: pros and cons list with unpacked reasons
        """
        pros_and_cons = copy.deepcopy(pros_and_cons)
        for root in pros_and_cons.roots:
            to_be_added = []
            to_be_removed = []
            for pro in root.pros:
                unpacked_pros = unpack_reason(
                    reason_data=pro.dict(), issue=issue, model=self._model, **self._generation_kwargs
                )
                if len(unpacked_pros) > 1:
                    to_be_removed.append(pro)
                    to_be_added.extend(unpacked_pros)
            for pro in to_be_removed:
                root.pros.remove(pro)
            root.pros.extend(to_be_added)
            to_be_added = []
            to_be_removed = []
            for con in root.cons:
                unpacked_cons = unpack_reason(
                    reason_data=con.dict(), issue=issue, model=self._model, **self._generation_kwargs
                )
                if len(unpacked_cons) > 1:
                    to_be_removed.append(con)
                    to_be_added.extend(unpacked_cons)
            for con in to_be_removed:
                root.cons.remove(con)
            root.cons.extend(to_be_added)

        return pros_and_cons

    # the following function calculates the strength of the argumentative relation between tow claims
    def _relation_strength(
        self, source_node: ArgMapNode, target_node: ArgMapNode, valence: Optional[str] = None
    ) -> Tuple[float, str]:
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
            dict(label=source_node.label, text=source_node.text),
            dict(label=target_node.label, text=target_node.text),
            model=self._model,
            **self._generation_kwargs,
        )
        if valence is None:
            valence = lmql_queries.label_to_valence(lmql_result.variables[lmql_result.distribution_variable])
        prob_1 = next(
            prob
            for label, prob in lmql_queries.get_distribution(lmql_result)
            if lmql_queries.label_to_valence(label) == valence
        )

        # step 2: strength probs
        query_fn = lmql_queries.supports_q if valence == SUPPORT else lmql_queries.attacks_q
        lmql_result = query_fn(
            dict(label=source_node.label, text=source_node.text),
            dict(label=target_node.label, text=target_node.text),
            model=self._model,
            **self._generation_kwargs,
        )
        prob_2 = next(prob for label, prob in lmql_queries.get_distribution(lmql_result) if label == "A")

        return prob_1 * prob_2, valence

    def _add_node(self, map: FuzzyArgMap, claim: Claim, type: str = REASON) -> ArgMapNode:
        """Add node to fuzzy argmap

        Args:
            map (FuzzyArgMap): fuzzy argmap
            claim (Claim): claim to be added

        Returns:
            ArgMapNode: node added to fuzzy argmap
        """
        node = ArgMapNode(
            id=str(uuid.uuid4()),
            label=claim.label,
            text=claim.text,
            nodeType=type,
        )
        map.nodelist.append(node)
        return node

    def _add_fuzzy_edge(
        self, map: FuzzyArgMap, source_node: ArgMapNode, target_node: ArgMapNode, valence: Optional[str] = None
    ) -> FuzzyArgMapEdge:
        """Add fuzzy edge to fuzzy argmap

        Args:
            map (FuzzyArgMap): fuzzy argmap
            target_node (ArgMapNode): target node
            source_node (ArgMapNode): source node
            valence (str, optional): fixed valence to assume, automatically determines most likely val if None

        Returns:
            FuzzyArgMapEdge: newly added edge
        """
        w, val = self._relation_strength(source_node, target_node, valence=valence)
        if valence is not None:
            val = valence
        edge = FuzzyArgMapEdge(source=source_node.id, target=target_node.id, valence=val, weight=w)
        map.edgelist.append(edge)
        return edge

    def _debug(self, debug_state: DebugState):
        """Build fuzzy argmap from pros and cons.

        Args:
            debug_state (DebugState): current debug_state to which new artifact is added

        Raises:
            ValueError: Failure to create Fuzzy argument map

        Proceeds as follows:

        1. Unpack each individual pro / con in pros cons list into separate claims (if possible)
        2. Determine reason - root weights for all reasons subsumed under a root claim
        3. Determine reason - reason weights for all reason pairs

        """

        issue = next((a.data for a in debug_state.artifacts if a.id == "issue"), None)
        if issue is None:
            raise ValueError("Missing required artifact: issue. Available artifacts: " + str(debug_state.artifacts))

        pros_and_cons_data = next((a.data for a in debug_state.artifacts if a.id == "proscons"), None)
        if pros_and_cons_data is None:
            raise ValueError("Missing required artifact: proscons. Available artifacts: " + str(debug_state.artifacts))
        try:
            pros_and_cons = ProsConsList(**pros_and_cons_data)
        except:
            raise ValueError(f"Failed to parse pros and cons list: {pros_and_cons_data}")

        # unpack individual reasons
        pros_and_cons = self._unpack_reasons(pros_and_cons, issue)
        self.logger.info(f"Unpacked pros and cons list: {pprint.pformat(pros_and_cons.dict())}")

        # create fuzzy argmap from fuzzy pros and cons list (reason-root edges)
        fuzzy_argmap = FuzzyArgMap()
        for root in pros_and_cons.roots:
            target_node = self._add_node(fuzzy_argmap, root, type=CENTRAL_CLAIM)
            for pro in root.pros:
                source_node = self._add_node(fuzzy_argmap, pro, type=REASON)
                self._add_fuzzy_edge(fuzzy_argmap, source_node=source_node, target_node=target_node, valence=SUPPORT)
            for con in root.cons:
                source_node = self._add_node(fuzzy_argmap, con, type=REASON)
                self._add_fuzzy_edge(fuzzy_argmap, source_node=source_node, target_node=target_node, valence=ATTACK)

        # add fuzzy reason-reason edges
        for target_node in fuzzy_argmap.nodelist:
            for source_node in fuzzy_argmap.nodelist:
                if source_node.id == target_node.id:
                    continue
                if source_node.nodeType == CENTRAL_CLAIM or target_node.nodeType == CENTRAL_CLAIM:
                    continue
                self._add_fuzzy_edge(fuzzy_argmap, source_node=source_node, target_node=target_node)

        if fuzzy_argmap is None:
            self.logger.warning("Failed to build fuzzy argument map (fuzzy_argmap is None).")

        try:
            fuzzy_argmap_data = fuzzy_argmap.model_dump()  # type: ignore
        except AttributeError:
            fuzzy_argmap_data = fuzzy_argmap.dict()

        artifact = Artifact(
            id=self.get_product(),
            description=self.get_description(),
            data=fuzzy_argmap_data,
        )

        debug_state.artifacts.append(artifact)
