import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from scipy.stats import t, ttest_ind

df = pd.read_csv('../matrix.csv')

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

# Calculate accuracy on the test set
accuracy = accuracy_score(y_test, y_pred)
print("Test Set Accuracy:", accuracy)

# Print classification report for precision, recall, and F1-score on the test set
# print(classification_report(y_test, y_pred))


# Now, get symptoms as input from the user and make a prediction
symptoms = X.columns.tolist()  # List of all symptoms from the dataframe
user_input = input("Enter a comma-separated list of symptoms (e.g., itching,sweating,vomiting): ").split(',')

# Convert the user input to a dictionary with symptom values (0 or 1)
symptoms_dict = {symptom: 1 if symptom.strip() in user_input else 0 for symptom in symptoms}

user_input_df = pd.DataFrame([symptoms_dict])

predicted_probabilities = model.predict_proba(user_input_df)

predicted_disease = model.predict(user_input_df)
print("Predicted Disease:", predicted_disease[0])
# Print the cross-validation scores for each fold
print("Cross-Validation Scores:", cv_scores)

# Print the average cross-validation accuracy
print("Average Cross-Validation Accuracy:", cv_scores.mean())

class_probabilities = model.predict_proba(X_test)

p_values = []
for i in range(len(predicted_probabilities[0])):
    _, p_value = ttest_ind(class_probabilities[:, i], predicted_probabilities[0][i])
    p_values.append(p_value)

significance_level = 0.05

# Print p-values and significant diseases
print("P-values and Significant Diseases:")
for disease, p_value in zip(model.classes_, p_values):
    # print(f"{disease}: {p_value}")
    if p_value < significance_level:
        print(f"Significant Disease: {disease} P-value: {p_value}")

# Find the row corresponding to the predicted disease
predicted_disease_row = df.loc[df['Disease'] == predicted_disease[0]]

# Extract the correlating symptoms to the predicted disease
correlating_symptoms = [symptom for symptom in symptoms if predicted_disease_row[symptom].values[0] == 1]

print("Correlating Symptoms to Predicted Disease:")
print(correlating_symptoms)