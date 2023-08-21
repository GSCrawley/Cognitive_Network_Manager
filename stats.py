import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from scipy.stats import t, ttest_ind

def do_stats_stuff(disease, symptoms):
    # Read the CSV file into a pandas DataFrame as input
    data = pd.read_csv('./updated_symptoms_and_disease.csv')
    data = data.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    data = data.apply(lambda x: x.str.rstrip() if x.dtype == "object" else x)
    new_item = {
        'Disease': 'Test',
    }
    new_item = {'Disease': disease}
    
    for i, symptom in enumerate(symptoms, start=1):
        new_item[f'Symptom_{i}'] = symptom

    # Append the new item to the DataFrame
    data = data.append(new_item, ignore_index=True)
    print(data.tail())
    matrix = make_matrix(data)
    stats = learn(matrix, symptoms)
    data.to_csv('./updated_symptoms_and_disease.csv', index=False)

    return(stats)

def make_matrix(data):
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
    return(df)

# do_stats_stuff(disease, symptoms)
def learn(matrix, user_syptoms):
    df = matrix

    # Step 1: Data Preparation
    X = df.drop(columns=['Disease'])  # Features (symptoms)
    y = df['Disease']  # Target variable (disease)

    # Split the data into training and testing sets (80% training, 20% testing)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Step 2: Model Selection and Training
    model = RandomForestClassifier(random_state=42)

    # Step 3: Model Evaluation with k-fold Cross-Validation
    k = 5  # Number of folds for cross-validation
    cv_scores = cross_val_score(model, X_train, y_train, cv=k)

    # Step 4: Final Model Training and Evaluation on Test Set
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    symptoms = X.columns.tolist()

    user_input = user_syptoms

    # Convert the user input to a dictionary with symptom values (0 or 1)
    symptoms_dict = {symptom: 1 if symptom.strip() in user_input else 0 for symptom in symptoms}

    user_input_df = pd.DataFrame([symptoms_dict])

    predicted_probabilities = model.predict_proba(user_input_df)

    predicted_disease = model.predict(user_input_df)
    print("Predicted Disease:", predicted_disease[0])

    class_probabilities = model.predict_proba(X_test)

    p_values = []
    for i in range(len(predicted_probabilities[0])):
        _, p_value = ttest_ind(class_probabilities[:, i], predicted_probabilities[0][i])
        p_values.append(p_value)

    significance_level = 0.05

    # Print p-values and significant diseases
    print("P-values and Significant Diseases:")
    disease_out = []
    p_value_out=[]
    for disease, p_value in zip(model.classes_, p_values):
        # print(f"{disease}: {p_value}")
        if p_value < significance_level:
            print(f"Significant Disease: {disease} P-value: {p_value}")
            disease_out.append(disease)
            p_value_out.append("{:.4f}".format(p_value))

    # Find the row corresponding to the predicted disease
    predicted_disease_row = df.loc[df['Disease'] == predicted_disease[0]]

    # Extract the correlating symptoms to the predicted disease
    correlating_symptoms = [symptom for symptom in symptoms if predicted_disease_row[symptom].values[0] == 1]

    print("Correlating Symptoms to Predicted Disease:")
    print(correlating_symptoms)
    return(disease_out, p_value_out, correlating_symptoms)

# disease = 'COVID-19'
# symptoms = ['cough', 'breathlessness', 'loss of taste']
# do_stats_stuff(disease, symptoms)
