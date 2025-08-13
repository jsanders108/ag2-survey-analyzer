# -----------------------------------------------------------------------------------
# AG2 Final Report Generation Script
#
# Purpose:
#   This script produces a comprehensive final survey report after the two
#   statistical reports (Report 1 and Report 2) have been generated and verified.
#
# Process:
#   Implements an AI-driven, multi-agent feedback loop for creating, reviewing,
#   revising, and finalizing the final report. The workflow includes:
#       1. Entry stage – Initiate report creation.
#       2. Draft stage – Create first draft from survey objectives & results.
#       3. Review stage – Critically evaluate the draft and provide structured feedback.
#       4. Revision stage – Apply feedback to improve the report.
#       5. Finalization stage – Polish and deliver the final Markdown file.
#
# Key Features:
#   - Structured iteration: up to `max_iterations` revision cycles.
#   - Persistent shared context for passing data between agents.
#   - Clear separation of roles across specialized agents.
#   - Task-driven handoff conditions between agents.
#
# Dependencies:
#   pip install python-dotenv ag2 pydantic
#
# Requirements:
#   - Must be run after survey results and objectives files exist.
#   - OPENAI_API_KEY must be available via environment variables.
# -----------------------------------------------------------------------------------

from dotenv import load_dotenv
import os
from autogen.agentchat.group import AgentTarget, ContextVariables, ReplyResult, TerminateTarget, OnContextCondition, ExpressionContextCondition, RevertToUserTarget
from autogen import UserProxyAgent, ConversableAgent, LLMConfig, UpdateSystemMessage, ContextExpression
from autogen.agentchat.group.patterns import DefaultPattern
from autogen.agentchat import initiate_group_chat
from pydantic import BaseModel, Field
from typing import Annotated
from enum import Enum
from pathlib import Path
from typing import Any, Optional

# Load environment variables from .env file
load_dotenv()

