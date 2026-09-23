import pandas as pd
df = pd.DataFrame({'ID':[3,7,2,4,6,5,1],'x':['c','a','b','a','b','c','b']})
sorted_df = df.sort_values(by=['ID','x'])
result = sorted_df.drop_duplicates(subset='x',keep='first').reset_index(drop=True)
print(result)