"""Data Models for Pros & Cons Lists"""

from __future__ import annotations

from pydantic import BaseModel


class Claim(BaseModel):
    text: str
    label: str


class RootClaim(Claim):
    pros: list[Claim] = []  # noqa: RUF012
    cons: list[Claim] = []  # noqa: RUF012


class ProsConsList(BaseModel):
    roots: list[RootClaim] = []
    options: list[str] | None = []
