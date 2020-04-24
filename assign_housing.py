import pandas as pd
import time
from ortools.linear_solver import pywraplp


def compile_stats(applicant_df, housing_df, total_assignments, race_assignments, disability_assignments):
    print('%d/%d, %f' % (total_assignments, len(housing_df), total_assignments / len(housing_df) * 100))
    print(race_assignments)
    race_percents = {}
    for race, num in race_assignments.items():
        race_percents[race] = num / len(applicant_df[applicant_df['Race'] == race])
    print(race_percents)
    num_dis_applicants = len(applicant_df[applicant_df['Disability'] == 'Yes'])
    print('%d/%d, %f' % (disability_assignments, num_dis_applicants, disability_assignments / num_dis_applicants * 100))
    print(disability_assignments)


def assign_random(race_dist, applicant_df, housing_df):
    start = time.time()
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

    print('middle', time.time() - start)
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

    print('end', time.time() - start)
    compile_stats(applicant_df, housing_df, total_assignments, race_assignments, disability_assignments)


def assign_optimal(race_dist, applicant_df, housing_df):
    zips = list(set(housing_df['Zip Code']))
    race_limit_map = {}  # find restrictions on how many of each race can be in a zip (proxy for block for now)
    for zip in zips:
        race_limit_map[zip] = {}
        for race, percent in race_dist.items():
            race_limit_map[zip][race] = percent / 100 * len(housing_df[housing_df['Zip Code'] == zip])

    disability_limit_map = {}  # find restrictions on how many people with disabilities can be in a zip
    for zip in zips:
        disability_limit_map[zip] = len(housing_df[(housing_df['Zip Code'] == zip) &
                                                   (housing_df['Disability Friendly'] == 'Yes')])

    solver = pywraplp.Solver('mip_program', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
    infinity = solver.infinity()
    x = {}
    for i in range(0, len(applicant_df)):
        x[i] = {}
        for j in range(0, len(zips)):
            x[i][j] = solver.IntVar(0, 1.0, 'x[%d][%d]' % (i, j))

    # Constraints on one to one matching
    for j in range(0, len(zips)):
        constraint = solver.RowConstraint(0, len(housing_df[housing_df['Zip Code'] == zips[j]]), '')
        for i in range(0, len(applicant_df)):
            constraint.SetCoefficient(x[i][j], 1)
    for i in range(0, len(applicant_df)):
        constraint = solver.RowConstraint(0, 1, '')
        for j in range(0, len(zips)):
            constraint.SetCoefficient(x[i][j], 1)

    # Constraints on race
    race_indices = {}
    for index, row in applicant_df.iterrows():
        if row['Race'] not in race_indices:
            race_indices[row['Race']] = []
        race_indices[row['Race']].append(index)  # Find which indices correspond to each race
    for j in range(0, len(zips)):
        for race, limit in race_limit_map[zips[j]].items():
            constraint = solver.RowConstraint(0, int(limit), '')
            for i in range(0, len(applicant_df)):
                if i in race_indices[race]:
                    constraint.SetCoefficient(x[i][j], 1)  # Only include indices corresponding to current race
                else:
                    constraint.SetCoefficient(x[i][j], 0)

    # Set objective (create utility matrix)
    objective = solver.Objective()
    for i in range(0, len(applicant_df)):
        for j in range(0, len(zips)):
            objective.SetCoefficient(x[i][j], 1)
    objective.SetMaximization()

    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        print('Problem solved in %f milliseconds' % solver.wall_time())
        print()
        total_count = 0
        for i, row in applicant_df.iterrows():
            for j in range(0, len(zips)):
                # print(x[i][j].solution_value())
                if int(x[i][j].solution_value()) == 1.0:
                    total_count += 1
        print(total_count, len(housing_df), total_count / len(housing_df))
    else:
        print('oop.')


if __name__ == '__main__':
    applicant_df = pd.read_csv('applicant.csv')
    housing_df = pd.read_csv('housing.csv')
    race_distribution = {"Black": 37.04, "Hispanic": 15.69, "White": 43.28, "Other": 3.55}

    assign_optimal(race_distribution, applicant_df, housing_df)
