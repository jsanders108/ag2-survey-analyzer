import pandas as pd
from scipy.stats import chi2_contingency

# Load the CSV file
file_path = '/Users/jsand/OneDrive/Desktop/AG2/Code_Interpreter/Crypto_Survey_Data.csv'
df = pd.read_csv(file_path)

# Define survey and demographic questions
survey_questions = [
    "Have you ever heard or read about cryptocurrencies such as Bitcoin and Ethereum?",
    "How familiar are you with cryptocurrencies in general?",
    "What is your overall opinion of cryptocurrencies?",
    "Which of the following statements applies to you?",
    "How likely are you to purchase cryptocurrency in the future?"
]

demographic_questions = [
    "Overall, how would you rate your computer skills? (e.g., your ability to learn and use software programs, use a smartphone device, etc.)",
    "How old are you?",
    "Which of the following best describes your education status?",
    "What is your gender?",
    "What is your current annual household income level?"
]

# Function to create frequency table for a given column
def create_frequency_table(series):
    series_clean = series.dropna()
    counts = series_clean.value_counts()
    percentages = series_clean.value_counts(normalize=True) * 100
    freq_table = pd.DataFrame({
        'Count': counts,
        'Percentage': percentages.round(2)
    })
    total_row = pd.DataFrame({
        'Count': [counts.sum()],
        'Percentage': [percentages.sum().round(2)]
    }, index=['Total'])
    freq_table = pd.concat([freq_table, total_row])
    return freq_table

# Create frequency tables for all questions
frequency_tables = {}
for col in df.columns:
    frequency_tables[col] = create_frequency_table(df[col])

# Prepare markdown report content
report_lines = []

# Add frequency tables to report
for question, table in frequency_tables.items():
    report_lines.append(f"## Frequency Table: {question}\n")
    report_lines.append(table.to_markdown())
    report_lines.append("\n")

# Create crosstabs and perform chi-square tests
for survey_q in survey_questions:
    for demo_q in demographic_questions:
        # Drop rows with missing values in either column
        subset = df[[survey_q, demo_q]].dropna()
        crosstab = pd.crosstab(subset[survey_q], subset[demo_q])
        
        # Perform chi-square test
        chi2, p, dof, expected = chi2_contingency(crosstab)
        
        # Format crosstab for markdown
        report_lines.append(f"## Crosstab: {survey_q} vs {demo_q}\n")
        report_lines.append(crosstab.to_markdown())
        report_lines.append("\n")
        
        # Add chi-square test result
        significance = "Yes" if p < 0.05 else "No"
        report_lines.append(f"**Chi-square test results:**\n\n- Chi2 Statistic: {chi2:.4f}\n- Degrees of Freedom: {dof}\n- p-value: {p:.4f}\n- Statistically Significant (p < 0.05): {significance}\n\n")

# Save the report to a markdown file
report_content = "\n".join(report_lines)
with open("survey_results_run_2.md", "w") as f:
    f.write(report_content)