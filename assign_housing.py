import time
from ortools.linear_solver import pywraplp  # https://developers.google.com/optimization/mip/mip_var_array
import numpy as np


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


def assign_lottery(race_dist, applicant_df, housing_df):
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


def assign_optimal_by_zip(race_dist, applicant_df, housing_df):
    zips = list(set(housing_df['Zip Code']))
    race_limit_map = {}  # find restrictions on how many of each race can be in a zip (proxy for block for now)
    for zip in zips:
        race_limit_map[zip] = {}
        total = len(housing_df[housing_df['Zip Code'] == zip])
        for race, percent in race_dist.items():
            limit = round(percent / 100.0 * total)
            race_limit_map[zip][race] = limit

    solver = pywraplp.Solver('mip_program', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
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
            for i in race_indices[race]:
                constraint.SetCoefficient(x[i][j], 1)  # Only include indices corresponding to current race

    # Constraints on applicants with disabilities (all must be matched)
    disability_indices = []
    for index, row in applicant_df.iterrows():
        if row['Disability'] == 'Yes':
            disability_indices.append(index)
    constraint = solver.RowConstraint(len(disability_indices), len(disability_indices), '')
    for j in range(0, len(zips)):
        for i in disability_indices:
            constraint.SetCoefficient(x[i][j], 1)

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


def assign_optimal_by_unit(applicant_df, housing_df, location_matrix, race_dist, disability):
    solver = pywraplp.Solver('mip_program', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
    x = {}
    n = len(applicant_df)
    m = len(housing_df)
    for i in range(0, n):
        x[i] = {}
        for j in range(0, m):
            x[i][j] = solver.IntVar(0, 1.0, 'x[%d][%d]' % (i, j))

    # Constraints on one to one matching
    for j in range(0, m):
        constraint = solver.RowConstraint(0, 1.0, '')
        for i in range(0, n):
            constraint.SetCoefficient(x[i][j], 1.0)
    for i in range(0, n):
        constraint = solver.RowConstraint(0, 1.0, '')
        for j in range(0, m):
            constraint.SetCoefficient(x[i][j], 1.0)

    # Constraints on race
    race_indices = {}

    for index, row in applicant_df.iterrows():
        if row['Race'] not in race_indices:
            race_indices[row['Race']] = []
        race_indices[row['Race']].append(index)  # Find which indices correspond to each race

    if race_dist:
        # find restrictions on how many of each race can be in a zip
        zips = list(set(housing_df['Zip Code']))
        race_limit_map = {}
        for zip in zips:
            race_limit_map[zip] = {}
            total = len(housing_df[housing_df['Zip Code'] == zip])
            for race, percent in race_dist.items():
                limit = round(percent / 100 * total) + 1
                race_limit_map[zip][race] = limit

        zip_indices = {}
        for index, row in housing_df.iterrows():
            if row['Zip Code'] not in zip_indices:
                zip_indices[row['Zip Code']] = []
            zip_indices[row['Zip Code']].append(index)  # Find which indices correspond to each zip
        for zip in zips:
            for race, limit in race_limit_map[zip].items():
                constraint = solver.RowConstraint(0, int(limit), '')
                for i in race_indices[race]:
                    for j in zip_indices[zip]:
                        constraint.SetCoefficient(x[i][j], 1)  # Only include indices corresponding to current race/zip

    # Constraints on disability
    disability_indices = []

    for index, row in applicant_df.iterrows():
        if row['Disability'] == 'Yes':
            disability_indices.append(index)

    if disability:
        constraint = solver.RowConstraint(len(disability_indices), len(disability_indices), '')
        for j in range(0, m):
            for i in disability_indices:
                constraint.SetCoefficient(x[i][j], 1)

        # Constraints on disability friendly housing (must be matched to those with disabilities)
        dis_fr_indices = []
        for index, row in housing_df.iterrows():
            if row['Disability Friendly'] == 'Yes':
                dis_fr_indices.append(index)
        constraint = solver.RowConstraint(len(dis_fr_indices), len(dis_fr_indices), '')
        for j in dis_fr_indices:
            for i in disability_indices:
                constraint.SetCoefficient(x[i][j], 1)
    # Set objective (create utility matrix)
    variance = 1
    distance_utilities = []
    applicant_zips = list(applicant_df['Zip Code'])
    housing_zips = list(housing_df['Zip Code'])
    for i in range(0, n):
        samples = []
        for j in range(0, m):  # This loop takes ~20 seconds due to pandas
            distance = location_matrix[applicant_zips[i]][housing_zips[j]]
            distance = 1.0 if distance == 0 else distance
            sample = max(0, np.random.normal(1.0 / distance, variance))
            samples.append(sample)
        norm_utils = [float(i) / sum(samples) for i in samples]
        distance_utilities.append(norm_utils)

    disability_utilities = []
    disability_list = list(applicant_df['Disability'])
    dis_fr_list = list(housing_df['Disability Friendly'])
    num_matches = len(housing_df[housing_df['Disability Friendly'] == 'Yes']) * \
                  len(applicant_df[applicant_df['Disability'] == 'Yes'])
    f_samples = np.random.f(5, 10, num_matches)
    count = 0
    for i in range(0, n):
        utils = []
        for j in range(0, m):
            if disability_list[i] == 'Yes' and dis_fr_list[j] == 'Yes':
                utils.append(f_samples[count] + 1)
                count += 1
            else:
                utils.append(1)
        disability_utilities.append(utils)

    disability_utilities = np.asarray(disability_utilities)
    distance_utilities = np.asarray(distance_utilities)
    final_utilities = disability_utilities * distance_utilities

    objective = solver.Objective()
    for i, row_a in applicant_df.iterrows():
        for j, row_h in housing_df.iterrows():
            objective.SetCoefficient(x[i][j], final_utilities[i][j])
    objective.SetMaximization()

    status = solver.Solve()

    race_totals = {"Black": 0, "Hispanic": 0, "White": 0, "Other": 0}
    disability_totals = 0
    disability_utility = 0
    distance_utility = 0

    if status == pywraplp.Solver.OPTIMAL:
        print('Problem solved in %f milliseconds' % solver.wall_time())
        print()
        total_count = 0
        for i, row in applicant_df.iterrows():
            for j in range(0, m):
                if int(x[i][j].solution_value()) == 1.0:
                    total_count += 1
                    for key in race_totals.keys():
                        if i in race_indices[key]:
                            race_totals[key] += 1
                            
                    if i in disability_indices:
                        disability_totals += 1

                    disability_utility += disability_utilities[i][j]
                    distance_utility += distance_utilities[i][j]
                    

        output_list = [total_count, len(housing_df), disability_totals, disability_utility, distance_utility]

        for key in race_totals.keys():
            output_list.append(race_totals[key])

        return output_list
    else:
        print('oop.')
        return []
