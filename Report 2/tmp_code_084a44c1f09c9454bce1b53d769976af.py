import pandas as pd

# Load the CSV file
file_path = '/Users/jsand/OneDrive/Desktop/AG2/Code_Interpreter/Crypto_Survey_Data.csv'
df = pd.read_csv(file_path)

# Display basic information about the dataset
info = df.info()

# Display the first few rows to understand the structure
head = df.head()

info, head