"""
 Copyright 2022 Google LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      https://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 """


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
