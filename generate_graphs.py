import matplotlib.pyplot as plt
import csv
import pandas as pd
import os
import numpy as np

results_folder = "results"
graph_folder = "graphs"

x = []
disability_utility = []
distance_utility = []
width = 0.3

for file in os.listdir(results_folder):
    results_df = pd.read_csv(results_folder + "/" + file)

    x.append(file)
    disability_utility.append(results_df['Disability-Utility'].mean())
    distance_utility.append(results_df['Distance-Utility'].mean())

plt.bar(np.arange(len(x)),disability_utility, label='Disability Utility',width=width)
plt.bar(np.arange(len(x)) + width,distance_utility, label='Distance Utility',width=width)
plt.xlabel('Experiment')
plt.xticks(np.arange(len(x)),x)
plt.ylabel('Average Utility')
plt.title('Utility')
plt.legend()
plt.savefig(graph_folder + "/" + "utility.png")