"""argdown.py

Utils and helpers for creating and parsing ardown snippets.
"""

import logging

from logikon.schemas.pros_cons import Claim, ProsConsList, RootClaim

# TODO: write tests for these regexes
REGEX_PROPOSITION = r"\[[^\]\n]*\]: [^\n]*\."
REGEX_PROSLIST = r"// PROS(\n\+ " + REGEX_PROPOSITION + r")*"
REGEX_CONSLIST = r"// CONS(\n\- " + REGEX_PROPOSITION + r")*"
REGEX_ROOTCLAIM = REGEX_PROPOSITION + r"\n" + REGEX_PROSLIST + r"\n" + REGEX_CONSLIST
REGEX_PROSCONS = r"```argdown\n(" + REGEX_ROOTCLAIM + r"\n)+```"

# GBNF for argdown pros/cons snippets
GRAMMAR_PROSCONS = r"""
root        ::= "```argdown\n" rootclaim+ "```"
rootclaim   ::= proposition proslist conslist
proslist    ::= "// PROS\n" ("+ " proposition)*
conslist    ::= "// CONS\n" ("- " proposition)*
proposition ::= "[" label "]: " text
text        ::= [^\n]* "\n"
label       ::= [^\]\n]*
"""


class ArgdownParser:
    """Parser for argdown snippets."""

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger

    def parse_proscons(self, snippet: str) -> ProsConsList:
        """Parse the argdown snippet into a ProsConsList."""
        lines = snippet.split("\n")
        if lines[0] == "```argdown":
            lines = lines[1:]
        elif self.logger is not None:
            self.logger.warning("Snippet does not start with '```argdown'")
        if lines[-1] == "```":
            lines = lines[:-1]
        elif self.logger is not None:
            self.logger.warning("Snippet does not end with '```'")

        roots: list[RootClaim] = []

        while len(lines) > 0:
            root_claim, lines = self.parse_rootclaim(lines)
            if root_claim is not None:
                roots.append(root_claim)

        return ProsConsList(roots=roots)

    def parse_rootclaim(self, lines: list[str]) -> tuple[RootClaim | None, list[str]]:
        """Parse a root claim from the given lines.
        Return remaining lines after parsing the root claim."""
        claim = self.parse_proposition(lines[0])
        if claim is None:
            if self.logger is not None:
                self.logger.warning(f"Expected root claim, got {lines[0]}")
            return None, lines[1:]
        lines = lines[1:]
        pros, lines = self.parse_reasonslist(lines, "PROS")
        cons, lines = self.parse_reasonslist(lines, "CONS")
        return RootClaim(label=claim.label, text=claim.text, pros=pros, cons=cons), lines

    def parse_proposition(self, line: str) -> Claim | None:
        """Parse a proposition from the given lines."""
        if (not line) or (line[0] != "[") or ("]: " not in line):
            if self.logger is not None:
                self.logger.warning(f"Expected proposition, got {line}")
            return None
        line = line[1:]
        label, text = line.split("]: ", maxsplit=1)
        return Claim(label=label, text=text)

    def parse_reasonslist(self, lines: list[str], name: str) -> tuple[list[Claim], list[str]]:
        """Parse a pros or cons list from the given lines."""
        if not lines:
            return [], lines
        if lines[0] == f"// {name}":
            lines = lines[1:]
        elif self.logger is not None:
            self.logger.warning(f"{name} list does not start with '// {name}'.")

        bullet = "+ " if name == "PROS" else "- "

        claims = []
        while len(lines) > 0:
            line = lines[0]
            if line.startswith(bullet):
                claim = self.parse_proposition(line[2:].strip())
                if claim is not None:
                    claims.append(claim)
                lines = lines[1:]
            else:
                break
        return claims, lines


class ArgdownFormatter:

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger

    def format_proscons(self, proscons: ProsConsList) -> str:
        """Format the given ProsConsList into an argdown snippet."""
        lines = []
        lines.append("```argdown")
        for root in proscons.roots:
            lines.extend(self.format_rootclaim(root))
        lines.append("```")
        return "\n".join(lines)

    def format_rootclaim(self, root: RootClaim) -> list[str]:
        """Format the given RootClaim into an argdown root claim."""
        lines = []
        lines.append(f"[{root.label}]: {root.text}")
        lines.extend(self.format_reasonslist(root.pros, "PROS"))
        lines.extend(self.format_reasonslist(root.cons, "CONS"))
        return lines

    def format_reasonslist(self, claims: list[Claim], name: str) -> list[str]:
        """Format the given list of claims into a pros or cons list."""
        lines = []
        lines.append(f"// {name}")
        bullet = "+ " if name == "PROS" else "- "
        for claim in claims:
            lines.append(f"{bullet}[{claim.label}]: {claim.text}")
        return lines


def format_proscons(proscons: ProsConsList) -> str:
    """Format the given ProsConsList into an argdown snippet."""
    formatter = ArgdownFormatter()
    return formatter.format_proscons(proscons)


def parse_proscons(snippet: str) -> ProsConsList:
    """Parse the argdown snippet into a ProsConsList."""
    parser = ArgdownParser()
    return parser.parse_proscons(snippet)
