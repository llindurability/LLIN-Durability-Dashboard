import pandas as pd
import numpy as np

# Create sample survey data
survey_data = {
    'hhid': [f'1221{str(i).zfill(4)}' for i in range(1, 6)],
    'selected_district': ['GULU'] * 5,
    'selected_subcounty': ['AWACH'] * 5,
    'selected_parish': ['PADUNY'] * 5,
    'selected_village': ['PAROMO'] * 5,
    'gpsloc': ['2.9606783 32.3875777 1019.3 4.675'] * 5
}
survey_df = pd.DataFrame(survey_data)
survey_df.to_csv('data/raw/survey.csv', index=False)

# Create sample campaign nets data
campnets_data = {
    'hhid': [f'1221{str(i).zfill(4)}' for i in range(1, 6)],
    'brand': ['Brand A', 'Brand B'] * 3,
    'distribution_date': ['2024-01-01'] * 5
}
campnets_df = pd.DataFrame(campnets_data)
campnets_df.to_csv('data/raw/campnets.csv', index=False)

# Create sample lost nets data
lostnets_data = {
    'hhid': [f'1221{str(i).zfill(4)}' for i in range(1, 3)],
    'reason': ['Damaged', 'Lost'],
    'loss_date': ['2024-03-01', '2024-03-15']
}
lostnets_df = pd.DataFrame(lostnets_data)
lostnets_df.to_csv('data/raw/lostnets.csv', index=False) 