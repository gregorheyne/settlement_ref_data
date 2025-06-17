'''
- convert source [00] into a json file
'''
import json
import pdfplumber
import pandas as pd
from datetime import datetime


expected_headers = [
    'Record_creation_date',
    'Last_Update_date',
    'BIC',
    'Brch_Code',
    'Full_legal_name',
    'Registered_address',
    'Operational_address',
    'Branch_description',
    'Branch_address',
    'Instit._Type'
]

print(f'start time: {datetime.now()}')
json_data = dict()
with pdfplumber.open("data_input/00 - ISOBIC.pdf") as pdf:
    for i in range(1, len(pdf.pages)):
    # for i in range(1, 5):
        if i%100==0:
            print(f'page {i} at {datetime.now()}')
        page = pdf.pages[i]
        table = page.extract_table()
        if table:
            df = pd.DataFrame(table[1:], columns=table[0])  # Use first row as headers
            # compare actual and expected headers
            headers = [x.replace('\n', '_').replace(' ', '_') for x in df.columns] 
            if headers != expected_headers:
                print(f'headers differ in page {i}')
                print(f'found headers: {headers}')
            df.columns = headers
            df['bic_long'] = df['BIC'] + df['Brch_Code']
            # convert to json data
            json_data_page = df.set_index("bic_long").to_dict(orient="index")
            # append to main json data
            json_data.update(json_data_page)

print(f'{len(json_data)} dict entries')
print(f'end time: {datetime.now()}')

with open("data_generated/bics_json.json", "w") as file:
    json.dump(json_data, file, indent=4)

for key in json_data.keys():
    if len(key) < 11:
        print(key)

