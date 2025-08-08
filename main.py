# -----------------------------------------------------------------------------------
# AG2 Survey Analysis Pipeline – Main Orchestrator
#
# Purpose:
#   This script coordinates the full workflow for analyzing cryptocurrency survey data,
#   verifying results, and producing a final comprehensive report.
#
# Workflow Overview:
#   1. Generate Report 1  → process_survey_data_1()
#      - Runs the AutoGen workflow to analyze the survey CSV and produce the first report.
#
#   2. Generate Report 2  → process_survey_data_2()
#      - Runs the same analysis workflow to produce an independent second report
#        (ensures reproducibility and detects variance).
#
#   3. Verify Consistency → run_verification()
#      - Compares statistical results between Report 1 and Report 2 to confirm they match.
#      - If discrepancies exist, the verification step will highlight them.
#
#   4. Generate Final Report → generate_final_report()
#      - After verification passes, compiles objectives and survey results into a
#        polished, stakeholder-ready Markdown report.
#
# Models:
#   Each step can be assigned its own LLM model.
#   Currently, all steps are configured to use "gpt-4.1-mini".
#
# Prerequisites:
#   - All dependencies from individual scripts installed (autogen, scipy, tabulate, etc.)
#   - OPENAI_API_KEY set in your environment (.env file recommended).
#   - The survey CSV file and objectives document available in the expected locations.
# -----------------------------------------------------------------------------------

from process_survey_data_1 import process_survey_data_1
from process_survey_data_2 import process_survey_data_2
from verify_survey_data import run_verification
from generate_final_report import generate_final_report

# ---------------------------
# Model assignments for each step
# ---------------------------
process_data_1_model = "gpt-4.1-mini"    # Model for first report generation
process_data_2_model = "gpt-4.1-mini"    # Model for second report generation
verification_model = "gpt-4.1-mini"     # Model for report verification
final_report_model = "gpt-4.1-mini"     # Model for final report creation

# ---------------------------
# Execute full pipeline
# ---------------------------
if __name__ == "__main__":
    # Step 1: Generate first survey analysis report
    process_survey_data_1(process_data_1_model)

    # Step 2: Generate second independent survey analysis report
    process_survey_data_2(process_data_2_model)

    # Step 3: Verify statistical consistency between both reports
    run_verification(verification_model)

    # Step 4: Generate polished final report
    generate_final_report(final_report_model)
