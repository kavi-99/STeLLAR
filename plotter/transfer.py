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

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import ScalarFormatter


def add_subplot(args, subtitle_percentile, ylabel, subplot, rtt_latencies, stamp_latencies):
    def change_to_seconds():
        subplot.set_ylabel('Latency (seconds)')
        return [latency / 1000.0 if latency != np.nan else np.nan for latency in used_latencies]

    assert rtt_latencies.keys() == stamp_latencies.keys()

    subplot.set_title(subtitle_percentile)
    subplot.set_xlabel('Transfer Size (KB)')
    subplot.set_ylabel(ylabel)

    subplot.set_xscale('log')  # better transfer latencies and bandwidth visualization
    subplot.xaxis.set_major_formatter(ScalarFormatter())
    subplot.grid(True)

    subplot.set_xticks([int(size/1024.) for size in args.transfer_sizes])

    used_transfer_sizes = args.transfer_sizes
    if max(used_transfer_sizes) >= 1e4:
        subplot.set_xlabel('Transfer Size (MB)')
        used_transfer_sizes = [size / 1024.0 for size in used_transfer_sizes]
    elif max(used_transfer_sizes) >= 1e6:
        subplot.set_xlabel('Transfer Size (GB)')
        used_transfer_sizes = [size / 1024.0 / 1024.0 for size in used_transfer_sizes]

    colors_rtt = []
    for memory_mb in sorted(rtt_latencies):
        diff = len(used_transfer_sizes) - len(rtt_latencies[memory_mb])
        while diff > 0:
            diff -= 1
            rtt_latencies[memory_mb].append(np.nan)

        used_latencies = rtt_latencies[memory_mb]
        if max(used_latencies) >= 1e3:
            used_latencies = change_to_seconds()

        rtts_plotted = subplot.plot(used_transfer_sizes, used_latencies, 'o--',
                                    label=f"{memory_mb / 1024.0}GB memory")
        colors_rtt.append(rtts_plotted[0].get_color())

        for j, txt in enumerate(used_latencies):
            if not np.isnan(used_latencies[j]):
                subplot.annotate(int(txt), (used_transfer_sizes[j], used_latencies[j]))

    for i, memory_mb in enumerate(sorted(stamp_latencies)):
        diff = len(used_transfer_sizes) - len(stamp_latencies[memory_mb])
        while diff > 0:
            diff -= 1
            stamp_latencies[memory_mb].append(np.nan)

        used_latencies = stamp_latencies[memory_mb]
        if max(used_latencies) >= 1e3:
            used_latencies = change_to_seconds()

        subplot.plot(used_transfer_sizes, used_latencies, 'o-', color=colors_rtt[i])

        for j, txt in enumerate(used_latencies):
            if not np.isnan(used_latencies[j]):
                subplot.annotate(int(txt), (used_transfer_sizes[j], used_latencies[j]))

    handles, labels = subplot.get_legend_handles_labels()

    if args.provider == "vHive":
        handles, labels = [], []
        legend_color = colors_rtt[0]
    else:
        legend_color = 'black'

    labels.append('Round Trip Time')
    handles.append(Line2D([0], [0], color=legend_color, linewidth=2, linestyle='dotted'))

    labels.append('Internal Timestamp')
    handles.append(Line2D([0], [0], color=legend_color, linewidth=2))

    if "Median" not in subtitle_percentile:
        subplot.legend(handles=handles, labels=labels, loc='upper left')


