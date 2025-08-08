import pandas as pd

# Load the CSV file
file_path = '/Users/jsand/OneDrive/Desktop/AG2/Code_Interpreter/Crypto_Survey_Data.csv'
df = pd.read_csv(file_path)

# Function to create frequency table for a given column
def create_frequency_table(series):
    # Remove missing values
    series_clean = series.dropna()
    counts = series_clean.value_counts()
    percentages = series_clean.value_counts(normalize=True) * 100
    freq_table = pd.DataFrame({
        'Count': counts,
        'Percentage': percentages.round(2)
    })
    # Add total row
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

# Example: print frequency table for the first question
# print(frequency_tables[df.columns[0]])

# Save frequency tables for report generation
frequency_tables