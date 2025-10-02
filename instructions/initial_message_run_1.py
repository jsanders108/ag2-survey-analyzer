# ---------------------------
# File paths and report names
# ---------------------------
file_path = "/Users/jsand/OneDrive/Desktop/AG2/LinkedIn Projects/Code_Interpreter/Crypto_Survey_Data.csv"
report_name = "survey_results_run_1.md"

initial_message_run_1 = f"""
        Please make the analysis of the CSV file {file_path}.
        It contains the results of a survey about cryptocurrencies.

        1. Create frequency tables for each question in the survey. 
        Each table should include the name of the question, as well as the number and percentage of responses 
        for each answer choice. There should also be a total row at the bottom of the table. Remove any missing values, such as 'nan'

        2. For the first five survey questions, create crosstabulations with each of the demographic questions. 
        Each crosstab should show how responses to the survey question vary across different demographic groups.

        Here are the demographic questions:
        - "Overall, how would you rate your computer skills? (e.g., your ability to learn and use software programs, use a smartphone device, etc.)"
        - "How old are you?"
        - "Which of the following best describes your education status?"
        - "What is your gender?"
        - "What is your current annual household income level?"

        When creating the crosstabs, collapse the categories of the demographic questions 
        into a smaller number of categories, as follows:
        - "Overall, how would you rate your computer skills?": "Excellent/Very Good", "Moderate", "Poor/Very Poor"
        - "How old are you?": "18-34", "35-54", "55+"
        - "Which of the following best describes your education status?": "Less than high school/High school", "University Undergraduate (Bachelor's degree)", "University Postgraduate (Master's or Doctoral degree)", "Other"
        - "What is your gender?": "Male", "Female"
        - "What is your current annual household income level?": "Under $39,999", "$40,000 to $79,999", "$80,000 to $119,999", "$120,000 or more"
    

        3. Perform chi-square tests on each of these crosstabs to identify any statistically significant differences. 
        Clearly indicate which results are statistically significant (e.g., p < 0.05).

        4. Create a final report that includes ALL the frequency tables, crosstabs, and chi-square test results.
        Do not add any additional insights or analysis. 

        **Make sure all the tables and crosstabs are formatted in markdown in ONE file**

        **Save the report in a new file named '{report_name}'**
        """


initial_message_old = f"""
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