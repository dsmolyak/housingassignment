import matplotlib.pyplot as plt
import csv
import pandas as pd
import os

results_folder = "results"
graph_folder = "graphs"

x = []
y = []


for file in os.listdir(results_folder):
    results_df = pd.read_csv(results_folder + "/" + file)

    x.append(file)
    y.append(results_df['Disability-Utility'].mean())

plt.bar(x,y, label='Disability Utility')
plt.xlabel('Experiment')
plt.ylabel('Disability Utility')
plt.title('Disability Utility')
plt.legend()
plt.savefig(graph_folder + "/" + "disability-utility.png")