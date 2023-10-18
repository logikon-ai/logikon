"""Module with debugger for building a pros & cons list with LMQL"""

from __future__ import annotations
from typing import List, TypedDict

import copy
import functools as ft
import random
import uuid

import lmql

from logikon.debuggers.reconstruction.lmql_debugger import LMQLDebugger
import logikon.debuggers.reconstruction.lmql_queries as lmql_queries
from logikon.schemas.results import Artifact, DebugState
from logikon.schemas.pros_cons import ProsConsList, RootClaim, Claim

MAX_N_REASONS = 50
MAX_N_ROOTS = 10
MAX_LEN_TITLE = 32
MAX_LEN_GIST = 180
N_DRAFTS = 3
LABELS = "ABCDEFG"

### EXAMPLES ###

EXAMPLES_ISSUE_PROSCONS = [
    (
        "Bullfighting?",
        ProsConsList(
            roots=[
                RootClaim(
                    label="(Bullfighting ban)",
                    text="Bullfighting should be banned.",
                    pros=[
                        Claim(
                            label="[[Cruelty]]",
                            text="Bullfighting is cruelty for the purpose of entertainment."
                        )
                    ],
                    cons=[
                        Claim(
                            label="[[Economic benefits]]",
                            text="Bullfighting may benefit national economies."
                        ),
                        Claim(
                            label="[[Cultural value]]",
                            text="Bullfighting is part of history and local cultures."
                        )
                    ]
                )
            ]
        )
    ),
    (
        "Our next holiday",
        ProsConsList(
            roots=[
                RootClaim(
                    label="(New York)",
                    text="Let's spend our next holiday in New York.",
                    pros=[
                        Claim(
                            label="[[Culture]]",
                            text="New York has incredible cultural events to offer."
                        )
                    ],
                    cons=[
                        Claim(
                            label="[[Costs]]",
                            text="Spending holidays in a big city is too expensive."
                        )
                    ]
                ),
                RootClaim(
                    label="(Florida)",
                    text="Let's spend our next holiday in Florida.",
                    pros=[
                        Claim(
                            label="[[Swimming]]",
                            text="Florida has wonderful beaches and a warm ocean."
                        )
                    ],
                    cons=[]
                ),
                RootClaim(
                    label="(Los Angeles)",
                    text="Let's spend our next holiday in Los Angeles.",
                    pros=[],
                    cons=[
                        Claim(
                            label="[[No Novelty]]",
                            text="We've been in Los Angeles last year."
                        )
                    ]
                )
            ]
        )
    ),
    (
        "Pick best draft",
        ProsConsList(
            roots=[
                RootClaim(
                    label="(Draft-1)",
                    text="Draft-1 is the best draft.",
                    pros=[
                        Claim(
                            label="[[Readability]]",
                            text="Draft-1 is easier to read than the other drafts."
                        ),
                        Claim(
                            label="[[Engagement]]",
                            text="Draft-1 is much more funny than the other drafts."
                        )
                    ],
                    cons=[]
                )
            ]
        )
    ),
]



### FORMATTERS ###

def format_reason(reason: Claim) -> str:
    return f"- \"[[{reason.label}]]: {reason.text}\"\n"

def format_proscons(issue: str, proscons: ProsConsList) -> str:
    formatted = "```yaml\n"
    # reasons block
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
            formatted += f"  - \"[[{pro.label}]]\"\n"
        formatted += "  cons:\n"
        for con in root.cons:
            formatted += f"  - \"[[{con.label}]]\"\n"
    formatted += "```"
    return formatted


### LMQL QUERIES ###

