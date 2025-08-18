# =============================================================================
# AG2 Survey Analysis Pipeline – Main Orchestrator
# --------
# This script coordinates the full workflow for analyzing cryptocurrency survey data,
# verifying results, and producing a final comprehensive report.
# =============================================================================

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


