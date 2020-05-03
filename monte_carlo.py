import assign_housing as ah
import generate_data as gd
import pandas as pd
import csv

# Set up file locations
applicant_data = "applicant.csv"
housing_data = "housing.csv"
results_file = "results.csv"

num_applicants = 562
num_houses = 292

num_iterations = 1

if __name__ == '__main__':

    with open(results_file, 'w', newline='') as resultsfile:

        resultswriter = csv.writer(resultsfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        resultswriter.writerow(['Iteration','Total Applicants Assigned', 'Total # Houses','Disabiled Applicants Assigned',' % Disabiled Applicants Assigned','# Blacks', '# Hispanics','# Whites', '# Others','% Blacks', '% Hispanics','% Whites', '% Others'])

        for i in range(num_iterations):

            gd.generate_applicant_data(num_applicants)
            gd.generate_housing_data(num_houses)

            # if i != 0:
            location_matrix = gd.create_adjacency_matrix()

            applicant_df = pd.read_csv(applicant_data)
            housing_df = pd.read_csv(housing_data)
            race_distribution = {"Black": 37.04, "Hispanic": 15.69, "White": 43.28, "Other": 3.55}

            csv_race_distribution = {"Black": 0, "Hispanic": 0, "White": 0, "Other": 0}
            csv_total_disabled = 0
            # Calculate applicant race distribution and disability from csv
            for index, row in applicant_df.iterrows():
                csv_race_distribution[row['Race']] += 1

                if row['Disability'] == 'Yes':
                    csv_total_disabled += 1

            print(csv_race_distribution)

            output_list = [i + 1]

            optimal_by_unit_output = ah.assign_optimal_by_unit(race_distribution, applicant_df, housing_df, location_matrix)
            for i in range(len(optimal_by_unit_output)):
                output_list.append(optimal_by_unit_output[i])

                # Append disabled %
                if i == 2:
                    output_list.append(optimal_by_unit_output[i] / csv_total_disabled)
            
            i = 4
            for race in csv_race_distribution.keys():
                output_list.append(optimal_by_unit_output[-i] / csv_race_distribution[race])
                i -= 1

            resultswriter.writerow(output_list)

            resultsfile.flush()

