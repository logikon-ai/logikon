"""Data Models for Pros & Cons Lists"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class Claim(BaseModel):
    text: str
    label: str

class RootClaim(Claim):
    pros: List[Claim] = []
    cons: List[Claim] = []

class ProsConsList(BaseModel):
    roots: List[RootClaim] = []
