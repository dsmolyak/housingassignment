from ortools.linear_solver import pywraplp  # https://developers.google.com/optimization/mip/mip_var_array
import numpy as np


def find_race_limits(race_dist, housing_df):
    zips = set(housing_df['Zip Code'])
    race_limit_map = {}
    for zip_code in zips:
        race_limit_map[zip_code] = {}
        total = len(housing_df[housing_df['Zip Code'] == zip_code])
        for race, percent in race_dist.items():
            limit = round(percent / 100 * total) + 1
            race_limit_map[zip_code][race] = limit
    return race_limit_map


def calc_distance_utilities(applicant_df, housing_df, location_matrix, variance):
    distance_utilities = []
    applicant_zips = list(applicant_df['Zip Code'])
    housing_zips = list(housing_df['Zip Code'])
    for i in range(0, len(applicant_df)):
        samples = []
        for j in range(0, len(housing_df)):
            distance = location_matrix[applicant_zips[i]][housing_zips[j]]
            distance = 1.0 if distance == 0 else distance
            sample = max(0, np.random.normal(1.0 / distance, variance))
            samples.append(sample)
        norm_utils = [float(i) / sum(samples) for i in samples]
        distance_utilities.append(norm_utils)

    return distance_utilities


def calc_disability_utilities(applicant_df, housing_df):
    disability_utilities = []
    disability_list = list(applicant_df['Disability'])
    dis_fr_list = list(housing_df['Disability Friendly'])
    num_matches = len(housing_df[housing_df['Disability Friendly'] == 'Yes']) * \
                  len(applicant_df[applicant_df['Disability'] == 'Yes'])
    f_samples = np.random.f(5, 10, num_matches)
    count = 0
    for i in range(0, len(applicant_df)):
        utils = []
        for j in range(0, len(housing_df)):
            if disability_list[i] == 'Yes' and dis_fr_list[j] == 'Yes':
                utils.append(f_samples[count] + 1)
                count += 1
            else:
                utils.append(1)
        disability_utilities.append(utils)

    return disability_utilities


def compile_stats(x, disability_utilities, distance_utilities, applicant_df, m):
    race_totals = {"Black": 0, "Hispanic": 0, "White": 0, "Other": 0}
    disability_totals = 0
    disability_utility = 0
    distance_utility = 0
    total_count = 0

    race_list = list(applicant_df['Race'])
    disability_list = list(applicant_df['Disability'])
    for i in range(0, len(applicant_df)):
        for j in range(0, m):
            if x[i][j] == 1.0:
                total_count += 1
                race_totals[race_list[i]] += 1
                if disability_list[i] == 'Yes':
                    disability_totals += 1

                disability_utility += disability_utilities[i][j]
                distance_utility += distance_utilities[i][j]

    output_list = [total_count, m, disability_totals, disability_utility, distance_utility]

    for key in race_totals.keys():
        output_list.append(race_totals[key])

    return output_list


def assign_lottery(applicant_df, housing_df, location_matrix, race_dist, disability):
    if disability:
        applicant_df = applicant_df.sort_values(by=['Disability'], ascending=False)

    race_limit_map = {}
    if race_dist:
        race_limit_map = find_race_limits(race_dist, housing_df)

    zips = set(housing_df['Zip Code'])

    disability_limit_map = {}  # find restrictions on how many people with disabilities can be in a zip
    for zip_code in zips:
        disability_limit_map[zip_code] = len(housing_df[(housing_df['Zip Code'] == zip_code) &
                                                        (housing_df['Disability Friendly'] == 'Yes')])

    variance = 1
    distance_utilities = calc_distance_utilities(applicant_df, housing_df, location_matrix, variance)
    disability_utilities = calc_disability_utilities(applicant_df, housing_df)
    disability_utilities = np.asarray(disability_utilities) * np.asarray(distance_utilities)

    x = np.zeros((len(applicant_df), len(housing_df)))
    assigned = {}
    disability_list = list(applicant_df['Disability'])
    dis_fr_list = list(housing_df['Disability Friendly'])
    race_list = list(applicant_df['Race'])
    zip_list = list(housing_df['Zip Code'])
    for i in range(0, len(applicant_df)):
        ordered_preferences = np.argsort(disability_utilities[i])[::-1]
        for j in ordered_preferences:
            if j in assigned:
                continue
            elif disability and disability_list[i] == 'No' and dis_fr_list[j] == 'Yes':
                continue
            elif race_dist and race_limit_map[zip_list[j]][race_list[i]] <= 0:
                continue
            else:
                assigned[j] = True
                x[i][j] = 1.0
                if race_dist:
                    race_limit_map[zip_list[j]][race_list[i]] -= 1
                break

    return compile_stats(x, disability_utilities, distance_utilities, applicant_df, len(housing_df))


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
        race_limit_map = find_race_limits(race_dist, housing_df)

        zip_indices = {}
        for index, row in housing_df.iterrows():
            if row['Zip Code'] not in zip_indices:
                zip_indices[row['Zip Code']] = []
            zip_indices[row['Zip Code']].append(index)  # Find which indices correspond to each zip
        for zip_code in zips:
            for race, limit in race_limit_map[zip_code].items():
                constraint = solver.RowConstraint(0, int(limit), '')
                for i in race_indices[race]:
                    for j in zip_indices[zip_code]:
                        constraint.SetCoefficient(x[i][j], 1)  # Only include indices corresponding to current race/zip

    # Constraints on disability
    disability_indices = []

    for index, row in applicant_df.iterrows():
        if row['Disability'] == 'Yes':
            disability_indices.append(index)

    # Constraints on disability friendly housing (must be matched to those with disabilities)
    dis_fr_indices = []
    for index, row in housing_df.iterrows():
        if row['Disability Friendly'] == 'Yes':
            dis_fr_indices.append(index)

    if disability:
        constraint = solver.RowConstraint(len(disability_indices), len(disability_indices), '')
        for j in range(0, m):
            for i in disability_indices:
                constraint.SetCoefficient(x[i][j], 1)

        constraint = solver.RowConstraint(len(dis_fr_indices), len(dis_fr_indices), '')
        for j in dis_fr_indices:
            for i in disability_indices:
                constraint.SetCoefficient(x[i][j], 1)

    # Set objective (create utility matrix)
    variance = 1
    distance_utilities = calc_distance_utilities(applicant_df, housing_df, location_matrix, variance)
    disability_utilities = calc_disability_utilities(applicant_df, housing_df)
    disability_utilities = np.asarray(disability_utilities) * np.asarray(distance_utilities)

    objective = solver.Objective()
    for i, row_a in applicant_df.iterrows():
        for j, row_h in housing_df.iterrows():
            objective.SetCoefficient(x[i][j], disability_utilities[i][j])
    objective.SetMaximization()

    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        print('Problem solved in %f milliseconds' % solver.wall_time(), flush=True)
        print()
        x_ = np.zeros((n, m))
        for i in range(0, n):
            for j in range(0, m):
                x_[i][j] = x[i][j].solution_value()

        return compile_stats(x_, disability_utilities, distance_utilities, applicant_df, m)
    else:
        print('oop.')
        return []
