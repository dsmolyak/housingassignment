import csv
from random import choices
from uszipcode import SearchEngine
import xlrd 
from math import radians, cos, sin, asin, sqrt, floor

# Set up file locations
applicant_data = "applicant.csv"
housing_data = "housing.csv"
housing_distribution_data = "housing_distribution.csv"
zipcode_file = "17zp21md.xlsx"

used_zipcodes = []

num_applicants = 562 #5626
num_houses = 292 #2926

def percent_return(dict):
    val_sum = sum(dict.values())
    d_pct = {k: v/val_sum for k, v in dict.items()}
    return next(iter(choices(population=list(d_pct), weights=d_pct.values(), k=1)))



def generate_applicant_data(num_applicants):
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

def generate_housing_data(num_houses):
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
    # matrix = [[0 for x in range(len(used_zipcodes))] for y in range(len(used_zipcodes))] 

    # for i in range(len(used_zipcodes)):
    #     for j in range(len(used_zipcodes)):
    #         data1 = search.by_zipcode(str(used_zipcodes[i])).to_dict()
    #         data2 = search.by_zipcode(str(used_zipcodes[j])).to_dict()

    #         matrix[i][j] = haversine(data1['lng'], data1['lat'], data2['lng'], data2['lat'])

    matrix = {}

    for i in used_zipcodes:
        matrix[i] = {}
        for j in used_zipcodes:
            data1 = search.by_zipcode(str(i)).to_dict()
            data2 = search.by_zipcode(str(j)).to_dict()

            matrix[i][j] = haversine(data1['lng'], data1['lat'], data2['lng'], data2['lat'])

    print(matrix)



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

def main():

    generate_applicant_data(num_applicants)
    generate_housing_data(num_houses)
    create_adjacency_matrix()
  


if __name__ == "__main__":
    main()
