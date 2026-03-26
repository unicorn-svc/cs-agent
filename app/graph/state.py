"""LangGraph state definition for the agent workflow."""

from typing import Optional

from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """Complete state schema for the agent workflow."""

    # Input parameters
    query: str = Field(default="", description="Customer question text")
    inquiry_channel: str = Field(default="웹채팅", description="Inquiry channel: 웹채팅, 카카오톡, 전화, 이메일")
    mock_preset: str = Field(default="default", description="MOCK preset: default, empty, error, timeout")
    mock_override: str = Field(default="", description="MOCK override JSON string")

    # Node 2: Classifier raw LLM output (passed to Node 3)
    llm_output: str = Field(default="", description="Raw LLM output from classifier")

    # Node 3: JSON Parsing output
    complexity: str = Field(default="high", description="Complexity level: low, high")
    category: str = Field(default="기타", description="Question category")

    # Node 4: FAQ Search output
    faq_results: str = Field(default="[]", description="JSON string of FAQ search results")
    faq_count: int = Field(default=0, description="Number of FAQ results found")
    top_score: float = Field(default=0.0, description="Top relevance score")
    search_attempts: int = Field(default=1, description="Number of search attempts")
    evaluation_log: str = Field(default="[]", description="JSON string of evaluation log")

    # Node 5: Auto-process decision
    auto_processable: bool = Field(default=False, description="Whether auto-processing is possible")

    # Node 6: Answer generation output
    generated_answer: str = Field(default="", description="LLM-generated answer")

    # Node 7: Cost aggregation output
    saved_cost: int = Field(default=0, description="Cost saved per handling")
    cost_note: str = Field(default="", description="Cost note text")
    total_saved_today: int = Field(default=0, description="Total cost saved today")

    # Node 9: Agent assignment output
    agent_id: str = Field(default="", description="Assigned agent ID")
    agent_name: str = Field(default="", description="Assigned agent name")
    queue_position: int = Field(default=0, description="Queue position")
    estimated_wait_minutes: int = Field(default=0, description="Estimated wait time")
    priority: str = Field(default="normal", description="Priority level: normal, high")

    # Metadata
    process_type: str = Field(default="", description="Process type: auto, escalation")
    error_message: Optional[str] = Field(default=None, description="Error message if any")

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True
