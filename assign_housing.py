import pandas as pd
import random


def assign(race_dist, applicant_df, housing_df):
    zips = set(housing_df['Zip Code'])
    race_limit_map = {} # find restrictions on how many of each race can be in a zip (proxy for block for now)
    for zip in zips:
        race_limit_map[zip] = {}
        for race, percent in race_dist.items():
            race_limit_map[zip][race] = percent / 100 * len(housing_df[housing_df['Zip Code'] == zip])

    disability_limit_map = {} # find restrictions on how many people with disabilities can be in a zip
    for zip in zips:
        disability_limit_map[zip] = len(housing_df[(housing_df['Zip Code'] == zip) &
                                                   (housing_df['Disability Friendly'] == 'Yes')])

    total_assignments = 0
    race_assignments = {}
    disability_assignments = 0
    for index, row in applicant_df.iterrows():
        race = row['Race']
        disability = row['Disability']
        zip = row['Zip Code']

        if race_limit_map[zip][race] > 0:
            if disability == 'Yes' and disability_limit_map[zip] > 0:
                disability_limit_map[zip] -= 1
                disability_assignments += 1
            elif disability == 'Yes':
                continue
            race_limit_map[zip][race] -= 1
            if race not in race_assignments:
                race_assignments[race] = 0
            race_assignments[race] += 1
            total_assignments += 1

    print(total_assignments)
    print(race_assignments)
    print(disability_assignments)


if __name__ == '__main__':
    applicant_df = pd.read_csv('applicant.csv')
    housing_df = pd.read_csv('housing.csv')
    race_distribution = {"Black": 45, "Hispanic": 21, "White": 32, "Other": 2}

    assign(race_distribution, applicant_df, housing_df)