@lmql.query
def mine_reasons(prompt, completion, issue) -> List[Claim]:  # type: ignore
    '''lmql
    sample(temperature=.4)
        """
        {lmql_queries.system_prompt()}

        ### User

        Your Assignment: Summarize all the arguments (pros and cons) presented in a text.

        Use the following inputs (a TEXT that addresses an ISSUE) to solve your assignment.

        <TEXT>
        {prompt}{completion}
        </TEXT>

        <ISSUE>
        {issue}
        </ISSUE>

        What are the TEXT's arguments (pros and cons) that address the ISSUE?
        
        Let me give you more detailed instructions:

        - Go through the text from beginning to end and extract all arguments in the order of appearance.
        - For each argument, sketch the argument's gist in one or two grammatically correct sentences, staying close to the original wording, and provide a telling title (2-4 words). I.e.:
            ```
            - title: "a very short title"
              gist: "the argument's gist in 1-2 sentences."
            ```
        - Avoid repeating one and the same argument in different words.
        - You don't have to distinguish between pro and con arguments.
        - IMPORTANT: Stay faithful to the text! Don't invent your own reasons. Only provide reasons which are either presented or discussed in the text.
        - Use yaml syntax and "```" code fences to structure your answer.

        ### Assistant
        
        The TEXT sets forth the following arguments:

        ```yaml
        arguments:"""
        reasons = []
        marker = ""
        n = 0
        while n<MAX_N_REASONS:
            n += 1
            "[MARKER]" where MARKER in set(["\n```", "\n- "])
            marker = MARKER
            if marker == "\n```":
                break
            else:
                "title: \"[TITLE]" where STOPS_AT(TITLE, "\"") and len(TITLE) < MAX_LEN_TITLE
                if not TITLE.endswith('\"'):
                    "\" "
                title = TITLE.strip('\"')
                "\n  gist: \"[GIST]" where STOPS_AT(GIST, "\"") and len(GIST) < MAX_LEN_GIST
                if not GIST.endswith('\"'):
                    "\" "
                gist = GIST.strip('\"')
                reasons.append(Claim(label=title, text=gist))
        return reasons
    '''

#@lmql.query
#def get_roots(reasons, issue):
#    '''lmql
#    "reasons:\n"
#    for reason in reasons:
#        format_reason(reason)    
#    "issue: \"{issue}\"\n"
#    "pros_and_cons:\n"
#    unused_reasons = copy.deepcopy(reasons)
#    roots = []
#    "[MARKER]" where MARKER in set(["```", "- "])
#    marker = MARKER
#    while len(roots)<MAX_N_ROOTS and unused_reasons:
#        if marker == "```":
#            break
#        elif marker == "- ":  # new root
#            "root: \"([TITLE]:" where STOPS_AT(TITLE, ")") and len(TITLE)<32
#            "[CLAIM]" where STOPS_AT(CLAIM, "\n") and len(CLAIM)<128
#            root = RootClaim(label=TITLE, text=CLAIM.strip('\"'))
#            "  pros:\n"
#            while unused_reasons:
#                "[MARKER]" where MARKER in set(["  cons:\n", "  - "])
#                marker = MARKER
#                if marker == "  - ":  # new pro
#                    "\"[[[REASON_TITLE]]]\"\n" where REASON_TITLE in set([reason.label for reason in unused_reasons])
#                    selected_reason = next(reason for reason in unused_reasons if reason.label == REASON_TITLE)
#                    root.pros.append(selected_reason)
#                    unused_reasons.remove(selected_reason)
#                else:
#                    break
#            # cons
#            while unused_reasons:
#                "[MARKER]" where MARKER in set(["```", "- ", "  - "])
#                marker = MARKER
#                if marker == "  - ":  # new con
#                    "\"[[[REASON_TITLE]]]\"\n" where REASON_TITLE in set([reason.label for reason in unused_reasons])
#                    selected_reason = next(reason for reason in unused_reasons if reason.label == REASON_TITLE)
#                    root.cons.append(selected_reason)
#                    unused_reasons.remove(selected_reason)
#                else:
#                    break
#
#            roots.append(root)
#
#    return (roots, unused_reasons)
#
#    '''

