#!/usr/bin/env python

# MIT License
#
# Copyright (c) 2021 Theodor Amariucai
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import statistics

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D


def plot_cdfs(args):
    def plot_dual_cdf(path, latencies_dict, burst_size):
        _fig = plt.figure(figsize=(5, 5))
        _fig.suptitle(f'Burst size {burst_size}')
        plt.xlabel('Latency (ms)')
        plt.ylabel('Portion of requests')
        plt.grid(True)

        for iat in ['600s', '3s']:
            latencies = latencies_dict[iat][burst_size]
            if 'warm' in path or burst_size == '1':
                latencies = latencies[:-int(burst_size)]  # remove extra cold latencies

            quantile = np.arange(len(latencies)) / float(len(latencies) - 1)
            recent = plt.plot(latencies, quantile, '--o', markersize=4, markerfacecolor='none',
                              label=f'{"Warm" if "warm" in path else "Cold"} (IAT {iat})')

            print(f'Max latency {latencies[-1]}, stddev {statistics.stdev(latencies)}')

            average_latency = sum(latencies) / len(latencies)
            plt.axvline(x=average_latency, color=recent[-1].get_color(), linestyle='--')
            plt.annotate(f'{average_latency:0.0f}ms', (int(average_latency) + 20, 0.5), color='black')

            tail_latency = latencies[int(0.99 * len(latencies))]
            plt.axvline(x=tail_latency, color=recent[-1].get_color(), linestyle='--')
            plt.annotate(f'{tail_latency:0.0f}ms', (int(tail_latency) + 20, 0.25), color='red')

        plt.legend(loc='lower right')
        _fig.savefig(f'{path}/burst{burst_size}-dual-IAT-CDF.png')
        _fig.savefig(f'{path}/burst{burst_size}-dual-IAT-CDF.pdf')
        plt.close()

    def plot_individual_cdf(path, inter_arrival_time, latencies, size):
        desired_percentile = 0.99

        if 'warm' in path or size == '1':  # remove cold latencies from warm instance experiments
            latencies = latencies[:-int(size)]

        _fig = plt.figure(figsize=(5, 5))
        _fig.suptitle(f'Burst size {size}, IAT ~{inter_arrival_time}s')
        plt.xlabel('Latency (ms)')
        plt.ylabel('Portion of requests')
        plt.grid(True)

        quantile = np.arange(len(latencies)) / float(len(latencies) - 1)
        recent = plt.plot(latencies, quantile, '--o', markersize=4, markerfacecolor='none', color='black')

        average_latency = sum(latencies) / len(latencies)
        plt.axvline(x=average_latency, color=recent[-1].get_color(), linestyle='--')
        plt.annotate(f'{average_latency:0.0f}ms', (min(int(average_latency) * 1.1, int(average_latency) + 2), 0.5),
                     color='black')

        tail_latency = latencies[int(desired_percentile * len(latencies))]
        plt.axvline(x=tail_latency, color='red', linestyle='--')
        plt.annotate(f'{tail_latency:0.0f}ms', (min(int(tail_latency) * 1.1, int(tail_latency) + 2), 0.25),
                     color='red')

        handles, labels = [], []

        labels.append('Average')
        handles.append(Line2D([0], [0], color=recent[-1].get_color(), linewidth=2, linestyle='dotted'))

        labels.append(f'{int(desired_percentile * 100)}%ile')
        handles.append(Line2D([0], [0], color='red', linewidth=2, linestyle='dotted'))

        legend = plt.legend(handles=handles, labels=labels, loc='lower right')
        legend.get_texts()[1].set_color("red")

        _fig.savefig(f'{path}/empirical-CDF.png')
        _fig.savefig(f'{path}/empirical-CDF.pdf')
        plt.close()

    def get_experiment_results(inter_arrival_time):
        burstsize_to_latencies = {}

        experiment_dirs = []
        for dir_path, dir_names, filenames in os.walk(args.path):
            if not dir_names and dir_path.split('IAT')[1].split('s')[0] == inter_arrival_time:
                experiment_dirs.append(dir_path)

        for experiment in experiment_dirs:
            experiment_name = experiment.split('/')[-1]
            burst_size = experiment_name.split('burst')[1].split('-')[0]

            with open(experiment + "/latencies.csv") as file:
                data = pd.read_csv(file)
                read_latencies = data['Client Latency (ms)'].to_numpy()
                sorted_latencies = np.sort(read_latencies)
                burstsize_to_latencies[burst_size] = sorted_latencies

                plot_individual_cdf(experiment, inter_arrival_time, sorted_latencies, burst_size)

        return burstsize_to_latencies

    def plot_composing_cdf_return_latencies(subplot, inter_arrival_time, xlim):
        subplot.set_title(f'{"Warm" if int(inter_arrival_time) < 600 else "Cold"} (IAT {inter_arrival_time}s)')
        subplot.set_xlabel('Latency (ms)')
        subplot.set_ylabel('Portion of requests')
        subplot.grid(True)

        subplot.set_xlim([0, xlim])

        burst_sizes = get_experiment_results(inter_arrival_time)

        for size in sorted(burst_sizes):
            latencies = burst_sizes[size]
            if inter_arrival_time == "3" or size == '1':  # remove cold latencies from warm instance experiments
                latencies = latencies[:-int(size)]  # remove extra cold latencies

            quantile = np.arange(len(latencies)) / float(len(latencies) - 1)
            recent = subplot.plot(latencies, quantile, '--o', markersize=3, label=f'Burst Size {size}',
                                  markerfacecolor='none')

            average_latency = sum(latencies) / len(latencies)
            subplot.axvline(x=average_latency, color=recent[-1].get_color(), linestyle='--')

        return burst_sizes

    title = f'{args.provider} Bursty Behavior Analysis'
    fig, axes = plt.subplots(nrows=1, ncols=2, sharey=True, figsize=(10, 5))
    fig.suptitle(title, fontsize=16)

    iat_burst_sizes_latencies = {'3s': plot_composing_cdf_return_latencies(axes[0], '3', 250),
                                 '600s': plot_composing_cdf_return_latencies(axes[1], '600', 1200)}

    plot_dual_cdf(path=args.path, latencies_dict=iat_burst_sizes_latencies, burst_size='1')
    plot_dual_cdf(path=args.path, latencies_dict=iat_burst_sizes_latencies, burst_size='500')

    plt.legend(loc='lower right')
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(f'{args.path}/{title}.png')
    fig.savefig(f'{args.path}/{title}.pdf')
    plt.close()

    print("Completed successfully.")
