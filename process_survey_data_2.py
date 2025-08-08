# -----------------------------------------------------------------------------------
# AG2 Crypto Survey Data Processing Script (Version 2)
#
# This script is nearly identical to process_survey_data_1, but:
#   - Outputs to "Report 2" directory
#   - Saves results in 'survey_results_run_2.md'
#
# It uses AutoGen's multi-agent orchestration to automatically:
#   1. Create frequency tables for all survey questions
#   2. Generate crosstabulations between first five questions and demographics
#   3. Perform chi-square statistical tests
#   4. Compile results into a single Markdown file
#
# Dependencies:
#   pip install scipy tabulate python-dotenv ag2
#
# Requirements:
#   - An OpenAI API key must be available via environment variable (OPENAI_API_KEY)
#   - CSV file path is hardcoded; adjust before running
# -----------------------------------------------------------------------------------

from pathlib import Path
from autogen import ConversableAgent, LLMConfig
from autogen.coding import LocalCommandLineCodeExecutor
from autogen.agentchat.group.patterns import AutoPattern
from autogen.agentchat import initiate_group_chat
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def process_survey_data_2(model: str):
    """
    Automates cryptocurrency survey analysis using AutoGen's agent collaboration pattern.

    Parameters
    ----------
    model : str
        The OpenAI model name to be used for all LLM-based agents (e.g., "gpt-4").

    Workflow
    --------
    1. Set up an output directory for the report.
    2. Configure LLM parameters for all agents.
    3. Create the following agents:
       - Planner: Produces high-level action plans (no code writing).
       - Code Writer: Generates complete, executable Python scripts.
       - Code Executor: Runs generated scripts locally.
       - User: Represents the requester in the workflow.
    4. Define an AutoPattern coordination framework to manage inter-agent messaging.
    5. Provide initial instructions for:
       - Frequency table generation
       - Crosstabulation creation
       - Chi-square significance testing
       - Markdown report compilation
    6. Run the group chat until the workflow signals "TERMINATE".
    """

    # ---------------------------
    # Create output directory
    # ---------------------------
    out_dir = Path("Report 2")
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------
    # LLM configuration
    # ---------------------------
    llm_config = LLMConfig(
        api_type="openai",
        model=model,
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0,           # Use deterministic outputs
        cache_seed=None,
    )

    # ---------------------------
    # Code Writer Agent system prompt
    # ---------------------------
    # Enforces complete, executable, self-contained code generation for data processing tasks.
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
    # File and report parameters
    # ---------------------------
    file_path = "/Users/jsand/OneDrive/Desktop/AG2/Code_Interpreter/Crypto_Survey_Data.csv"
    report_name = "survey_results_run_2.md"

    # ---------------------------
    # Initial user instructions
    # ---------------------------
    initial_message = f"""
        Please make the analysis of the CSV file {file_path}.
        It contains the results of a survey about cryptocurrencies.

        1. Create frequency tables for each question in the survey. 
        Each table should include the name of the question, as well as the number and percentage of responses 
        for each answer choice. There should also be a total row at the bottom of the table. Remove any missing values, such as 'nan'

        2. For the first five survey questions, create crosstabulations with each of the demographic questions. 
        Each crosstab should show how responses to the survey question vary across different demographic groups.

        3. Perform chi-square tests on each of these crosstabs to identify any statistically significant differences. 
        Clearly indicate which results are statistically significant (e.g., p < 0.05).

        4. Create a final report that includes ALL the frequency tables, crosstabs, and chi-square test results.
        Do not add any additional insights or analysis. 

        **Make sure all the tables and crosstabs are formatted in markdown in ONE file**

        **Save the report in a new file named '{report_name}'**
        """

    # ---------------------------
    # Run the orchestrated workflow
    # ---------------------------
    result, context, last_agent = initiate_group_chat(
        pattern=pattern,
        messages=initial_message,
        max_rounds=50
    )


