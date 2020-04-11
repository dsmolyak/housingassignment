import csv
from random import choices

# Set up file locations
data_file = "data.csv"

race_distribution = {"Black" : 0, "Hispanic" : 0, "White" : 0, "Other" : 0}
disability_distribution = {"Yes" : 0, "No" : 0}

def main():

    i = 0
    with open(data_file, 'r', newline='',errors='ignore') as csvfile:

        csvreader = csv.reader(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)

        for row in csvreader:

            if i == 0:
                i += 1
                continue

            race_distribution[row[0]] += 1
            disability_distribution[row[1]] += 1
            i += 1

        print(race_distribution,disability_distribution)

if __name__ == "__main__":
    main()
