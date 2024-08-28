"""Data Models for Pros & Cons Lists"""

from __future__ import annotations

from pydantic import BaseModel, Field, RootModel


class Claim(BaseModel, frozen=True):
    text: str = Field(description="The statement that expresses the claim")
    label: str = Field(description="Brief headline that describes the claim")


class ClaimList(RootModel):
    root: list[Claim] = Field(description="List of claims")


class RootClaim(Claim, frozen=False):
    pros: list[Claim] = Field(description="List of claims that support root claim")
    cons: list[Claim] = Field(description="List of claims that oppose root claim")


class ProsConsList(BaseModel):
    roots: list[RootClaim] = Field(description="List of seperate pros/cons list for different root claims")
    options: list[str] | None = Field(default=None, description="List of options relevant for the pros/cons list")
