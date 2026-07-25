from pydantic import BaseModel, Field
from typing import List


class VerificationReport(BaseModel):
    """
    Structured verification report from the LLM.
    """
    supported: str = Field(
        description="YES or NO - whether the answer is factually supported by context",
        examples=["YES", "NO"]
    )
    unsupported_claims: List[str] = Field(
        default_factory=list,
        description="List of claims not supported by the context"
    )
    contradictions: List[str] = Field(
        default_factory=list,
        description="List of contradictions found between answer and context"
    )
    relevant: str = Field(
        description="YES or NO - whether the answer is relevant to the question",
        examples=["YES", "NO"]
    )
    additional_details: str = Field(
        default="",
        description="Any extra information or explanations"
    )

    def to_report(self) -> str:
        """Format the verification report into a readable string."""
        report = f"**Supported:** {self.supported}\n"

        if self.unsupported_claims:
            report += f"**Unsupported Claims:** {', '.join(self.unsupported_claims)}\n"
        else:
            report += f"**Unsupported Claims:** None\n"

        if self.contradictions:
            report += f"**Contradictions:** {', '.join(self.contradictions)}\n"
        else:
            report += f"**Contradictions:** None\n"

        report += f"**Relevant:** {self.relevant}\n"

        if self.additional_details:
            report += f"**Additional Details:** {self.additional_details}\n"
        else:
            report += f"**Additional Details:** None\n"

        return report
