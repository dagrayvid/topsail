from collections import defaultdict
import re
import logging
import datetime
import math
import copy

import statistics as stats

import plotly.subplots
import plotly.graph_objs as go
import pandas as pd
import plotly.express as px
from dash import html

import matrix_benchmarking.plotting.table_stats as table_stats
import matrix_benchmarking.common as common

from . import error_report, report

def register():
    SFTTraining()


def generateSFTTrainingData(entries, _variables, _ordered_vars, sfttraining_key):
    data = []

    variables = [v for v in _variables if v != "gpu"]

    for entry in entries:
        datum = dict()
        datum["gpu"] = entry.results.allocated_resources.gpu
        datum[sfttraining_key] = getattr(entry.results.sft_training_metrics, sfttraining_key, 0)
        datum["name"] = entry.get_name(variables)

        data.append(datum)

    ref = None
    for datum in data:
        if datum["gpu"] == 1:
            ref = datum[sfttraining_key]

    if not ref:
        return data, None

    for datum in data:
        datum[f"{sfttraining_key}_speedup"] = speedup = ref / datum[sfttraining_key]
        datum[f"{sfttraining_key}_efficiency"] = speedup / datum["gpu"]

    return data, ref


class SFTTraining():
    def __init__(self):
        self.name = "SFTTraining"
        self.id_name = self.name

        table_stats.TableStats._register_stat(self)
        common.Matrix.settings["stats"].add(self.name)

    def do_hover(self, meta_value, variables, figure, data, click_info):
        return "nothing"

    def do_plot(self, ordered_vars, settings, setting_lists, variables, cfg):
        cfg__sft_key = cfg.get("sfttraining_key", False)
        cfg__speedup = cfg.get("speedup", False)
        cfg__efficiency = cfg.get("efficiency", False)

        from ..store import parsers
        key_properties = parsers.SFT_TRAINER_RESULTS_KEYS[cfg__sft_key]

        if not cfg__sft_key:
            raise ValueError("'sfttraining_key' is a mandatory parameter ...")

        entries = common.Matrix.all_records(settings, setting_lists)

        data, has_speedup = generateSFTTrainingData(entries, variables, ordered_vars, cfg__sft_key)
        df = pd.DataFrame(data)

        if df.empty:
            return None, "Not data available ..."

        x_key = "gpu"
        df = df.sort_values(by=[x_key], ascending=False)

        y_key = cfg__sft_key
        if (cfg__speedup or cfg__efficiency) and not has_speedup:
            return None, "Cannot compute the speedup & efficiency (reference value not found)"

        if cfg__speedup:
            y_key += "_speedup"
        elif cfg__efficiency:
            y_key += "_efficiency"

        fig = px.line(df, hover_data=df.columns, x=x_key, y=y_key, color="name")


        for i in range(len(fig.data)):
            fig.data[i].update(mode='lines+markers+text')

        fig.update_xaxes(title="Number of GPUs used for the fine-tuning")
        y_title = getattr(key_properties, "title", "speed")
        y_units = key_properties.units

        if cfg__speedup:
            what = ", GPU speedup"
            y_lower_better = False
        elif cfg__efficiency:
            what = ", GPU efficiency"
            y_lower_better = False
        else:
            y_lower_better = key_properties.lower_better
            what = f", in {y_units}"

        y_title = f"Fine-tuning {y_title}{what}. "
        title = y_title + "<br>"+("Lower is better" if y_lower_better else "Higher is better") + "."
        fig.update_yaxes(title=("❮ " if y_lower_better else "") + y_title + (" ❯" if not y_lower_better else ""))
        fig.update_layout(title=title, title_x=0.5,)
        fig.update_layout(legend_title_text="Configuration")

        # ❯ or ❮

        return fig, ""
