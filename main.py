# Import AG2 framework
import autogen

# Import the function to process survey data (generates frequency tables, crosstabs, chi-square tests)
from data_processing_groupchat import run_survey_data_processing

# Import the swarm analysis functions 
from survey_analysis_swarm import run_survey_analysis_swarm

# Import the function to read and load survey objectives and results
from survey_analysis_swarm import read_objectives_and_results

# Import the shared context dictionary used by all agents in the swarm
from survey_analysis_swarm import shared_context


# === MAIN EXECUTION FLOW ===
# First: Run a multi-agent groupchat (Planner, Programmer, Executor) to process survey data
# Then: Run a swarm of agents (Drafting, Review, Revision, Finalization, Recorder) to analyze results and produce a final report
if __name__ == "__main__":
    run_survey_data_processing()  # Step 1: Create survey_results.md via groupchat
    read_objectives_and_results(shared_context)  # Step 2: Load results and objectives into context for swarm
    run_survey_analysis_swarm()  # Step 3: Launch swarm to analyze and refine the results
