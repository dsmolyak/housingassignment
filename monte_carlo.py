import pandas as pd
import time
from ortools.linear_solver import pywraplp
import csv
from random import choices
from uszipcode import SearchEngine
import xlrd 
from math import radians, cos, sin, asin, sqrt, floor

# Set up file locations
applicant_data = "applicant.csv"
housing_data = "housing.csv"
results_file = "results.csv"
housing_distribution_data = "housing_distribution.csv"
zipcode_file = "17zp21md.xlsx"

num_applicants = 5626
num_houses = 2926

num_iterations = 5

used_zipcodes = []


'''
Mechanism Design
'''

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
        return [total_count, len(housing_df), total_count / len(housing_df)]
    else:
        print('oop.')
        return ["ERROR","ERROR","ERROR"]


'''
Data Generation
'''

def percent_return(dict):
    val_sum = sum(dict.values())
    d_pct = {k: v/val_sum for k, v in dict.items()}
    return next(iter(choices(population=list(d_pct), weights=d_pct.values(), k=1)))



def generate_applicant_data():
    global used_zipcodes

    # Applicant Distributions
    race_distribution = {"Black" : 37.04, "Hispanic" : 15.69, "White" : 43.28, "Other" : 3.55}
    disability_distribution = {"Yes" : 12.8, "No" : 87.2}
    population_distribution = {}

    search = SearchEngine(simple_zipcode=True)
    zipcodes = [int(dict.to_dict()['zipcode']) for dict in search.by_city_and_state(city="Baltimore", state="MD", returns = 0)]

    # Calculate Population Distributions based on zipcodes
    wb = xlrd.open_workbook(zipcode_file) 
    sheet = wb.sheet_by_index(0) 
  
    population_sum = 0
    for i in range(sheet.nrows): 
        try:
            md_code = int(sheet.cell_value(i, 0))

            # Retrieve population of <$25,000 from excel
            if md_code not in population_distribution.keys() and md_code in zipcodes:
                population_distribution.update({int(sheet.cell_value(i + 1, 0)) : int(sheet.cell_value(i + 1, 2))})
                population_sum += int(sheet.cell_value(i + 1, 2))
                used_zipcodes.append(md_code)
        except:
            continue

    # Convert population distribution to weights
    for key, value in population_distribution.items():
        population_distribution.update({key : value / population_sum * 100})

    with open(applicant_data, 'w', newline='') as applicantfile:

        applicantwriter = csv.writer(applicantfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        applicantwriter.writerow(['Applicant #','Race','Disability','Zip Code'])

        for i in range(0,num_applicants):

            # Randomly select factors based on weights and write results to csv
            applicantwriter.writerow([i+1,percent_return(race_distribution),percent_return(disability_distribution),percent_return(population_distribution)])

            applicantfile.flush()

def generate_housing_data():
    global used_zipcodes

    # Housing Distributions
    disability_friendly_distribution = {"Yes" : 3.88, "No" : 96.12}
    public_section_8_distribution = {"Public Housing" : 9851, "Section 8" : 19417}
    housing_zipcode_distribution = {}

    search = SearchEngine(simple_zipcode=True)
    zipcodes = [int(dict.to_dict()['zipcode']) for dict in search.by_city_and_state(city="Baltimore", state="MD", returns = 0)]

    avail_housing_sum = 0
    for zipcode in used_zipcodes:
        zipcode_data = search.by_zipcode(str(zipcode)).to_dict()
        avail_houses = int(zipcode_data['housing_units']) - int(zipcode_data['occupied_housing_units'])
        housing_zipcode_distribution.update({zipcode : avail_houses})
        avail_housing_sum += avail_houses

    # Write Housing Distribution to file
    with open(housing_distribution_data, 'w', newline='') as housingfile:
        housingwriter = csv.writer(housingfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        housingwriter.writerow(['Zip Code','# Houses'])

        for key,value in housing_zipcode_distribution.items():

            housingwriter.writerow([key,floor(value / avail_housing_sum * num_houses)])

            housingfile.flush()

    # Convert housing zipcode distribution to weights
    for key, value in housing_zipcode_distribution.items():
        housing_zipcode_distribution.update({key : value / avail_housing_sum * 100})

    with open(housing_data, 'w', newline='') as housingfile:

        housingwriter = csv.writer(housingfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        housingwriter.writerow(['House #','Disability Friendly', 'Type', 'Zip Code', 'Population','# of Housing Units', '# of Occupied Housing Units','Median Household Income','Median Home Value'])

        for i in range(0,num_houses):

            # Randomly select zipcode for applicant and get data based on zipcode
            selected_zipcode = percent_return(housing_zipcode_distribution)
            zipcode_data = search.by_zipcode(str(selected_zipcode)).to_dict()
            population = zipcode_data['population']
            housing_units = zipcode_data['housing_units']
            occupied_housing_units = zipcode_data['occupied_housing_units']    
            median_household_income = zipcode_data['median_household_income']
            median_home_value = zipcode_data['median_home_value']
            

            # Randomly select factors based on weights and write results to csv
            housingwriter.writerow([i+1,percent_return(disability_friendly_distribution),percent_return(public_section_8_distribution),selected_zipcode, population,housing_units,occupied_housing_units,median_household_income,median_home_value])

            housingfile.flush()


def create_adjacency_matrix():
    global used_zipcodes

    search = SearchEngine(simple_zipcode=True)
    matrix = {}

    for i in used_zipcodes:
        matrix[i] = {}
        for j in used_zipcodes:
            data1 = search.by_zipcode(str(i)).to_dict()
            data2 = search.by_zipcode(str(j)).to_dict()

            matrix[i][j] = haversine(data1['lng'], data1['lat'], data2['lng'], data2['lat'])

    return matrix



def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r


if __name__ == '__main__':

    with open(results_file, 'w', newline='') as resultsfile:

        resultswriter = csv.writer(resultsfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        resultswriter.writerow(['Iteration','Applicants Assigned','Number Houses Available','Percent Allocated'])

        for i in range(num_iterations):
            used_zipcodes = []

            generate_applicant_data()
            generate_housing_data()

            if i != 0:
                location_matrix = create_adjacency_matrix()
            

            applicant_df = pd.read_csv(applicant_data)
            housing_df = pd.read_csv(housing_data)
            race_distribution = {"Black": 37.04, "Hispanic": 15.69, "White": 43.28, "Other": 3.55}

            output_list = [i]
            for output in assign_optimal(race_distribution, applicant_df, housing_df):
                output_list.append(output)

            resultswriter.writerow(output_list)

            resultsfile.flush()

