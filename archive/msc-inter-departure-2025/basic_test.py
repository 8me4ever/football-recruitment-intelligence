print("Basic test - Python is working!")
import pandas as pd
print("Pandas imported successfully")

try:
    df = pd.read_csv('Inter_Players_Departure_Labels.csv')
    print(f"Loaded {len(df)} departure labels")
    print("First few rows:")
    print(df.head())
except Exception as e:
    print(f"Error: {e}")

print("Test complete!")