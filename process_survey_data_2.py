# =============================================================================
# AG2 Final Report Generation Script
# --------
# This script uses AG2's multi-agent orchestration to perform automated data
# processing on a cryptocurrency survey dataset. It coordinates between:
#   - A Planner Agent (designs the analysis plan)
#   - A Code Writer Agent (writes Python code for data analysis)
#   - A Code Executor Agent (runs the generated code locally)
# =============================================================================

from pathlib import Path
from autogen import ConversableAgent, LLMConfig
from autogen.coding import LocalCommandLineCodeExecutor
from autogen.agentchat.group.patterns import AutoPattern
from autogen.agentchat import initiate_group_chat
from dotenv import load_dotenv
import os
from instructions.initial_message_run_2 import initial_message_run_2

# Load environment variables from .env file
load_dotenv()

def process_survey_data_2(model: str):
    """
    Orchestrates an AI-driven survey data processing workflow using AG2's agent
    collaboration pattern.

    """

    # ---------------------------
    # Create output directory
    # ---------------------------
    out_dir = Path("report_2")
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

    # ---------------------------------------------------------------------
    # OpenRouterLLM Configuration (commented out)
    # ---------------------------------------------------------------------
    # openrouter_llm_config = LLMConfig(
    #     api_type="openai",  # AG2 uses the OpenAI-compatible client
    #     base_url="https://openrouter.ai/api/v1",  # OpenRouter endpoint
    #     api_key=os.environ["OPENROUTER_API_KEY"],  # set this in your env
    #     model=model,  # or e.g. "anthropic/claude-3.5-sonnet"
    #     temperature=0,  # Deterministic output for consistency
    #     cache_seed=None,
    #     parallel_tool_calls=False,
    #     tool_choice="required", # Enforces structured function call sequence
    #     price=[0.00025, 0.001] # Cost per 1000 tokens (numbers not important, but call will fail if not provided)
        
    # )

    llm_config = openai_llm_config

    # ---------------------------
    # System message for Code Writer Agent
    # ---------------------------
    # Defines strict rules for generating complete, error-free,
    # self-contained Python scripts for data processing tasks.
    code_writer_system_message = """You are a skilled Code Writer who writes python code to solve  
    tasks specifically on data exploration, data analysis, data cleaning, feature  
    engineering and data processing tasks.  
    
    Wrap the code in a code block that specifies the script type. 
    The user can't modify your code. So do not suggest incomplete code which requires others to modify. 
    Don't use a code block if it's not intended to be executed by the executor.  
    Don't include multiple code blocks in one response.  
    Do not ask others to copy/paste the result and run it on their own.  
    Check the execution result returned by the executor. If the result indicates there is an error,  
    fix the error and output the code again.  
    Suggest the complete code instead of partial code or code changes.  
    All the variables should be defined. 
    If you are loading data, then load it everytime you write a new piece of code.  
    If the error can't be fixed or if the task is not solved even after the code is executed successfully,  
    analyze the problem, revisit your assumption, collect additional info you need, and think of a  
    different approach to try.  
    The final output of the code will always be either be a Visualization, a CSV file, or simply text. 
    When unclear what should be the final output of the query, prefer to answer the query using visualisation. 
    If it's visualisation or a CSV file, it should be saved externally in the working directory. 
    If the code doesn't generate any file, simply print the text to the console.  
    Don't open saved file (for example using plt.show() in case of visualization), simply save it in  
    the working directory.  
    If there's no code to be written, revert back to Planner agent.
    """

    # ---------------------------
    # Agent definitions
    # ---------------------------

    # Planner: Designs the high-level workflow
    planner = ConversableAgent(
        name="Planner",
        system_message="""You are a skilled Planner. 
        You don't write any code. 
        You suggest a plan of action to solve the user's query. 
        You only give high level plan of action. 
        The plan may involve a Code Writer and/or an Executor. Explain the plan first. 
        Be clear which step is performed by Code Writer, Executor and Planner.  
        Always include reverting back to Planner agent once all the tasks in the plan  
        are completed successfully.
        **After the report has been saved, reply with 'TERMINATE'.**""",
        llm_config=llm_config
    )

    # Code Writer: Generates Python code according to strict output rules
    code_writer = ConversableAgent(
        name="code_writer",
        system_message=code_writer_system_message,
        llm_config=llm_config,
        code_execution_config=False,
    )

    # Local command-line executor for running code
    executor = LocalCommandLineCodeExecutor(
        timeout=10,
        work_dir=out_dir,
    )

    # Code Executor: Executes generated code in isolated environment
    code_executor = ConversableAgent(
        name="code_executor",
        llm_config=False,
        code_execution_config={"executor": executor},
        human_input_mode="NEVER",
    )

    # User agent: Represents the request initiator
    user = ConversableAgent(
        name="user",
        human_input_mode="NEVER"
    )

    # ---------------------------
    # AutoPattern orchestration setup
    # ---------------------------
    pattern = AutoPattern(
        initial_agent=planner,
        agents=[planner, code_writer, code_executor],
        user_agent=user,
        group_manager_args={
            "llm_config": llm_config,
            # Workflow terminates when the Planner outputs "TERMINATE"
            "is_termination_msg": lambda msg: msg.get("content", "").strip() == "TERMINATE"
        }
    )

    # ---------------------------
    # Run the orchestrated workflow
    # ---------------------------
    result, context, last_agent = initiate_group_chat(
        pattern=pattern,
        messages=initial_message_run_2,
        max_rounds=50
    )









