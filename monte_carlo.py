import assign_housing as ah
import generate_data as gd
import pandas as pd
import csv

# Set up file locations
applicant_data = "generated_data/applicant.csv"
housing_data = "generated_data/housing.csv"
experiments_file = "experiments.csv"
results_folder = "results"




if __name__ == '__main__':


    experiments_df = pd.read_csv(experiments_file)

    for experimentindex, experimentrow in experiments_df.iterrows():

        

        with open(results_folder + "/" + experimentrow['Name'] + ".csv", 'w', newline='') as resultsfile:

            resultswriter = csv.writer(resultsfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
            resultswriter.writerow(['Iteration','Total-Applicants-Assigned', 'Total-#-Houses','Disabiled-Applicants-Assigned', '%-Disabiled-Applicants-Assigned','Disability-Utility','Distance-Utility','#-Blacks', '#-Hispanics','#-Whites', '#-Others','%-Blacks', '%-Hispanics','%-Whites', '%-Others'])

            for i in range(experimentrow['Iterations']):
                

                gd.generate_applicant_data(int(experimentrow['NumApplicants']))
                gd.generate_housing_data(int(experimentrow['NumHouses']))

                # if i != 0:
                location_matrix = gd.create_adjacency_matrix()

                applicant_df = pd.read_csv(applicant_data)
                housing_df = pd.read_csv(housing_data)

                if experimentrow['RaceDistribution'] == 'Yes':
                    race_distribution = {"Black": float(experimentrow['Black']), "Hispanic": float(experimentrow['Hispanic']), "White": float(experimentrow['White']), "Other": float(experimentrow['Other'])}
                else:
                    race_distribution = {}

                csv_race_distribution = {"Black": 0, "Hispanic": 0, "White": 0, "Other": 0}
                csv_total_disabled = 0
                # Calculate applicant race distribution and disability from csv
                for index, row in applicant_df.iterrows():
                    csv_race_distribution[row['Race']] += 1

                    if row['Disability'] == 'Yes':
                        csv_total_disabled += 1

                print(csv_race_distribution)

                output_list = [i + 1]

                lottery_output = ah.assign_lottery(applicant_df, housing_df, location_matrix, race_distribution,
                                                   experimentrow['Disability'] == 'Yes')

                print(lottery_output)
                optimal_by_unit_output = ah.assign_optimal_by_unit(applicant_df, housing_df, location_matrix,
                                                                   race_distribution, experimentrow['Disability'] == 'Yes')
                print(optimal_by_unit_output)

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

