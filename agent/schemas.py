"""The shape of the report the agent must return."""
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class Finding(BaseModel):
    problem: str = Field(description="What is wrong, in simple words. 1-2 sentences.")
    resource: str = Field(
        description="Resource ID or name, copied exactly from the tool output."
    )
    category: Literal["security", "cost"]
    risk_level: Literal["HIGH", "MEDIUM", "LOW"]
    estimated_monthly_saving_usd: Optional[float] = Field(
        default=None,
        description=(
            "Monthly saving in USD ONLY if it can be calculated from tool data. "
            "Otherwise null. Never guess a price."
        ),
    )
    suggested_fix: str = Field(
        description="One concrete fix. A human must approve and do it."
    )


class Report(BaseModel):
    summary: str = Field(description="2-3 sentence overview in simple words.")
    findings: List[Finding] = Field(
        default_factory=list,
        description="Every problem found. Empty list if nothing was found.",
    )
    spend_month_to_date_usd: Optional[float] = Field(
        default=None, description="Total spend this month, from the cost tool."
    )
    checks_not_covered: List[str] = Field(
        default_factory=list,
        description="Important things these tools do not check.",
    )