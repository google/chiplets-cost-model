
import numpy as np

from matplotlib import pyplot as plt


def plot_graph(years, costsA, costsB, title):
    x = np.arange(1, years + 1)
    plt.title(title)
    plt.xlabel('Year')
    plt.ylabel('Cost($)')
    plt.plot(x, costsA, color='r', label='Option 1 (Chiplet)')
    plt.plot(x, costsB, color='g', label='Option 2 (2 SOC Chips)')
    plt.legend()
    plt.savefig(f'outputs/{title.lower().replace(" ", "_")}.png')
    plt.clf()


def plot_df(df, suffix=''):

    for col in df.columns:
        file_name = f'{col}_{suffix}.png' if suffix else f'{col}.png'
        plt.figure()
        plt.hist(df[col], bins=25, histtype='stepfilled')
        plt.savefig(f'outputs/{file_name}')
        plt.clf()
    
    col = len(df.columns)
    df.hist(bins = 25, figsize=(5, col * 5), layout=(col, 1))
    plt.savefig(f'outputs/cost_diff_summary.png')
    plt.clf()
