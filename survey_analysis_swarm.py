# Standard libraries
import os
from typing import Annotated, Optional, Any
from enum import Enum

# Pydantic models for data validation
from pydantic import BaseModel, Field

# AG2 framework for creating and orchestrating autonomous agents
from autogen import (
    ConversableAgent,
    UserProxyAgent,
    AfterWork,
    AfterWorkOption,
    initiate_swarm_chat,
    SwarmResult,
)

# Get OpenAI API key from a utility file
from utils import get_openai_api_key

# Configure LLM model for all agents
OPENAI_API_KEY = get_openai_api_key()
llm_config = {
    "api_type": "openai", 
    "model": "gpt-4o",
    "parallel_tool_calls": False,
    "cache_seed": None
}

# Shared context to persist state across stages of analysis
shared_context = {
    "survey_objectives": "",
    "survey_results": "",
    "analysis_draft": {},
    "feedback_collection": {},
    "revised_analysis": {},
    "final_report": {},
}

# === STEP 1: Load Objectives & Results ===
def read_objectives_and_results(context_variables: dict) -> SwarmResult:
    """Read the survey objectives and results files and store in shared context"""
    
    # Load survey objectives
    with open('documents/survey_objectives.md', 'r') as file:
        survey_objectives = file.read() 
    context_variables['survey_objectives'] = survey_objectives

    # Load survey results
    with open('static/survey_results.md', 'r') as file:
        survey_results = file.read() 
    context_variables['survey_results'] = survey_results

    # Return control to the analysis drafting agent
    return SwarmResult(
        agent=analysis_drafting_agent,
        context_variables=context_variables,
        values="""Read survey objectives and results and saved to shared context. 
        Moving to analysis drafting stage.""",
    )


# === STEP 2: Drafting Stage ===
class AnalysisDraft(BaseModel):
    title: str = Field(..., description="Analysis title")
    content: str = Field(..., description="Full text content of the analysis")

def submit_analysis_draft(
    title: Annotated[str, "Analysis title"],
    content: Annotated[str, "Full text content of the analysis"],
    context_variables: dict[str, Any]
) -> SwarmResult:
    """Submit the initial draft of the analysis and proceed to review stage"""
    
    analysis_draft = AnalysisDraft(title=title, content=content)
    context_variables["analysis_draft"] = analysis_draft.model_dump()

    return SwarmResult(
        agent=review_agent,
        values="Analysis draft submitted. Moving to review stage.",
        context_variables=context_variables,
    )


# === STEP 3: Feedback Stage ===
class FeedbackItem(BaseModel):
    feedback: str = Field(..., description="Detailed feedback")
    severity: str = Field(..., description="Severity level: minor, moderate, major, critical")
    recommendation: Optional[str] = Field(None, description="Recommended fix")

class FeedbackCollection(BaseModel):
    items: list[FeedbackItem] = Field(..., description="All feedback items")
    overall_assessment: str = Field(..., description="Summary of overall feedback")
    priority_issues: list[str] = Field(..., description="Key issues to fix first")

def submit_feedback(
    items: Annotated[list[FeedbackItem], "Feedback list"],
    overall_assessment: Annotated[str, "Overall assessment"],
    priority_issues: Annotated[list[str], "Priority issues"],
    context_variables: dict[str, Any]
) -> SwarmResult:
    """Submit structured feedback and transition to revision stage"""
    
    feedback = FeedbackCollection(
        items=items,
        overall_assessment=overall_assessment,
        priority_issues=priority_issues,
    )
    context_variables["feedback_collection"] = feedback.model_dump()

    return SwarmResult(
        values="Feedback submitted. Moving to revision stage.",
        agent=revision_agent,
        context_variables=context_variables,
    )


# === STEP 4: Revision Stage ===
class RevisedAnalysis(BaseModel):
    title: str = Field(..., description="Revised title")
    content: str = Field(..., description="Revised content")
    changes_made: Optional[list[str]] = Field(None, description="Changes made")