@lmql.query
def build_pros_and_cons(reasons_data: list, issue: str):
    '''lmql
    sample(temperature=.4)
        reasons = [Claim(**reason_data) for reason_data in reasons_data]
        """
        {lmql_queries.system_prompt()}

        ### User

        Assignment: Organize an unstructured set of reasons as a pros & cons list.

        Let's begin by thinking through the basic issue addressed by the reasons:
        
        <issue>{issue}</issue>
        
        What are the basic options available to an agent who needs to address this issue? Keep your answer short: sketch each option in a few words only, one per line. Use "<options>"/"</options>" tags.
        
        ### Assistant
        
        The options available to an agent who faces the above issue are:
        
        <options>
        """
        options = []
        marker = ""
        while len(options)<MAX_N_ROOTS:
            "[MARKER]" where MARKER in set(["</options>", "- "])
            marker = MARKER
            if marker == "</options>":
                break
            else:
                "[OPTION]" where STOPS_AT(OPTION, "\n") and len(OPTION) < 32
                options.append(OPTION.strip("\n "))
        """

        ### User

        Thanks, let's keep that in mind.

        Let us now come back to the main assignment: constructing a pros & cons list from a set of reasons. 

        You'll be given a set of reasons, which you're supposed to organize as a pros and cons list. To do so, you have to find a fitting target claim (root statement) the reasons are arguing for (pros) or against (cons).

        Use the following inputs (a list of reasons that address an issue) to solve your assignment.

        <inputs>
        <issue>{issue}</issue>
        <reasons>
        """
        for reason in reasons:
            format_reason(reason)
        """</reasons>
        </inputs>

        Let me show you a few examples to illustrate the task / intended output:
        """
        for ex_issue, ex_proscons in EXAMPLES_ISSUE_PROSCONS:
            f"""
            <example>
            {format_proscons(ex_issue, ex_proscons)}
            </example>
            """
                    
#        <example>
#        ```yaml
#        reasons:
#        - "[[Cultural value]]: Bullfighting is part of history and local cultures."
#        - "[[Cruelty]]: Bullfighting is cruelty for the purpose of entertainment."
#        - "[[Economic benefits]]: Bullfighting may benefit national economies."
#        issue: "Bullfighting?"
#        pros_and_cons:
#        - root: "(Bullfighting ban): Bullfighting should be banned."
#          pros:
#          - "[[Cruelty]]"
#          cons:
#          - "[[Economic benefits]]"
#          - "[[Cultural value]]"
#        ```
#        </example>
#        
#        <example>
#        ```yaml
#        reasons:
#        - "[[Culture]]: New York has incredible cultural events to offer."
#        - "[[Costs]]: Spending holidays in a big city is too expensive."
#        - "[[Swimming]]: Florida has wonderful beaches and a warm ocean."
#        - "[[No Novelty]]: We've been in Los Angeles last year."
#        issue: "Our next holiday"
#        pros_and_cons:
#        - root: "(New York): Let's spend our next holiday in New York."
#          pros:
#          - [[Culture]]
#          cons:
#          - [[Costs]]
#        - root: "(Florida): Let's spend our next holiday in Florida."
#          pros:
#          - [[Swimming]]
#          cons: 
#        - root: "(Los Angeles): Let's spend our next holiday in Los Angeles."
#          pros:
#          cons:
#          - "[[No Novelty]]"
#          - "[[Costs]]"
#        ```
#        </example>
#        
#        <example>
#        ```yaml
#        reasons:
#        - "[[Readability]]: Draft-1 is easier to read than the other drafts."
#        - "[[Engagement]]: Draft-1 is much more funny than the other drafts."
#        issue: "Pick best draft"
#        pros_and_cons:
#        - root: "(Draft-1): Draft-1 is the best draft."
#          pros:
#          - "[[Readability]]"
#          - "[[Engagement]]"
#          cons:        
#        ```        
#        </example>   

        """        
        Please consider carefully the following further, more specific instructions:

        * Be bold: Render the root claim(s) as general, and strong, and unequivocal statement(s).
        * No reasoning: Your root claim(s) must not contain any reasoning (or comments, or explanations).
        * Keep it short: Try to identify a single root claim. Add further root claims only if necessary (e.g., if reasons address three alternative decision options).
        * Recall options: Use the options you've identified above to construct the pros and cons list.
        * Be exhaustive: All reasons must figure in your pros and cons list.
        * !!Re-organize!!: Don't stick to the order of the original reason list.

        Moreover:

        * Use simple and plain language.
        * If you identify multiple root claims, make sure they are mutually exclusive alternatives.
        * Avoid repeating one and the same root claim in different words.
        * Use yaml syntax and "```" code fences to structure your answer.

        ### Assistant
        
        ```yaml
        reasons:
        """
        for reason in reasons:
            format_reason(reason)    
        "issue: \"{issue}\"\n"
        "pros_and_cons:\n"
        unused_reasons = copy.deepcopy(reasons)
        roots = []
        "[MARKER]" where MARKER in set(["```", "- "])
        marker = MARKER
        while len(roots)<MAX_N_ROOTS and unused_reasons:
            if marker == "```":
                break
            elif marker == "- ":  # new root
                "root: \"([TITLE]:" where STOPS_AT(TITLE, ")") and len(TITLE)<32
                "[CLAIM]" where STOPS_AT(CLAIM, "\n") and len(CLAIM)<128
                root = RootClaim(label=TITLE, text=CLAIM.strip('\"'))
                "  pros:\n"
                while unused_reasons:
                    "[MARKER]" where MARKER in set(["  cons:\n", "  - "])
                    marker = MARKER
                    if marker == "  - ":  # new pro
                        "\"[[[REASON_TITLE]]]\"\n" where REASON_TITLE in set([reason.label for reason in unused_reasons])
                        selected_reason = next(reason for reason in unused_reasons if reason.label == REASON_TITLE)
                        root.pros.append(selected_reason)
                        unused_reasons.remove(selected_reason)
                    else:
                        break
                # cons
                while unused_reasons:
                    "[MARKER]" where MARKER in set(["```", "- ", "  - "])
                    marker = MARKER
                    if marker == "  - ":  # new con
                        "\"[[[REASON_TITLE]]]\"\n" where REASON_TITLE in set([reason.label for reason in unused_reasons])
                        selected_reason = next(reason for reason in unused_reasons if reason.label == REASON_TITLE)
                        root.cons.append(selected_reason)
                        unused_reasons.remove(selected_reason)
                    else:
                        break

                roots.append(root)        

        if not unused_reasons:
            return ProsConsList(roots=roots)
            
        """
        ### User 
        
        Thanks! However, I've realized that the following reasons haven't been integrated in the pros & cons list, yet:
        """
        for reason in unused_reasons:
            format_reason(reason)
        """
        Can you please carefully check the above pros & cons list, correct any errors and add the missing reasons?

        ### Assistant
        
        ```yaml
        reasons:
        """
        for reason in reasons:
            format_reason(reason)    
        "issue: \"{issue}\"\n"
        "pros_and_cons:\n"
        unused_reasons = copy.deepcopy(reasons)
        roots = []
        "[MARKER]" where MARKER in set(["```", "- "])
        marker = MARKER
        while len(roots)<MAX_N_ROOTS and unused_reasons:
            if marker == "```":
                break
            elif marker == "- ":  # new root
                "root: \"([TITLE]:" where STOPS_AT(TITLE, ")") and len(TITLE)<32
                "[CLAIM]" where STOPS_AT(CLAIM, "\n") and len(CLAIM)<128
                root = RootClaim(label=TITLE, text=CLAIM.strip('\"'))
                "  pros:\n"
                while unused_reasons:
                    "[MARKER]" where MARKER in set(["  cons:\n", "  - "])
                    marker = MARKER
                    if marker == "  - ":  # new pro
                        "\"[[[REASON_TITLE]]]\"\n" where REASON_TITLE in set([reason.label for reason in unused_reasons])
                        selected_reason = next(reason for reason in unused_reasons if reason.label == REASON_TITLE)
                        root.pros.append(selected_reason)
                        unused_reasons.remove(selected_reason)
                    else:
                        break
                # cons
                while unused_reasons:
                    "[MARKER]" where MARKER in set(["```", "- ", "  - "])
                    marker = MARKER
                    if marker == "  - ":  # new con
                        "\"[[[REASON_TITLE]]]\"\n" where REASON_TITLE in set([reason.label for reason in unused_reasons])
                        selected_reason = next(reason for reason in unused_reasons if reason.label == REASON_TITLE)
                        root.cons.append(selected_reason)
                        unused_reasons.remove(selected_reason)
                    else:
                        break

                roots.append(root)
        return ProsConsList(roots=roots)

    '''

