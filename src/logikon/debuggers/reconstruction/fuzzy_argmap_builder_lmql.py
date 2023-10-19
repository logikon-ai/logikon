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
from typing import List, TypedDict, Tuple

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
        ]
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
        ]
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
            }
        ]
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
            }
        ]
    }
]


### FORMATTERS ###


def format_reason(reason: Claim, max_len: int = -1) -> str:
    label_text = f"[{reason.label}]: {reason.text}"
    if max_len > 0 and len(label_text) > max_len:
        label_text = label_text[:max_len] + "..."
    return f"- \"{label_text}\"\n"


def format_proscons(issue: str, proscons: ProsConsList) -> str:
    formatted = "```yaml\n"
    # reasons block
    formatted += "reasons:\n"
    reasons = []
    for root in proscons.roots:
        reasons.extend(root.pros)
        reasons.extend(root.cons)
    reasons = random.Random(42).sample(reasons, min(len(reasons), MAX_N_REASONS))
    for reason in reasons:
        formatted += format_reason(reason)
    # issue
    formatted += f"issue: \"{issue}\"\n"
    # pros and cons block
    formatted += "pros_and_cons:\n"
    for root in proscons.roots:
        formatted += f"- root: \"({root.label}): {root.text}\"\n"
        formatted += "  pros:\n"
        for pro in root.pros:
            formatted += f"  - \"[{pro.label}]\"\n"
        formatted += "  cons:\n"
        for con in root.cons:
            formatted += f"  - \"[{con.label}]\"\n"
    formatted += "```\n"
    return formatted

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
def unpack_reason(reason_data: dict, issue: str) -> List[Claim]:
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


    def ensure_unique_labels(self, reasons: List[Claim]) -> List[Claim]:
        """Revises labels of reasons to ensure uniqueness

        Args:
            reasons (List[Claim]): list of reasons

        Returns:
            List[Claim]: list of reasons with unique labels
        """

        labels = [reason.label for reason in reasons]
        duplicate_labels = [label for label in labels if labels.count(label) > 1]
        if not duplicate_labels:
            return reasons

        unique_reasons = copy.deepcopy(reasons)
        for reason in unique_reasons:
            if reason.label in duplicate_labels:
                i = 1
                new_label = f"{reason.label}-{str(i)}"
                while new_label in labels:
                    if i >= MAX_N_REASONS:
                        self.logger.warning("Failed to ensure unique labels for reasons.")
                        break
                    i += 1
                    new_label = f"{reason.label}-{str(i)}"
                reason.label = new_label

        return unique_reasons


    def unpack_reasons(self, pros_and_cons: ProsConsList, issue: str) -> ProsConsList:
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
    def _relation_strength(self, target_claim: Claim, source_claim: Claim, valence: str = "") -> Tuple[float, str]:
        """calculate the strength of the argumentative relation between two claims

        Args:
            target_claim (Claim): _description_
            source_claim (Claim): _description_
            valence (str, optional): calculate strength between source and target for this valence

        Returns:
            Tuple[float, str]: strength and valence
        """

    @staticmethod
    def _add_node(map: FuzzyArgMap, claim: Claim, type: str = REASON) -> ArgMapNode:
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
            type=type,
        )
        map.nodelist.append(node)
        return node


    def _debug(self, debug_state: DebugState):
        """Build fuzzy argmap from pros and cons.

        Args:
            debug_state (DebugState): current debug_state to which new artifact is added

        Raises:
            ValueError: Failure to create Fuzzy argument map

        Proceeds as follows:

        1. Unpack each individual pro / con in pros cons list into separate claims (if possible)


        """

        issue = next((a.data for a in debug_state.artifacts if a.id == "issue"), None)
        if issue is None:
            raise ValueError("Missing required artifact: issue. Available artifacts: " + str(debug_state.artifacts))

        pros_and_cons = next((a.data for a in debug_state.artifacts if a.id == "proscons"), None)
        if pros_and_cons is None:
            raise ValueError("Missing required artifact: proscons. Available artifacts: " + str(debug_state.artifacts))

        # unpack individual reasons
        pros_and_cons = self.unpack_reasons(pros_and_cons, issue)
        self.logger.info(f"Unpacked pros and cons list: {pprint.pformat(pros_and_cons.dict())}")

        # create fuzzy argmap from fuzzy pros and cons list (reason-root edges)
        fuzzy_argmap = FuzzyArgMap()
        for root in pros_and_cons.roots:
            # add root node
            target_node = self._add_node(fuzzy_argmap, root, type=CENTRAL_CLAIM)
            for pro in root.pros:
                # add pro reason node
                source_node = self._add_node(fuzzy_argmap, pro)
                # add fuzzy reason-root edges
                w, _ = self._relation_strength(root, pro, valence=SUPPORT)
                edge = FuzzyArgMapEdge(source=source_node.id, target=target_node.id, valence=SUPPORT, weight=w)
                fuzzy_argmap.edgelist.append(edge)
            for con in root.cons:
                # add con reason node
                source_node = self._add_node(fuzzy_argmap, con)
                # add fuzzy reason-root edges
                w, _ = self._relation_strength(root, con, valence=ATTACK)
                edge = FuzzyArgMapEdge(source=source_node.id, target=target_node.id, valence=ATTACK, weight=w)
                fuzzy_argmap.edgelist.append(edge)

        # add fuzzy reason-reason edges









        if pros_and_cons is None:
            self.logger.warning("Failed to build pros and cons list (pros_and_cons is None).")

        try:
            pros_and_cons_data = pros_and_cons.model_dump()  # type: ignore
        except AttributeError:
            pros_and_cons_data = pros_and_cons.dict()

        artifact = Artifact(
            id=self.get_product(),
            description=self.get_description(),
            data=pros_and_cons_data,
        )

        debug_state.artifacts.append(artifact)
