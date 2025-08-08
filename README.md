# AG2: Cryptocurrency Survey Analyzer

## Overview & Background
**The Challenge**:  
Market researchers traditionally spend hours—sometimes days—manually cleaning survey data, running statistical tests, and building formatted reports. This process is prone to human error, especially when reconciling multiple versions of the same analysis.

**The Solution**:  
This project demonstrates how **AG2 multi-agent workflows** can automate and accelerate survey data analysis—turning what might be a multi-day process into a matter of minutes, without sacrificing analytical rigor or reproducibility.

Our example analyzes data from a **synthetic (mock) survey** on public attitudes toward cryptocurrencies. The workflow not only produces statistical summaries but also:
- **Reproduces the analysis twice** (independently) to verify accuracy.
- **Checks** that all numerical results match across runs before final synthesis.
- **Generates** a polished, stakeholder-ready final report through an iterative draft → review → revise → finalize loop.

---

## Survey Objectives
From the [survey objectives document](documents/survey_objectives.md):

The survey explored:
1. **Awareness of and familiarity with cryptocurrencies**
2. **Ownership** – whether respondents currently own cryptocurrencies, and which ones
3. **Ownership reasons** – why or why not respondents own cryptocurrencies
4. **Attitudes** toward cryptocurrencies
5. **Future purchase likelihood**

**Methodology**:  
- 18-question survey distributed Dec 22–28, 2022 to U.S. respondents via QuestionPro Audience panel  
- N = 178 completed surveys  
- Weighted by gender (due to oversampling of females at 69%)  
- Originally processed using SPSS

---

## Who This Is For
- **Market Research Teams** looking to speed up survey analysis
- **Consultants & Agencies** juggling multiple client studies
- **Product & Strategy Teams** needing rapid, reliable insights
- **Data Scientists** seeking reproducibility in analysis workflows

---

## Workflow Overview

The system consists of **four sequential steps**, each handled by its own script, orchestrated in `main.py`:

### 1. **Generate Report 1** – `process_survey_data_1.py`
- Cleans survey data and removes missing values
- Generates frequency tables for each question (counts & %)
- Creates crosstabs for the first five survey questions vs. demographic variables
- Performs chi-square significance tests
- Outputs results as `Report 1/survey_results_run_1.md`

---

### 2. **Generate Report 2** – `process_survey_data_2.py`
- Repeats the same workflow independently
- Outputs results as `Report 2/survey_results_run_2.md`
- Serves as a reproducibility check

---

### 3. **Verify Consistency** – `verify_survey_data.py`
- Compares `Report 1` and `Report 2`  
- Ignores wording/formatting differences  
- Flags **any numerical/statistical mismatches**  
- Verification must pass before proceeding

---

### 4. **Generate Final Report** – `generate_final_report.py`
- Reads:
  - Survey objectives
  - Verified survey results
- Runs a **multi-agent feedback loop**:
  1. **Create** – Draft final report synthesizing survey findings in context of objectives
  2. **Review** – Critically assess clarity, accuracy, and completeness
  3. **Revise** – Apply feedback and improve
  4. **Finalize** – Polish for delivery
- Saves `final_survey_report.md`

---

## Iterative Feedback Loop (Quality First)
The **final report stage** uses AG2's staged iteration pattern to enforce quality:

**Stages:**
1. **Create** – AI generates the first draft from objectives and data  
2. **Review** – Separate AI agent checks the draft against the brief and data  
3. **Revise** – AI incorporates review feedback, logs changes  
4. **Finalize** – Minor polishing; outputs decision-ready Markdown

**Quality gates:**
- Full coverage of stated objectives
- All statistics traceable to verified data
- Clear, well-structured Markdown
- Ends with `# End of Report`

---

## System Architecture

### Entry Point (`main.py`)
Runs the full workflow in sequence:
1. `process_survey_data_1`
2. `process_survey_data_2`
3. `run_verification`
4. `generate_final_report`

### Report Generators (`process_survey_data_1.py` / `process_survey_data_2.py`)
- Configure Planner, Code Writer, and Code Executor agents
- Handle CSV ingestion, table generation, and statistical testing
- Output Markdown reports

### Verification (`verify_survey_data.py`)
- Reads and compares both reports
- Passes verification result and feedback

### Final Report Creator (`generate_final_report.py`)
- Uses draft → review → revise → finalize loop
- Produces polished, stakeholder-ready report

---

## Running the Project

### 1. Install Dependencies
```bash
pip install autogen scipy tabulate python-dotenv pydantic
```

### 2. Set Your API Key
Create a .env file:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Ensure Required Inputs
- Survey CSV file (path set in process_survey_data_1.py & process_survey_data_2.py)
- documents/survey_objectives.md

### 4. Run the Pipeline
```bash
python main.py
```

## Outputs
After running main.py successfully, you'll have:

- **Report 1**: Report 1/survey_results_run_1.md
- **Report 2**: Report 2/survey_results_run_2.md
- **Final Report**: final_survey_report.md

---

## Conclusion
This project shows how AG2 multi-agent workflows can transform survey analysis:

- **Faster** – From days to minutes
- **More reliable** – Independent replication & verification step ensures accuracy
- **Higher quality** – Iterative feedback loop produces a polished final report

By automating the tedious, error-prone parts of quantitative market research, AG2 frees analysts to focus on interpretation, storytelling, and strategic recommendations.