@lmql.query
def unpack_reason(reason_data: dict, issue: str):
    '''lmql
    sample(temperature=.4)
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

        <example>
        ```yaml
        argumentation:
          issue: "Eating animals?"
          title: "Climate impact"
          gist: "Animal farming contributes to climate change because it is extremely energy intensive and causes the degradation of natural carbon sinks through land use change."
          claims:
          - title: "Climate impact"
            claim: "Animal farming contributes to climate change."
          - title: "High energy consumption"
            claim: "Animal farming is extremely energy intensive."
          - title: "Land use change"
            claim: "Animal farming causes the degradation of natural carbon sinks through land use change."
        ```        
        </example>

        <example>
        ```yaml
        argumentation:
          issue: "Should Bullfighting be Banned?"
          title: "Economic benefit"
          gist: "Bullfighting can benefit national economies with an underdeveloped industrial base."
          claims:
          - title: "Economic benefit"
            claim: "Bullfighting can benefit national economies with an underdeveloped industrial base."
        ```        
        </example>

        <example>
        ```yaml
        argumentation:
          issue: "Video games: good or bad?"
          title: "Toxic communities"
          gist: "Many video gaming communities are widely regarded as toxic since online games create opportunities for players to stalk and abuse each other."
          claims:
          - title: "Toxic communities"
            claim: "Many video gaming communities are widely regarded as toxic."
          - title: "Opportunities for abuse"
            claim: "Online games create opportunities for players to stalk and abuse each other."
        ```        
        </example>

        <example>
        ```yaml
        argumentation:
          issue: "Pick best draft"
          title: "Readability"
          gist: "Draft 1 is easier to read and much more funny than the other drafts."
          claims:
          - title: "Readability"
            claim: "Draft 1 is easier to read than the other drafts."
          - title: "Engagement"
            claim: "Draft 1 is much more funny than the other drafts."
        ```        
        </example>

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
                "title: \"[TITLE]" where STOPS_AT(TITLE, "\"") and len(TITLE) < 24
                if not TITLE.endswith('\"'):
                    "\" "
                title = TITLE.strip('\"')
                "\n    claim: \"[CLAIM]" where STOPS_AT(CLAIM, "\"") and len(CLAIM) < 180
                if not CLAIM.endswith('\"'):
                    "\" "
                claim = CLAIM.strip('\"')
                claims.append(Claim(label=title, text=claim))
        return claims

    '''


