# Import required libraries
import pandas as pd

# Import necessary classes and functions from the AG2 framework and utility modules
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager, register_function
from utils import get_openai_api_key

# Retrieve OpenAI API key and define configuration for the LLM
OPENAI_API_KEY = get_openai_api_key()
llm_config = {
    "api_type": "openai", 
    "model": "gpt-4o",
    "cache_seed": None
}

# Utility function to read the schema of a CSV file (only reads first 5 rows for efficiency)
def get_csv_schema(file_path: str) -> str:
	try:
		df = pd.read_csv(file_path, nrows=5)
		schema = df.dtypes.to_dict()
		schema_str = "Columns and Data Types:\n"
		for col, dtype in schema.items():
			schema_str += f"  - {col}: {dtype}\n"
		return schema_str
	except Exception as e:
		return f"Error reading CSV schema: {e}"

# Main function that orchestrates the data analysis process through a group chat of agents
def run_survey_data_processing():
    """Run the group chat that processes the survey data into frequency tables."""
    print("Initiating Data Processing...")

    # Define the Planner agent, responsible for outlining a high-level strategy (no coding)
    planner = AssistantAgent(
        name="Planner", 
        system_message="""You are a skilled Planner. 
        You don't write any code. 
        You suggest a plan of action to solve the user's query. 
        You only give high level plan of action. 
        The plan may involve a Programmer and/or an Executor. Explain the plan first. 
        Be clear which step is performed by programmer, executor and itself.  
        Always include reverting back to Planner agent once all the tasks in the plan  
        are completed successfully.
        After the report has been saved, instruct the Programmer to reply with 'TERMINATE'.""",
        llm_config=llm_config
    )

    # Define the Programmer agent, responsible for writing code related to data tasks
    programmer = AssistantAgent(
        name="Programmer",
        system_message="""You are a skilled Programmer who writes python code to solve  
        tasks specifically on data exploration, data analysis, data cleaning, feature  
        engineering and modelling tasks.  
        
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
        After the report has been saved, reply with 'TERMINATE'.""",
        llm_config=llm_config,
    )

    # Define the Executor agent, responsible for executing the Programmer’s code
    executor = UserProxyAgent(
        name="Executor",
        system_message="Executor. Execute the code written by the Programmer and report the result back to it.",
        description="Executor that executes the code written by the Programmer agent.",
        human_input_mode="NEVER",  # This disables manual input—Executor acts autonomously
        code_execution_config={
            "last_n_messages": 3,
            "use_docker": False,
            "work_dir": "static",  # Directory where any output files will be saved
        },
        is_termination_msg=lambda x: x.get("content") == "TERMINATE"
    )

    # Register the schema-checking function so the Programmer can call it when needed
    register_function(
        get_csv_schema,
        caller=programmer,
        executor=executor,
        description="""Tool function that reads a CSV file and returns a string describing its schema 
        (column names and data types). Reads only a few rows for efficiency.""",
    )

    # Create a group chat among the Planner, Programmer, and Executor agents
    groupchat = GroupChat(
        agents=[planner, programmer, executor], 
        max_round=25,
        send_introductions=True,
        messages=[]
    )

    # Instantiate the GroupChatManager that will facilitate message passing and control flow
    manager = GroupChatManager(
        groupchat=groupchat, 
        llm_config=llm_config,
        is_termination_msg=lambda x: x.get("content") == "TERMINATE"
    )

    # Path to the CSV survey data file
    file_path = "/Users/jsand/OneDrive/Desktop/AG2 Portfolio Projects/quant_analysis_and_sequential_swarm/data/Crypto_Survey_Data.csv"

    # Define the user's initial message with detailed instructions for data analysis
    initial_message = f"""
    Please make the analysis of the CSV file {file_path}.
    It contains the results of a survey about cryptocurrencies.

    1. Create frequency tables for each question in the survey. 
    Each table should include the name of the question, as well as the number and percentage of responses 
    for each answer choice.

    2. For the first five survey questions, create crosstabulations with each of the demographic questions. 
    Each crosstab should show how responses to the survey question vary across different demographic groups.

    3. Perform chi-square tests on each of these crosstabs to identify any statistically significant differences. 
    Clearly indicate which results are statistically significant (e.g., p < 0.05).

    4. Create a final report that includes ALL the frequency tables, crosstabs, and chi-square test results.
    Do not add any additional insights or analysis. 

    **Make sure all the tables and crosstabs are formatted in markdown in ONE file**

    **Save the report in a new file named 'survey_results.md'**
    """

    # Start the chat between the agents using the user’s message as the initial prompt
    chat_result = executor.initiate_chat(
        recipient=manager,
        message=initial_message,
        summary_method="reflection_with_llm",  # Summarize using LLM-based reflection
    )