def submit_revised_analysis(
    title: Annotated[str, "Revised title"],
    content: Annotated[str, "Revised content"],
    changes_made: Annotated[Optional[list[str]], "List of changes made"],
    context_variables: dict[str, Any]
) -> SwarmResult:
    """Submit revised analysis incorporating feedback"""

    revised = RevisedAnalysis(title=title, content=content, changes_made=changes_made)
    context_variables["revised_analysis"] = revised.model_dump()

    # Also update the current analysis draft to reflect revision
    context_variables["analysis_draft"] = {
        "title": revised.title,
        "content": revised.content
    }

    return SwarmResult(
        values="Analysis revised. Moving to finalization stage.",
        agent=finalization_agent,
        context_variables=context_variables,
    )


# === STEP 5: Finalization Stage ===
class FinalAnalysis(BaseModel):
    title: str = Field(..., description="Final title")
    content: str = Field(..., description="Final content")

def finalize_analysis(
    title: Annotated[str, "Final title"],
    content: Annotated[str, "Final content"],
    context_variables: dict[str, Any]
) -> SwarmResult:
    """Submit final analysis ready for recording and delivery"""
    
    final = FinalAnalysis(title=title, content=content)
    context_variables["final_analysis"] = final.model_dump()

    return SwarmResult(
        values="Analysis finalized. Moving to report recording.",
        agent=report_recorder_agent,
        context_variables=context_variables,
    )


# === STEP 6: Write Report to File ===
def write_report_to_file(report: str, filename: str) -> SwarmResult:
    """Save the final analysis report to a markdown file"""

    reports_dir = os.path.join(os.getcwd(), "reports")
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)

    filepath = os.path.join(reports_dir, filename)
    with open(filepath, 'w') as f:
        f.write(report)

    return SwarmResult(
        values=f"Report written to {filepath}",
        context_variables={}
    )


# === Define All Agents ===
from autogen import UpdateSystemMessage

# Agent: Analysis Drafting
analysis_drafting_agent = ConversableAgent(
    name="analysis_drafting_agent",
    system_message="Placeholder system message",  # Updated dynamically
    llm_config=llm_config,
    functions=[submit_analysis_draft],
    context_variables=shared_context,
    update_agent_state_before_reply=UpdateSystemMessage(
        """You are the analysis drafting agent responsible for creating an initial draft...
        [Detailed instructions omitted for brevity]
        """
    )
)

# Agent: Review
review_agent = ConversableAgent(
    name="review_agent",
    system_message="""You are the analysis review agent responsible for critical evaluation...
    [Details omitted]
    """,
    llm_config=llm_config,
    functions=[submit_feedback]
)

# Agent: Revision
revision_agent = ConversableAgent(
    name="revision_agent",
    system_message="""You are the analysis revision agent...
    """,
    llm_config=llm_config,
    functions=[submit_revised_analysis]
)

# Agent: Finalization
finalization_agent = ConversableAgent(
    name="finalization_agent",
    system_message="""You are the finalization agent responsible for completing the process...
    """,
    llm_config=llm_config,
    functions=[finalize_analysis]
)

# Agent: Report Recorder
report_recorder_agent = ConversableAgent(
    name="report_recorder_agent",
    system_message="""You are the report recorder agent...
    """,
    llm_config=llm_config,
    functions=[write_report_to_file]
)

# User agent (non-autonomous)
user = UserProxyAgent(
    name="user",
    code_execution_config=False
)


# === Swarm Orchestration ===
def run_survey_analysis_swarm():
    """Start and run the complete agent workflow for survey analysis"""
    print("Initiating survey results analysis...")

    chat_result, final_context, last_agent = initiate_swarm_chat(
        initial_agent=analysis_drafting_agent,
        agents=[
            analysis_drafting_agent,
            review_agent,
            revision_agent,
            finalization_agent,
            report_recorder_agent
        ],
        messages="Please start the analysis process.",
        context_variables=shared_context,
        user_agent=user,
        max_rounds=30,
        after_work=AfterWork(AfterWorkOption.REVERT_TO_USER)
    )