class ProsConsBuilderLMQL(LMQLDebugger):
    """ProsConsBuilderLMQL

    This LMQLDebugger is responsible for reconstructing a pros and cons list for a given issue.
    """

    _KW_DESCRIPTION = "Pros and cons list with multiple root claims"
    _KW_PRODUCT = "proscons"
    _KW_REQUIREMENTS = ["issue"]


    @staticmethod
    def get_product() -> str:
        return ProsConsBuilderLMQL._KW_PRODUCT


    @staticmethod
    def get_requirements() -> list[str]:
        return ProsConsBuilderLMQL._KW_REQUIREMENTS


    @staticmethod
    def get_description() -> str:
        return ProsConsBuilderLMQL._KW_DESCRIPTION


    def ensure_unique_labels(self, reasons: List[Claim]) -> List[Claim]:
        """Revises labels of reasons to ensure uniqueness

        Args:
            reasons (List[Claim]): list of reasons

        Returns:
            List[Claim]: list of reasons with unique labels
        """

        labels = [reason.label for reason in reasons]
        duplicate_labels = [
            label for label in labels
            if labels.count(label) > 1
        ]
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


    def check_and_revise(self, pros_and_cons: ProsConsList, reasons: List[Claim], issue: str) -> ProsConsList:
        """Checks and revises a pros & cons list

        Args:
            pros_and_cons (List[Dict]): the pros and cons list to be checked and revised
            issue (str): the overarching issue addressed by the pros and cons

        Returns:
            List[Dict]: the revised pros and cons list

        For each pro (con) reason *r* targeting root claim *c*:

        - Checks if *r* supports (attacks) another root claim *c'* more strongly
        - Revises map accordingly

        """

        class Revision(TypedDict):
            reason: Claim
            old_target_idx: int
            old_val: str
            new_target_idx: int
            new_val: str

        revisions: List[Revision] = []

        revised_pros_and_cons = copy.deepcopy(pros_and_cons)

        for enum, root in enumerate(revised_pros_and_cons.roots):

            for pro in root.pros:

                # check target
                lmql_result = lmql_queries.most_confirmed(
                    pro.dict(),
                    [r.dict() for r in revised_pros_and_cons.roots],
                    model=self._model,
                    **self._generation_kwargs
                )
                if lmql_result is None:
                    continue
                probs_confirmed = lmql_queries.get_distribution(lmql_result)
                max_confirmed = max(probs_confirmed, key=lambda x: x[1])
                if max_confirmed[1] < 2*probs_confirmed[enum][1]:
                    continue

                old_val = lmql_queries.PRO
                new_val = old_val
                old_target_idx = enum
                new_target_idx = lmql_queries.label_to_idx(max_confirmed[0])

                # check valence
                lmql_result = lmql_queries.most_disconfirmed(
                    pro.dict(),
                    [r.dict() for r in revised_pros_and_cons.roots],
                    model=self._model,
                    **self._generation_kwargs
                )
                if lmql_result is None:
                    continue
                probs_disconfirmed = lmql_queries.get_distribution(lmql_result)
                max_disconfirmed = max(probs_disconfirmed, key=lambda x: x[1])
                if max_confirmed[0] == max_disconfirmed[0]:
                    lmql_result = lmql_queries.valence(pro.dict(), revised_pros_and_cons.roots[new_target_idx].dict(), model=self._model, **self._generation_kwargs)
                    if lmql_result is not None:
                        new_val = lmql_queries.label_to_valence(
                            lmql_result.variables[lmql_result.distribution_variable]
                        )

                revisions.append({
                    "reason": pro,
                    "old_target_idx": old_target_idx,
                    "new_target_idx": new_target_idx,
                    "old_val": old_val,
                    "new_val": new_val
                })

            for con in root.cons:

                # check target
                lmql_result = lmql_queries.most_disconfirmed(
                    con.dict(),
                    [r.dict() for r in revised_pros_and_cons.roots],
                    model=self._model,
                    **self._generation_kwargs
                )
                if lmql_result is None:
                    continue
                probs_disconfirmed = lmql_queries.get_distribution(lmql_result)
                max_disconfirmed = max(probs_disconfirmed, key=lambda x: x[1])
                if max_disconfirmed[1] < 2*probs_disconfirmed[enum][1]:
                    continue

                old_val = lmql_queries.CON
                new_val = old_val
                old_target_idx = enum
                new_target_idx = lmql_queries.label_to_idx(max_disconfirmed[0])

                # check valence
                lmql_result = lmql_queries.most_confirmed(
                    con.dict(),
                    [r.dict() for r in revised_pros_and_cons.roots],
                    model=self._model,
                    **self._generation_kwargs
                )
                if lmql_result is None:
                    continue
                probs_confirmed = lmql_queries.get_distribution(lmql_result)
                max_confirmed = max(probs_confirmed, key=lambda x: x[1])
                if max_disconfirmed[0] == max_confirmed[0]:
                    lmql_result = lmql_queries.valence(con.dict(), revised_pros_and_cons.roots[new_target_idx].dict(), model=self._model, **self._generation_kwargs)
                    if lmql_result is not None:
                        new_val = lmql_queries.label_to_valence(
                            lmql_result.variables[lmql_result.distribution_variable]
                        )

                revisions.append({
                    "reason": con,
                    "old_target_idx": old_target_idx,
                    "new_target_idx": new_target_idx,
                    "old_val": old_val,
                    "new_val": new_val
                })

        self.logger.info(f"Identified {len(revisions)} revision of pros and cons list.")

        # revise pros and cons list according to revision instructions
        for revision in revisions:
            reason = revision["reason"]
            old_root = revised_pros_and_cons.roots[revision["old_target_idx"]]
            new_root = revised_pros_and_cons.roots[revision["new_target_idx"]]
            if revision["old_val"] == lmql_queries.PRO:
                old_root.pros.remove(reason)
            elif revision["old_val"] == lmql_queries.CON:
                old_root.cons.remove(reason)
            if revision["new_val"] == lmql_queries.PRO:
                new_root.pros.append(reason)
            elif revision["new_val"] == lmql_queries.CON:
                new_root.cons.append(reason)

        return revised_pros_and_cons


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
            for pro in root.pros:
                unpacked_pros = unpack_reason(reason_data=pro.dict(), issue=issue, model=self._model, **self._generation_kwargs)
                if len(unpacked_pros) > 1:
                    root.pros.remove(pro)
                    root.pros.extend(unpacked_pros)
            for con in root.cons:
                unpacked_cons = unpack_reason(reason_data=con.dict(), issue=issue, model=self._model, **self._generation_kwargs)
                if len(unpacked_cons) > 1:
                    root.cons.remove(con)
                    root.cons.extend(unpacked_cons)

        return pros_and_cons


    def _debug(self, debug_state: DebugState):
        """Extract pros and cons of text (prompt/completion).

        Args:
            debug_state (DebugState): current debug_state to which new artifact is added

        Raises:
            ValueError: Failure to create pros and cons list

        Proceeds as follows:

        1. Mine (i.e., extract) all individual reasons from prompt/completion text
        2. Organize reasons into pros and cons list
        3. Double-check and revise pros and cons list
        4. Unpack each individual reason into separate claims (if possible)

        """

        prompt, completion = debug_state.get_prompt_completion()
        issue = next(a.data for a in debug_state.artifacts if a.id == "issue")

        if prompt is None or completion is None:
            raise ValueError(f"Prompt or completion is None. {self.__class__} requires both prompt and completion to debug.")

        # mine reasons
        reasons = mine_reasons(prompt=prompt, completion=completion, issue=issue, model=self._model, **self._generation_kwargs)
        if not all(isinstance(reason, Claim) for reason in reasons):
            raise ValueError(f"Reasons are not of type Claim. Got {reasons}.")
        reasons = self.ensure_unique_labels(reasons)

        # build pros and cons list
        pros_and_cons = build_pros_and_cons(reasons_data=[r.dict() for r in reasons], issue=issue, model=self._model, **self._generation_kwargs)
        if not isinstance(pros_and_cons, ProsConsList):
            raise ValueError(f"Pros and cons list is not of type ProsConsList. Got {pros_and_cons}.")
        # TODO: consider drafting alternative pros&cons lists and choosing best

        # double-check and revise
        pros_and_cons = self.check_and_revise(pros_and_cons, reasons, issue)

        # unpack individual reasons
        pros_and_cons = self.unpack_reasons(pros_and_cons, issue)

        if pros_and_cons is None:
            self.logger.warning("Failed to build pros and cons list (pros_and_cons is None).")

        try:
            pros_and_cons_data = pros_and_cons.model_dump()  # type: ignore
        except AttributeError:
            pros_and_cons_data = pros_and_cons.dict()

        artifact = Artifact(
            id=self._KW_PRODUCT,
            description=self._KW_DESCRIPTION,
            data=pros_and_cons_data,
        )

        debug_state.artifacts.append(artifact)