def load_experiment_results(args, inter_arrival_time):
    # dicts from function memories to latencies according to the transfer_size array
    rtt_median = {}
    rtt_percentiles = {}
    stamp_diff_median = {}
    stamp_diff_percentiles = {}
    transfer_sizes_kb = []

    experiment_dirs = []
    for dir_path, dir_names, filenames in os.walk(args.path):
        if not dir_names:  # no subdirectories
            experiment_dirs.append(dir_path)

    # sort by image size
    experiment_dirs.sort(key=lambda s: float(s.split('payload')[-1].split('KB')[0]))
    experiment_dirs = filter(lambda s: float(s.split('IAT')[1].split('s-')[0]) <= inter_arrival_time, experiment_dirs)
    experiment_dirs = filter(lambda s: float(s.split('payload')[-1].split('KB')[0]) > 0.0, experiment_dirs)

    for experiment in experiment_dirs:
        transfer_sizes_kb.append(float(experiment.split('payload')[-1].split('KB')[0]))
        memory_size = int(experiment.split('memory')[1].split('MB')[0])

        with open(experiment + "/latencies.csv") as rtt_file:
            data = pd.read_csv(rtt_file)
            transfer_latencies = data['Client Latency (ms)'].to_numpy()
            sorted_latencies = np.sort(transfer_latencies)

            median_value = sorted_latencies[int(len(sorted_latencies) * 0.5)]
            if memory_size in rtt_median:
                rtt_median[memory_size].append(median_value)  # 50%ile = median
            else:
                rtt_median[memory_size] = [median_value]

            tail_value = sorted_latencies[int(len(sorted_latencies) * args.desired_percentile / 100.0)]
            if memory_size in rtt_percentiles:
                rtt_percentiles[memory_size].append(tail_value)  # 95%ile
            else:
                rtt_percentiles[memory_size] = [tail_value]

        with open(experiment + "/data-transfers.csv") as stamp_file:
            data = pd.read_csv(stamp_file)
            timestamp1 = data['Function 0 Timestamp'].to_numpy()
            timestamp2 = data['Function 1 Timestamp'].to_numpy()
            transfer_latencies = timestamp2 - timestamp1
            sorted_latencies = np.sort(transfer_latencies)

            median_value = sorted_latencies[int(len(sorted_latencies) * 0.5)]
            if memory_size in stamp_diff_median:
                stamp_diff_median[memory_size].append(median_value)  # 50%ile = median
            else:
                stamp_diff_median[memory_size] = [median_value]

            tail_value = sorted_latencies[int(len(sorted_latencies) * args.desired_percentile / 100.0)]
            if memory_size in stamp_diff_percentiles:
                stamp_diff_percentiles[memory_size].append(tail_value)  # 50%ile = median
            else:
                stamp_diff_percentiles[memory_size] = [tail_value]

    return transfer_sizes_kb, rtt_median, rtt_percentiles, stamp_diff_median, stamp_diff_percentiles


def generate_transfer_bandwidth_figure(args, inter_arrival_time, rtt_median, stamp_diff_median):
    title = f'{args.provider} {"Storage" if "storage" in args.path else "Inline"} Transfer Bandwidth'
    # (IAT {inter_arrival_time}) <- they differ e.g. 3s and 10s

    fig, axes = plt.subplots(nrows=1, ncols=1, sharey=True, figsize=(7, 5))
    fig.suptitle(title, fontsize=16)

    for memory_kb in rtt_median:
        rtt_median[memory_kb] = [(x / 1024) / (y / 1000) for x, y in zip(args.transfer_sizes, rtt_median[memory_kb])]

    for memory_kb in stamp_diff_median:
        stamp_diff_median[memory_kb] = [(x / 1024) / (y / 1000) for x, y in
                                        zip(args.transfer_sizes, stamp_diff_median[memory_kb])]

    add_subplot(args, "", 'Network Bandwidth (MB/s)', axes, rtt_median, stamp_diff_median)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(f'{args.path}/{title}.png')
    fig.savefig(f'{args.path}/{title}.pdf')
    plt.close()


def generate_transfer_latency_figure(args, inter_arrival_time, rtt_median, rtt_percentiles, stamp_diff_median,
                                     stamp_diff_percentiles):
    title = f'{args.provider} {"Storage" if "storage" in args.path else "Inline"} Transfer Latency'
    # (IAT {inter_arrival_time}) <- they differ e.g. 3s and 10s
    fig, axes = plt.subplots(nrows=1, ncols=1 if args.just_median else 2, sharey=True, figsize=(10, 5))
    fig.suptitle(title, fontsize=16)
    plt.grid(True)

    if args.just_median:
        add_subplot(args, 'Median (50% percentile)', 'Latency (ms)', axes, rtt_median, stamp_diff_median)
    else:
        add_subplot(args, f"{args.desired_percentile}% percentile", 'Latency (ms)', axes[0],
                    rtt_percentiles,
                    stamp_diff_percentiles)
        add_subplot(args, 'Median (50% percentile)', 'Latency (ms)', axes[1], rtt_median, stamp_diff_median)

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(f'{args.path}/{title}.png')
    fig.savefig(f'{args.path}/{title}.pdf')
    plt.close()


def generate_figures(args, inter_arrival_time):
    args.transfer_sizes, rtt_median, rtt_percentiles, stamp_diff_median, stamp_diff_percentiles = load_experiment_results(
        args,
        inter_arrival_time)
    args.transfer_sizes = list(dict.fromkeys(args.transfer_sizes))  # remove duplicates

    generate_transfer_latency_figure(args, inter_arrival_time, rtt_median, rtt_percentiles, stamp_diff_median,
                                     stamp_diff_percentiles)
    generate_transfer_bandwidth_figure(args, inter_arrival_time, rtt_median, stamp_diff_median)


def plot_data_transfer_stats(args):
    args.just_median = False  # True if "vHive" in args.provider else False
    args.desired_percentile = 99 if "vHive" in args.provider else 99
    generate_figures(args, 50)  # IAT less than or equal to
    # generate_figures(args, '600')