import json
import collections

file_path = r'c:\Users\hanok\wordpress\scripts\tools\sociam_stock_processing\data\colors_map.json'

with open(file_path, 'r', encoding='utf-8') as f:
    # Load into a list of tuples to handle potential issues, but standard json.load 
    # will just take the last occurrence of a duplicate key.
    data = json.load(f)

# Sort the dictionary by key for better maintainability
sorted_data = collections.OrderedDict(sorted(data.items()))

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(sorted_data, f, indent=4, ensure_ascii=False)

print("JSON file deduplicated and sorted successfully.")
