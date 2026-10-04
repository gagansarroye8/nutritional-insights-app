# TEMPORARY data_analysis.py - only to test the CI/CD pipeline.
# Replace this with the real file from the Task 1 teammate.
import pandas as pd

df = pd.read_csv("All_Diets.csv")

macros = ["Protein(g)", "Carbs(g)", "Fat(g)"]
df[macros] = df[macros].fillna(df[macros].mean())

avg_macros = df.groupby("Diet_type")[macros].mean()
print("Average macronutrients per diet type:")
print(avg_macros)
