# =============================================================================
# AG2 Final Report Generation Script
# --------
# This script produces a comprehensive final survey report after the two
# statistical reports (Report 1 and Report 2) have been generated and verified.
# =============================================================================

from dotenv import load_dotenv
import os
from autogen.agentchat.group import AgentTarget, ContextVariables, ReplyResult, TerminateTarget, OnContextCondition, ExpressionContextCondition, RevertToUserTarget
from autogen import UserProxyAgent, ConversableAgent, LLMConfig, UpdateSystemMessage, ContextExpression
from autogen.agentchat.group.patterns import DefaultPattern
from autogen.agentchat import initiate_group_chat
from pydantic import BaseModel
from typing import Annotated
from enum import Enum
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
load_dotenv()

def generate_final_report(model: str):
    """
    Orchestrates the multi-agent feedback loop to create a polished final survey report.

    """

    # ---------------------------
    # Create output directory
    # ---------------------------
    out_dir = Path("final_report")
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------
    # Configure LLM parameters
    # ---------------------------
    openai_llm_config = LLMConfig(
        api_type="openai", 
        model=model,
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0, # deterministic output
        cache_seed=None,
    )

    llm_config = openai_llm_config

    # ---------------------------------------------------------------------
    # OpenRouterLLM Configuration (commented out)
    # ---------------------------------------------------------------------
    #openrouter_llm_config = LLMConfig(
    #    api_type="openai",  # AG2 uses the OpenAI-compatible client
    #    base_url="https://openrouter.ai/api/v1",  # OpenRouter endpoint
    #    api_key=os.environ["OPENROUTER_API_KEY"],  # set this in your env
    #    model=model,  # or e.g. "anthropic/claude-3.5-sonnet"
    #    temperature=0,  # Deterministic output for consistency
    #    cache_seed=None,
    #    parallel_tool_calls=False,
    #    tool_choice="required", # Enforces structured function call sequence
    #    price=[0.00025, 0.001] # Cost per 1000 tokens (numbers not important, but call will fail if not provided)   
    #)

    llm_config = openai_llm_config

    # ---------------------------
    # Enum for workflow stage tracking
    # ---------------------------
    class ReportStage(str, Enum):
        CREATING = "creating"
        REVIEWING = "reviewing"
        REVISING = "revising"
        FINALIZING = "finalizing"

    # ---------------------------
    # Shared context variables
    # ---------------------------
    shared_context = ContextVariables(data={
        # Feedback loop state
        "loop_started": False,
        "current_iteration": 0,
        "max_iterations": 2,
        "iteration_needed": True,
        "current_stage": ReportStage.CREATING.value,

        # Report data at various stages
        "survey_objectives": "",
        "survey_results": "",
        "report_draft": "",
        "feedback_collection": {},
        "revised_report": {},
        "final_report": "",
    })

    # ---------------------------
    # Tools & data models for each stage
    # ---------------------------

    # File loaders (objectives and results)
    def read_objectives(context_variables: ContextVariables) -> str:
        """Read the survey objectives from 'documents/survey_objectives.md'."""
        file_path = "documents/survey_objectives.md"
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def read_survey_results(context_variables: ContextVariables) -> str:
        """Read the survey results from 'report_1/survey_results_run_1.md'."""
        file_path = "report_1/survey_results_run_1.md"
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    
    # Stage 1: Entry / Creation
    def kickoff_report_creation_process(context_variables: ContextVariables) -> ReplyResult:
        """Start the report creation process and advance to CREATING stage."""
        context_variables["loop_started"] = True
        context_variables["current_stage"] = ReportStage.CREATING.value
        context_variables["current_iteration"] = 1
        return ReplyResult(
            message="Report creation process started.",
            target=AgentTarget(report_drafter_agent),
            context_variables=context_variables,
        )

    # Stage 2: Drafting
    def submit_report_draft(content: Annotated[str, "Full text content of the report draft"],
                            context_variables: ContextVariables) -> ReplyResult:
        """Submit the initial report draft and advance to REVIEWING stage."""
        context_variables["report_draft"] = content
        context_variables["current_stage"] = ReportStage.REVIEWING.value
        return ReplyResult(
            message="Report draft submitted. Moving to reviewing stage.",
            target=AgentTarget(report_reviewer_agent),
            context_variables=context_variables,
        )

    # Stage 3: Reviewing / Feedback
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
        """Submit reviewer feedback and advance to revising stage."""
        feedback = FeedbackCollection(
            items=items,
            overall_assessment=overall_assessment,
            priority_issues=priority_issues,
            iteration_needed=iteration_needed
        )
        context_variables["feedback_collection"] = feedback.model_dump()
        context_variables["iteration_needed"] = feedback.iteration_needed
        context_variables["current_stage"] = ReportStage.REVISING.value
        return ReplyResult(
            message="Feedback submitted. Moving to revising stage.",
            context_variables=context_variables,
        )

    # Stage 4: Revising
    class RevisedReport(BaseModel):
        content: str
        changes_made: Optional[list[str]]

    def submit_revised_report(content: Annotated[str, "Full text content after revision"],
                              changes_made: Annotated[Optional[list[str]], "List of changes made based on feedback"],
                              context_variables: ContextVariables) -> ReplyResult:
        """Submit revised report and either loop back to REVIEWING or advance to FINALIZING stage."""
        revised = RevisedReport(content=content, changes_made=changes_made)
        context_variables["revised_report"] = revised.model_dump()
        context_variables["report_draft"] = revised.content

        if context_variables["iteration_needed"] and context_variables["current_iteration"] < context_variables["max_iterations"]:
            context_variables["current_iteration"] += 1
            context_variables["current_stage"] = ReportStage.REVIEWING.value
            return ReplyResult(
                message=f"Report revised. Starting iteration {context_variables['current_iteration']} with another review.",
                context_variables=context_variables,
            )
        else:
            context_variables["current_stage"] = ReportStage.FINALIZING.value
            return ReplyResult(
                message="Revisions complete. Moving to finalizing stage.",
                target=AgentTarget(final_report_agent),  
                context_variables=context_variables,
            )

    # Stage 5: Finalizing
    def finalize_report(content: Annotated[str, "Full text content of the final report"],
                        context_variables: ContextVariables) -> ReplyResult:
        """Submit the final report and terminate workflow."""
        context_variables["final_report"] = content
        context_variables["iteration_needed"] = False
        context_variables["current_stage"] = "done" 
        return ReplyResult(
            message="Report finalized ✅ - terminating workflow.",
            target=TerminateTarget(),
            context_variables=context_variables,
        )

    # ---------------------------
    # Agent definitions for each stage
    # ---------------------------
    with llm_config:
        # Kickoff → Draft → Review → Revision → Finalization

        kickoff_agent = ConversableAgent(
            name="kickoff_agent",
            system_message="""
            You are the kickoff agent. You only initialize the workflow. Your job is to call 
            kickoff_report_creation_process(context_variables: ContextVariables).

            Do not analyze data or produce narrative.
            """,
            functions=[kickoff_report_creation_process]
        )

        report_drafter_agent = ConversableAgent(
            name="report_drafter_agent",
            system_message="""You are the report drafter agent.""",
            functions=[submit_report_draft, read_survey_results, read_objectives],
            update_agent_state_before_reply=[UpdateSystemMessage("""
            ROLE:
            You are the report drafter agent for the report creation process. Your job is to produce the first 
            complete draft of a report, fully compliant with the task instructions.

            TOOLS:  
            • read_survey_results(context_variables: ContextVariables) - Load the survey results.  
            • read_objectives(context_variables: ContextVariables) - Load the survey objectives.   
            • submit_report_draft(content: str, context_variables: ContextVariables) - Submit your completed report draft.

            WORKFLOW (complete in order):  
            1. **Gather Source Material**  
                a. Call **read_survey_results** tool and study the results of the survey. 
                b. Call **read_objectives** tool and study the objectives of the survey. 

            2. **Write the Draft Report**  
                • Examine correlations between different responses and highlight significant takeaways from the data.

                    Expected Output:
                    A comprehensive report draft that includes:
                        1. Key trends and patterns in the survey responses.
                        2. Insights derived from the results, particularly in relation to the survey objectives.
                        3. Notable trends or unexpected findings.
                        4. Differences in responses across demographic groups, if applicable.
                        5. Potential implications of the findings.
                        6. Any gaps in the data or areas that may require further investigation.
                        7. Initial recommendations based on the analysis.
                    
                    • Base the report explicitly on the survey results.  

            SUBMISSION:
            After you have created the report draft, you MUST submit the report draft by using the *submit_report_draft* function.

            """)]
        )

        report_reviewer_agent = ConversableAgent(
            name="report_reviewer_agent",
            system_message="You are the report reviewer agent.",
            functions=[submit_feedback, read_survey_results, read_objectives],
            update_agent_state_before_reply=[UpdateSystemMessage("""
            ROLE:
            You are the report reviewer agent responsible for critical evaluation. Your job is to perform a rigorous, 
            constructive evaluation of the report draft to ensure it fully satisfies the original task 
            instructions and accurately reflects the survey results.

            TOOLS:  
            • read_survey_results(context_variables: ContextVariables) - Load the survey results.  
            • read_objectives(context_variables: ContextVariables) - Load the survey objectives. 
            • submit_feedback(items: list[FeedbackItem], overall_assessment: str, priority_issues: list[str], iteration_needed: bool, context_variables: ContextVariables) - Submit structured feedback.

            WORKFLOW-(complete in order):  
            1. **Gather Context**  
                a. Call **read_survey_results** to review the survey results.  
                b. Call **read_objectives** to review the survey objectives (used to create the report).
                c. Review the report draft : {report_draft}  
                d. Review original task instructions, provided below:
                -----
                • Examine correlations between different responses and highlight significant takeaways from the data.

                    Expected Output:
                    A comprehensive report draft that includes:
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

            SUBMISSION:  
            After you have created your feedback, you MUST use the submit_feedback function to submit the feedback.
            """)]
        )

        report_reviser_agent = ConversableAgent(
            name="report_reviser_agent",
            system_message="""
            You are the report reviser agent.
            """,
            functions=[submit_revised_report],
            update_agent_state_before_reply=[UpdateSystemMessage("""
            ROLE: 
            You are the report reviser agent responsible for implementing feedback. Your job is to incorporate reviewer 
            feedback to produce an improved Markdown report that still satisfies the original task instructions.

            INPUTS:  
            • Current report draft: {report_draft} 
            • Feedback from report_reviewer_agent: {feedback_collection} 
            • Original task instructions are provided below:
            -----
            • Examine correlations between different responses and highlight significant takeaways from the data.

                Expected Output:
                A comprehensive report draft that includes:
                    1. Key trends and patterns in the survey responses.
                    2. Insights derived from the results, particularly in relation to the survey objectives.
                    3. Notable trends or unexpected findings.
                    4. Differences in responses across demographic groups, if applicable.
                    5. Potential implications of the findings.
                    6. Any gaps in the data or areas that may require further investigation.
                    7. Initial recommendations based on the analysis.
                    
                    • Base the report explicitly on the survey results. 
            -----

            TOOLS: 
            • submit_revised_report(content: str, changes_made: Optional[list[str]], context_variables: ContextVariables) - Submit the revised report.


            WORKFLOW (complete in order): 
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

            SUBMISSION:  
            After you have created your revised report, you MUST use the submit_revised_report function to submit the revised report,
            as well as the change log.
            The revised report may go through multiple revision cycles depending on the feedback.
            """)],
        )

        final_report_agent = ConversableAgent(
            name="final_report_agent",
            system_message="""You are the final report agent.""",
            functions=[finalize_report],
            update_agent_state_before_reply=[UpdateSystemMessage("""
            ROLE:
            You are the final report agent. Your job is to complete the process by producing a polished, delivery-ready Markdown report.

            INPUTS: 
            • {report_draft} - the latest report version.  
            • {feedback_collection} - the revision history.
            • The original task instructions are provided below:
            -----
            • Examine correlations between different responses and highlight significant takeaways from the data.

                Expected Output:
                A comprehensive report draft that includes:
                    1. Key trends and patterns in the survey responses.
                    2. Insights derived from the results, particularly in relation to the survey objectives.
                    3. Notable trends or unexpected findings.
                    4. Differences in responses across demographic groups, if applicable.
                    5. Potential implications of the findings.
                    6. Any gaps in the data or areas that may require further investigation.
                    7. Initial recommendations based on the analysis.
                    
                    • Base the report explicitly on the survey results. 
            -----


            TOOLS:
            • submit_final_report(content: str, context_variables: ContextVariables) — Submit your completed final report.

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

            SUBMISSION:  
            After you have created your final report, you MUST use the submit_final_report function to submit the final report.
             
            """)]
        )

    # ---------------------------
    # Handoff logic between agents
    # ---------------------------
    kickoff_agent.handoffs.add_context_condition(
        OnContextCondition(
            target=AgentTarget(report_drafter_agent),
            condition=ExpressionContextCondition(ContextExpression("${loop_started} == True and ${current_stage} == 'creating'"))
        )
    )
    report_drafter_agent.handoffs.add_context_condition(
        OnContextCondition(
            target=AgentTarget(report_reviewer_agent),
            condition=ExpressionContextCondition(ContextExpression("${current_stage} == 'reviewing'"))
        )
    )
    report_reviewer_agent.handoffs.add_context_condition(
        OnContextCondition(
            target=AgentTarget(report_reviser_agent),
            condition=ExpressionContextCondition(ContextExpression("${current_stage} == 'revising'"))
        )
    )
    report_reviser_agent.handoffs.add_context_conditions([
        OnContextCondition(
            target=AgentTarget(final_report_agent),
            condition=ExpressionContextCondition(ContextExpression("${current_stage} == 'finalizing'"))
        ),
        OnContextCondition(
            target=AgentTarget(report_reviewer_agent),
            condition=ExpressionContextCondition(ContextExpression("${current_stage} == 'reviewing'"))
        )
    ])
    final_report_agent.handoffs.set_after_work(TerminateTarget())

    # ---------------------------
    # Pattern orchestration
    # ---------------------------
    user = UserProxyAgent(name="user", code_execution_config=False)
    agent_pattern = DefaultPattern(
        initial_agent=kickoff_agent,
        agents=[kickoff_agent, report_drafter_agent, report_reviewer_agent, report_reviser_agent, final_report_agent],
        context_variables=shared_context,
        user_agent=user,
    )

    # ---------------------------
    # Run the multi-agent loop
    # ---------------------------
    chat_result, final_context, last_agent = initiate_group_chat(
        pattern=agent_pattern,
        messages="Write a final report that synthesizes the results of multiple focus group session reports.",
        max_rounds=60,
    )

    # ---------------------------
    # Save final output
    # ---------------------------
    if final_context.get("final_report"):
        print("Report creation completed successfully!")
        final_report_content = final_context['final_report']
        os.makedirs("final_report", exist_ok=True)
        with open("final_report/final_survey_report.md", "w", encoding="utf-8") as f:
            f.write(final_report_content)
    else:
        print("Report creation did not complete successfully.")
        




