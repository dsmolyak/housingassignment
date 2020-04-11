import csv
from random import choices
from uszipcode import SearchEngine
import xlrd 

# Set up file locations
output_file = "data.csv"
zipcode_file = "d:/Documents/College/CMSC828M/housingassignment/17zp21md.xlsx"

num_applicants = 1000

def percent_return(dict):
    val_sum = sum(dict.values())
    d_pct = {k: v/val_sum for k, v in dict.items()}
    return next(iter(choices(population=list(d_pct), weights=d_pct.values(), k=1)))

def main():

    # Distributions
    race_distribution = {"Black" : 45, "Hispanic" : 21, "White" : 32, "Other" : 2}
    disability_distribution = {"Yes" : 20, "No" : 80}
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
        except:
            continue

    # Convert population distribution to weights
    for key, value in population_distribution.items():
        population_distribution.update({key : value / population_sum * 100})

    with open(output_file, 'w', newline='') as csvfile:

        csvwriter = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')

        csvwriter.writerow(['Applicant #','Race','Disability','Zip Code', 'Population','# of Housing Units', '# of Occupied Housing Units','Median Household Income','Median Home Value'])

        for i in range(0,num_applicants):

            # Randomly select zipcode for applicant and get data based on zipcode
            selected_zipcode = percent_return(population_distribution)
            zipcode_data = search.by_zipcode(str(selected_zipcode)).to_dict()
            population = zipcode_data['population']
            housing_units = zipcode_data['housing_units']
            occupied_housing_units = zipcode_data['occupied_housing_units']    
            median_household_income = zipcode_data['median_household_income']
            median_home_value = zipcode_data['median_home_value']
            

            # Randomly select factors based on weights and write results to csv
            csvwriter.writerow([i+1,percent_return(race_distribution),percent_return(disability_distribution),selected_zipcode, population,housing_units,occupied_housing_units,median_household_income,median_home_value])

            csvfile.flush()


if __name__ == "__main__":
    main()
