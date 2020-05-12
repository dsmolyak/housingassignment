import matplotlib.pyplot as plt
import csv

results_folder = "results"
graph_folder = "graphs"

x = []
y = []

with open(results_folder + "/" + "control.csv",'r') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',')
    next(csvreader, None) #skip headers
    for row in csvreader:
        x.append(int(row[0]))
        y.append(float(row[5]))

plt.plot(x,y, label='Disability Utility')
plt.xlabel('Iteration')
plt.ylabel('Disability Utility')
plt.title('Disability Utility')
plt.legend()
plt.savefig(graph_folder + "/" + "control.png")