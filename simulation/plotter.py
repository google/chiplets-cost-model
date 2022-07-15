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


from turtle import width
import numpy as np
import plotly.graph_objects as go
import locale

from matplotlib import pyplot as plt

locale.setlocale(locale.LC_ALL, '')

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
    df.hist(bins=25, figsize=(5, col * 5), layout=(col, 1))
    plt.savefig(f'outputs/cost_diff_summary.png')
    plt.clf()

"""
The input param `values` should in format:
[
    [
        {
            'name': 'variable name1',
            'high': high_val1,
            'low': low_val1
        },
        {
            'name': 'variable name2',
            'high': high_val2,
            'low': low_val2
        }
    ]
]
"""
def plot_tornado(values):
    def cost_diff(val):
        return abs(val['high'] - val['low'])

    for year in range(1, len(values) + 1):
        value_yr = values[year - 1]
        value_yr.sort(reverse = False, key=cost_diff)
        arr_len = len(value_yr)
        start = max(0, arr_len - 6) # to take max 6 inputs
        trimmed_values = value_yr[start:arr_len]
        cols = list(map(lambda val: val['name'].replace('{year}', f'Yr{year}'), trimmed_values))
        highs = list(map(lambda val: val['high'], trimmed_values))
        lows = list(map(lambda val: val['low'], trimmed_values))
        plot_tornado_chart(cols, highs, lows, year)


def plot_tornado_chart(cols, highs, lows, year):
    n = len(highs)

    def find_baseline():
        avg_sum = 0

        for i in range(0, n):
            avg_sum += (highs[i] + lows[i]) / 2

        return avg_sum / n

    baseline = find_baseline() # (highs[n - 1] + lows[n - 1])/2

    def move(lst):
        return [i - baseline for i in lst]

    moved_highs = move(highs)
    moved_lows = move(lows)

    def format(lst):
        return [locale.currency(i, grouping=True) for i in lst]
    
    text_highs = format(highs)
    text_lows = format(lows)

    fig = go.Figure()
    fig.add_trace(go.Bar(y=cols, x=moved_highs,
                         base=baseline, # take average value of low and high
                         marker_color='darkblue',
                         name='InputHigh',
                         marker_line_color='darkblue',
                         orientation='h',
                         marker_line_width=1.5,
                         opacity=0.7,
                         text=text_highs,
                         textposition='auto'
                         ))
    fig.add_trace(go.Bar(y=cols, x=moved_lows,
                         base=baseline,
                         marker_color='darkred',
                         name='InputLow',
                         marker_line_color='darkred',
                         orientation='h',
                         marker_line_width=1.5,
                         opacity=0.7,
                         text=text_lows,
                         textposition='auto'
                         ))
    fig.update_layout(
        height=500,
        width=1000,
        margin=dict(t=50, l=10, b=10, r=10),
        title_text=f"Cost Difference ($)/ Yr{year}",
        title_font_family="sans-serif",
        title_font_size=25,
        title_font_color="darkblue",
        title_x=0.5  # to adjust the position along x-axis of the title
    )
    fig.update_layout(barmode='overlay',
                      xaxis_tickangle=baseline,
                      legend=dict(
                          x=0.80,
                          y=0.01,
                          bgcolor='rgba(255, 255, 255, 0)',
                          bordercolor='rgba(255, 255, 255, 0)'
                      ),
                      yaxis=dict(
                          titlefont_size=16,
                          tickfont_size=14
                      ),
                      bargap=0.20)
    fig.write_image(file=f'outputs/tornado_yr{year}.png', format='png')
