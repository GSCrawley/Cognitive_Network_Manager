import pandas as pd


# Read the CSV file into a pandas DataFrame as input
data = pd.read_csv('../symptoms_and_diseases.csv')
data = data.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
data = data.apply(lambda x: x.str.rstrip() if x.dtype == "object" else x)

symp_set = set()
symp_set.add('Patient')
symp_set.discard(float('nan'))
# Building New Data Frame for output
for i in range(1, 18):  # Loop through columns 'Symptom_1' to 'Symptom_17'
    column_name = f'Symptom_{i}'
    for symptom_value in data[column_name]:
        if pd.notna(symptom_value) and symptom_value.strip():  # Check if not null and not empty string
            symp_set.add(symptom_value.strip())

#Convert to list
titles_list = sorted(list(symp_set))
titles_list.append('Disease')
column_list = titles_list[1:-1]

# Create an empty list to hold the rows
rows = []

# Fancy loop 
for index, row in data.iterrows():
    # Initialize the row with 0s
    row_data = {col: 0 for col in titles_list}
    
    # Set 'Patient' and 'Disease' values
    row_data['Patient'] = index + 1
    row_data['Disease'] = row['Disease']

    # Set matching symptoms to 1
    for i in row[1:-1]:
        # ignore empty values
        if pd.notna(i):
            # swap 0's to 1's for matching symptoms
            row_data[i] = 1
    rows.append(row_data)

# Create the DataFrame by concatenating the rows list
df = pd.concat([pd.DataFrame([row]) for row in rows], ignore_index=True)

# Fill NaN values with 0
df.fillna(0, inplace=True)

print(df)
df.to_csv('../matrix.csv', index=False)



