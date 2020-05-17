import matplotlib.pyplot as plt
import csv
import os
import pandas as pd
import numpy as np

results_folder = "results"
graph_folder = "graphs"

def utility():
    x = []
    disability_utility = []
    distance_utility = []
    width = 0.3

    for file in os.listdir(results_folder):
        results_df = pd.read_csv(results_folder + "/" + file)

        x.append(file)
        disability_utility.append(results_df['Disability-Utility'].mean())
        distance_utility.append(results_df['Distance-Utility'].mean())

    plt.clf()
    plt.bar(np.arange(len(x)),disability_utility, label='Disability Utility',width=width)
    plt.bar(np.arange(len(x)) + width,distance_utility, label='Distance Utility',width=width)
    plt.xlabel('Experiment')
    plt.xticks(np.arange(len(x)),x)
    plt.ylabel('Average Utility')
    plt.title('Utility')
    plt.legend()
    plt.savefig(graph_folder + "/" + "utility.png")

def disability_percentage_comparisons():
    x = []
    disability_percent = []

    on_df = pd.read_csv(results_folder + "/control.csv")
    x.append("ON")
    disability_percent.append(on_df['%-Disabiled-Applicants-Assigned'].mean())

    off_df = pd.read_csv(results_folder + "/nothing.csv")
    x.append("OFF")
    disability_percent.append(off_df['%-Disabiled-Applicants-Assigned'].mean())

    plt.clf()
    plt.bar(np.arange(len(x)),disability_percent, label='Disability Percent')
    plt.xlabel('Disability Contraints')
    plt.xticks(np.arange(len(x)),x)
    plt.ylabel('Percent Assigned')
    plt.title('Percent Applicants with Disabilities Assigned')
    plt.legend()
    plt.savefig(graph_folder + "/" + "percent_disabled.png") 

def race_percentage_comparisons():
    x = []
    race_on_percent = []
    race_off_percent = []
    races = ['Blacks','Hispanics','Whites','Others']

    on_df = pd.read_csv(results_folder + "/control.csv")

    for race in races:
        x.append(race)
        race_on_percent.append(on_df['%-'+ race].mean())

    off_df = pd.read_csv(results_folder + "/nothing.csv")

    for race in races:
        race_off_percent.append(off_df['%-'+ race].mean())

    width = 0.3

    plt.clf()
    plt.bar(np.arange(len(x)),race_on_percent, label='ON',width=width)
    plt.bar(np.arange(len(x)) + width,race_off_percent, label='OFF',width=width)
    plt.xlabel('Races')
    plt.xticks(np.arange(len(x)),x)
    plt.ylabel('Percent Assigned')
    plt.title('Percent Assigned by Race Distribution')
    plt.legend()
    plt.savefig(graph_folder + "/" + "percent_race.png") 


if __name__ == '__main__':
    utility()
    disability_percentage_comparisons()
    race_percentage_comparisons()