def generate_final_report(model: str):
    """
    Orchestrates the multi-agent feedback loop to create a polished final survey report.

    Parameters
    ----------
    model : str
        The OpenAI model name for LLM-based agents (e.g., "gpt-4").

    Workflow
    --------
    1. Prepare output directory for final report.
    2. Define shared context variables for state, content, and error tracking.
    3. Define data models & tools for each workflow stage:
       - Create → Review → Revise → Finalize
    4. Configure specialized ConversableAgents for each stage.
    5. Define handoff conditions for stage transitions.
    6. Initiate the feedback loop pattern until the report is finalized or errors occur.
    7. Save the final report to disk.
    """

    # ---------------------------
    # Create output directory
    # ---------------------------
    out_dir = Path("Final Report")
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------
    # LLM configuration
    # ---------------------------
    llm_config = LLMConfig(
        api_type="openai",
        model=model,
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0,
        cache_seed=None,
        tool_choice="required"  # Require explicit tool usage
    )

    # ---------------------------
    # Enum for workflow stage tracking
    # ---------------------------
    class ReportStage(str, Enum):
        CREATE = "create"
        REVIEW = "review"
        REVISE = "revise"
        FINALIZE = "finalize"

    # ---------------------------
    # Shared context variables
    # ---------------------------
    shared_context = ContextVariables(data={
        # Feedback loop state
        "loop_started": False,
        "current_iteration": 0,
        "max_iterations": 2,
        "iteration_needed": True,
        "current_stage": ReportStage.CREATE,

        # Report data at various stages
        "survey_objectives": "",
        "survey_results": "",
        "report_draft": {},
        "feedback_collection": {},
        "revised_report": {},
        "final_report": {},

        # Error state
        "has_error": False,
        "error_message": "",
        "error_stage": ""
    })

    # ---------------------------
    # Tools & data models for each stage
    # ---------------------------

    # Stage 1: Entry / Creation
    def start_report_creation_process(context_variables: ContextVariables) -> ReplyResult:
        """Start the report creation process and advance to CREATE stage."""
        context_variables["loop_started"] = True
        context_variables["current_stage"] = ReportStage.CREATE.value
        context_variables["current_iteration"] = 1
        return ReplyResult(
            message="Report creation process started.",
            context_variables=context_variables,
        )

    # File loaders (objectives and results)
    def read_objectives(context_variables: ContextVariables) -> str:
        """Read the survey objectives from 'documents/survey_objectives.md'."""
        file_path = "documents/survey_objectives.md"
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError as err:
            context_variables["has_error"] = True
            context_variables["error_stage"] = "read_objectives"
            context_variables["error_message"] = str(err)
            raise

    def read_survey_results(context_variables: ContextVariables) -> str:
        """Read the survey results from 'Report 1/survey_results_run_1.md'."""
        file_path = "Report 1/survey_results_run_1.md"
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError as err:
            context_variables["has_error"] = True
            context_variables["error_stage"] = "read_results"
            context_variables["error_message"] = str(err)
            raise

    # Stage 2: Draft
    class ReportDraft(BaseModel):
        title: str
        content: str

    def submit_report_draft(title: Annotated[str, "Report title"],
                            content: Annotated[str, "Full text content of the report draft"],
                            context_variables: ContextVariables) -> ReplyResult:
        """Store the initial draft in context and advance to REVIEW stage."""
        report_draft = ReportDraft(title=title, content=content)
        context_variables["report_draft"] = report_draft.model_dump()
        context_variables["current_stage"] = ReportStage.REVIEW.value
        return ReplyResult(
            message="Report draft submitted. Moving to review stage.",
            context_variables=context_variables,
        )

    # Stage 3: Review / Feedback
    class FeedbackItem(BaseModel):
        section: str
        feedback: str
        severity: str
        recommendation: Optional[str]

    class FeedbackCollection(BaseModel):
        items: list[FeedbackItem]
        overall_assessment: str
        priority_issues: list[str]
        iteration_needed: bool

    def submit_feedback(items: Annotated[list[FeedbackItem], "Collection of feedback items"],
                        overall_assessment: Annotated[str, "Overall assessment of the report"],
                        priority_issues: Annotated[list[str], "List of priority issues to address"],
                        iteration_needed: Annotated[bool, "Whether another iteration is needed"],
                        context_variables: ContextVariables) -> ReplyResult:
        """Store reviewer feedback and advance to REVISE stage."""
        feedback = FeedbackCollection(
            items=items,
            overall_assessment=overall_assessment,
            priority_issues=priority_issues,
            iteration_needed=iteration_needed
        )
        context_variables["feedback_collection"] = feedback.model_dump()
        context_variables["iteration_needed"] = feedback.iteration_needed
        context_variables["current_stage"] = ReportStage.REVISE.value
        return ReplyResult(
            message="Feedback submitted. Moving to revision stage.",
            context_variables=context_variables,
        )

    # Stage 4: Revision
    class RevisedReport(BaseModel):
        title: str
        content: str
        changes_made: Optional[list[str]]

    def submit_revised_report(title: Annotated[str, "Report title"],
                              content: Annotated[str, "Full text content after revision"],
                              changes_made: Annotated[Optional[list[str]], "List of changes made based on feedback"],
                              context_variables: ContextVariables) -> ReplyResult:
        """Store revised report and either loop back to REVIEW or advance to FINALIZE stage."""
        revised = RevisedReport(title=title, content=content, changes_made=changes_made)
        context_variables["revised_report"] = revised.model_dump()

        if context_variables["iteration_needed"] and context_variables["current_iteration"] < context_variables["max_iterations"]:
            context_variables["current_iteration"] += 1
            context_variables["current_stage"] = ReportStage.REVIEW.value
            context_variables["report_draft"] = {"title": revised.title, "content": revised.content}
            return ReplyResult(
                message=f"Report revised. Starting iteration {context_variables['current_iteration']} with another review.",
                context_variables=context_variables,
            )
        else:
            context_variables["current_stage"] = ReportStage.FINALIZE.value
            return ReplyResult(
                message="Revisions complete. Moving to report finalization.",
                context_variables=context_variables,
            )

    # Stage 5: Finalization
    class FinalReport(BaseModel):
        title: str
        content: str

    def finalize_report(title: Annotated[str, "Final report title"],
                        content: Annotated[str, "Full text content of the final report"],
                        context_variables: ContextVariables) -> ReplyResult:
        """Store the final report in context and terminate workflow."""
        final = FinalReport(title=title, content=content)
        context_variables["final_report"] = final.model_dump()
        context_variables["iteration_needed"] = False
        return ReplyResult(
            message="Report finalized ✅ - terminating workflow.",
            target=TerminateTarget(),
            context_variables=context_variables,
        )

    # ---------------------------
    # Agent definitions for each stage
    # ---------------------------
    with llm_config:
        # Entry → Draft → Review → Revision → Finalization
        entry_agent = ConversableAgent(
            name="entry_agent",
            system_message="""You are the entry point for the report creation process...""",
            functions=[start_report_creation_process]
        )

        report_draft_agent = ConversableAgent(
            name="report_draft_agent",
            system_message="""You are the report draft agent...""",
            functions=[submit_report_draft, read_survey_results, read_objectives],
            update_agent_state_before_reply=[UpdateSystemMessage("""
            ROLE
                You are the report draft agent for the report creation process.

             YOUR TASK  
                Produce the first complete draft of the final survey report, fully compliant 
                with the task instructions.
                Submit the draft report for review.

             TOOLS  
                • read_survey_results() - Load the survey results.  
                • read_objectives() - Load the survey objectives.   
                • submit_report_draft() - Submit the finished report draft.

             WORKFLOW (complete in order)  
                1. **Gather Source Material**  
                    a. Call **read_survey_results** tool and study the individual survey reports. 
                    b. Call **read_objectives** tool and study the survey objectives. 

                2. **Write the Draft Report**  
                    • Examine correlations between different responses and highlight significant takeaways from the data.

                Expected Output:
                    A comprehensive analysis draft that includes:
                        1. Key trends and patterns in the survey responses.
                        2. Insights derived from the results, particularly in relation to the survey objectives.
                        3. Notable trends or unexpected findings.
                        4. Differences in responses across demographic groups, if applicable.
                        5. Potential implications of the findings.
                        6. Any gaps in the data or areas that may require further investigation.
                        7. Initial recommendations based on the analysis.
                    
                    • Base the report explicitly on the survey results.  

                3. **Submit**  
                    • After you have completed the report draft, use the **submit_report_draft** tool to submit it for review.  
            """)]
        )

        report_review_agent = ConversableAgent(
            name="report_review_agent",
            system_message="You are the report review agent responsible for critical evaluation.",
            functions=[submit_feedback, read_survey_results, read_objectives],
            update_agent_state_before_reply=[UpdateSystemMessage("""
            ROLE
                You are the report review agent responsible for critical evaluation.

                YOUR TASK  
                Perform a rigorous, constructive evaluation of the draft final survey report to ensure 
                it fully satisfies the original task instructions and accurately reflects the individual survey reports.
                Submit your feedback for revision.

                TOOLS  
                • read_survey_results() - Load the survey results.  
                • read_objectives() - Load the survey objectives (used to create the draft report)  
                • submit_feedback() - Submit structured feedback.

                WORKFLOW-(complete in order)  
                1. **Gather Context**  
                   a. Call **read_survey_results** to review the survey results.  
                   b. Call **read_objectives** to review the survey objectives (used to create the draft report).
                   c. Review the report draft : {report_draft}  
                   d. Review original task instructions, provided below:
                      -----
                      • Examine correlations between different responses and highlight significant takeaways from the data.

                        Expected Output:
                            A comprehensive analysis draft that includes:
                                1. Key trends and patterns in the survey responses.
                                2. Insights derived from the results, particularly in relation to the survey objectives.
                                3. Notable trends or unexpected findings.
                                4. Differences in responses across demographic groups, if applicable.
                                5. Potential implications of the findings.
                                6. Any gaps in the data or areas that may require further investigation.
                                7. Initial recommendations based on the analysis.
                    
                        • Base the report explicitly on the survey results. 
                      ----- 

                2. **Evaluate the Draft Report** against:  
                   • Instruction compliance & completeness  
                   • Thematic accuracy and evidence support (statistical analysis)  
                   • Clarity, logic, and flow of writing  
                   • Neutrality and stakeholder-friendliness  

                3. **Provide Feedback**
                For the feedback you MUST provide the following:
                    1. items: list of feedback items (see next section for the collection of feedback items)
                    2. overall_assessment: Overall assessment of the draft report
                    3. priority_issues: List of priority issues to address
                    4. iteration_needed: Whether another iteration is needed (True or False)

                    For each item within feedback, you MUST provide the following:
                        1. section: The specific section the feedback applies to
                        2. feedback: Detailed feedback explaining the issue
                        3. severity: Rate as 'minor', 'moderate', 'major', or 'critical'
                        4. recommendation: A clear, specific action to address the feedback

                    Provide specific feedback with examples and clear recommendations for improvement.
                    For each feedback item, specify which section it applies to and rate its severity.

                    If this is a subsequent review iteration, also evaluate how well previous feedback was addressed.

                4. **Submit Feedback**
                - Use the submit_feedback tool when your review is complete, indicating whether another iteration is needed.
            """)]
        )

        revision_agent = ConversableAgent(
            name="revision_agent",
            system_message="""
            ROLE 
            You are the report revision agent responsible for implementing feedback.

            OBJECTIVE  
            Incorporate reviewer feedback to produce an improved Markdown report that still satisfies the original task instructions.

            INPUTS  
            • Current report draft: {report_draft} 
            • Feedback from review_agent: {feedback_collection} 
            • Original task instructions are provided below:
            -----
            • Examine correlations between different responses and highlight significant takeaways from the data.

                        Expected Output:
                            A comprehensive analysis draft that includes:
                                1. Key trends and patterns in the survey responses.
                                2. Insights derived from the results, particularly in relation to the survey objectives.
                                3. Notable trends or unexpected findings.
                                4. Differences in responses across demographic groups, if applicable.
                                5. Potential implications of the findings.
                                6. Any gaps in the data or areas that may require further investigation.
                                7. Initial recommendations based on the analysis.
                    
                        • Base the report explicitly on the survey results. 
            -----

            TOOLS 
            • submit_revised_report() - Submit the revised report.


            WORKFLOW (complete in order)  
            1. **Analyze Feedback**  
            • Sort feedback items by the reviewer's stated priority (or severity if no explicit order).  
            • Verify whether any item conflicts with the original task instructions; if so, favor the original task 
            instructions and note the conflict in the change log.

            2. **Revise the Report**  
            • Make targeted edits that directly address each feedback item.  
            • Preserve existing strengths and accurate content.  
            • Maintain all formatting constraints (e.g., no triple back-ticks; end with “# End of Report”).

            3. **Document Changes**  
            • Track and document the changes you make in a change log.

            4. **Submit**  
            • Use the submit_revised_report tool to submit the revised report, as well as the change log. The report may go through
            multiple revision cycles depending on the feedback.
            """,
            functions=[submit_revised_report]
        )

        finalization_agent = ConversableAgent(
            name="finalization_agent",
            system_message="""
            ROLE
            You are the report finalization agent responsible for completing the process.

            YOUR TASK:   
            Produce a polished, delivery-ready Markdown report.

            INPUTS  
            • {report_draft} - the latest report version.  
            • {feedback_collection} - the revision history.
            • The original task instructions are provided below:
            -----
            • Examine correlations between different responses and highlight significant takeaways from the data.

                        Expected Output:
                            A comprehensive analysis draft that includes:
                                1. Key trends and patterns in the survey responses.
                                2. Insights derived from the results, particularly in relation to the survey objectives.
                                3. Notable trends or unexpected findings.
                                4. Differences in responses across demographic groups, if applicable.
                                5. Potential implications of the findings.
                                6. Any gaps in the data or areas that may require further investigation.
                                7. Initial recommendations based on the analysis.
                    
                        • Base the report explicitly on the survey results. 
            -----


            TOOLS  
            • finalize_report() - Submit the finished artefacts.

            WORKFLOW (complete in order)  
            1. **Assess Compliance**  
            • Compare {report_draft} to the original task instructions; confirm every requirement is met.  
            • Skim revision history {feedback_collection} to verify previous feedback was resolved.

            2. **Polish the Report**  
            • Correct residual issues in clarity, grammar, tone, or Markdown formatting.  
            • Preserve analyst content; limit edits to minor improvements (no structural overhauls).  
            • Ensure no triple back-ticks, proper headings, and that the document ends with “# End of Report”.

            3. **Craft Revision Journey Summary**  
            • 1-2 short paragraphs highlighting key iterations and how the report improved.

            4. **Submit Final Report**
            - Use the finalize_report tool when the report is complete and ready for delivery.
            
            """,
            functions=[finalize_report]
        )

    # ---------------------------
    # Handoff logic between agents
    # ---------------------------
    entry_agent.handoffs.add_context_condition(
        OnContextCondition(
            target=AgentTarget(report_draft_agent),
            condition=ExpressionContextCondition(ContextExpression("${loop_started} == True and ${current_stage} == 'create'"))
        )
    )
    report_draft_agent.handoffs.add_context_condition(
        OnContextCondition(
            target=AgentTarget(report_review_agent),
            condition=ExpressionContextCondition(ContextExpression("${current_stage} == 'review'"))
        )
    )
    report_review_agent.handoffs.add_context_condition(
        OnContextCondition(
            target=AgentTarget(revision_agent),
            condition=ExpressionContextCondition(ContextExpression("${current_stage} == 'revise'"))
        )
    )
    revision_agent.handoffs.add_context_conditions([
        OnContextCondition(
            target=AgentTarget(finalization_agent),
            condition=ExpressionContextCondition(ContextExpression("${current_stage} == 'finalize'"))
        ),
        OnContextCondition(
            target=AgentTarget(report_review_agent),
            condition=ExpressionContextCondition(ContextExpression("${current_stage} == 'review'"))
        )
    ])
    finalization_agent.handoffs.set_after_work(TerminateTarget())

    # ---------------------------
    # Pattern orchestration
    # ---------------------------
    user = UserProxyAgent(name="user", code_execution_config=False)
    agent_pattern = DefaultPattern(
        initial_agent=entry_agent,
        agents=[entry_agent, report_draft_agent, report_review_agent, revision_agent, finalization_agent],
        context_variables=shared_context,
        user_agent=user,
    )

    # ---------------------------
    # Run the multi-agent loop
    # ---------------------------
    chat_result, final_context, last_agent = initiate_group_chat(
        pattern=agent_pattern,
        messages="Write a final report that synthesizes the results of multiple focus group session reports.",
        max_rounds=50,
    )

    # ---------------------------
    # Save final output
    # ---------------------------
    if final_context.get("final_report"):
        print("Report creation completed successfully!")
        final_report_content = final_context['final_report'].get('content', '')
        os.makedirs("final_report", exist_ok=True)
        with open("final_survey_report.md", "w", encoding="utf-8") as f:
            f.write(final_report_content)
    else:
        print("Report creation did not complete successfully.")
        if final_context.get("has_error"):
            print(f"Error during {final_context.get('error_stage')} stage: {final_context.get('error_message')}")

