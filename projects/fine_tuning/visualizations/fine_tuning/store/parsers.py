import types
import pathlib
import logging
import yaml
import os
import json
import datetime
import urllib
import uuid

import jsonpath_ng

import matrix_benchmarking.cli_args as cli_args
import matrix_benchmarking.store.prom_db as store_prom_db

import projects.core.visualizations.helpers.store as core_helpers_store
import projects.core.visualizations.helpers.store.parsers as core_helpers_store_parsers

from . import prom as workload_prom

register_important_file = None # will be when importing store/__init__.py

K8S_TIME_FMT = "%Y-%m-%dT%H:%M:%SZ"
SHELL_DATE_TIME_FMT = "%a %b %d %H:%M:%S %Z %Y"
ANSIBLE_LOG_DATE_TIME_FMT = "%Y-%m-%d %H:%M:%S"

artifact_dirnames = types.SimpleNamespace()
artifact_dirnames.CLUSTER_CAPTURE_ENV_DIR = "*__cluster__capture_environment"
artifact_dirnames.CLUSTER_DUMP_PROM_DB_DIR = "*__cluster__dump_prometheus_dbs/*__cluster__dump_prometheus_db"
artifact_dirnames.FINE_TUNING_RUN_FINE_TUNING_DIR = "*__fine_tuning__run_fine_tuning_job"
artifact_paths = types.SimpleNamespace() # will be dynamically populated

IMPORTANT_FILES = [
    ".uuid",
    "config.yaml",
    f"{artifact_dirnames.CLUSTER_DUMP_PROM_DB_DIR}/prometheus.t*",
    f"{artifact_dirnames.CLUSTER_CAPTURE_ENV_DIR}/_ansible.log",
    f"{artifact_dirnames.CLUSTER_CAPTURE_ENV_DIR}/nodes.json",
    f"{artifact_dirnames.CLUSTER_CAPTURE_ENV_DIR}/ocp_version.yml",
    f"{artifact_dirnames.FINE_TUNING_RUN_FINE_TUNING_DIR}/artifacts/pod.log",
    f"{artifact_dirnames.FINE_TUNING_RUN_FINE_TUNING_DIR}/artifacts/pod.json",
]


def parse_always(results, dirname, import_settings):
    # parsed even when reloading from the cache file
    results.from_local_env = core_helpers_store_parsers.parse_local_env(dirname)

    pass


def parse_once(results, dirname):
    results.test_config = core_helpers_store_parsers.parse_test_config(dirname)
    results.test_uuid = core_helpers_store_parsers.parse_test_uuid(dirname)

    capture_state_dir = artifact_paths.CLUSTER_CAPTURE_ENV_DIR
    results.ocp_version = core_helpers_store_parsers.parse_ocp_version(dirname, capture_state_dir)
    results.from_env = core_helpers_store_parsers.parse_env(dirname, results.test_config, capture_state_dir)
    results.nodes_info = core_helpers_store_parsers.parse_nodes_info(dirname, capture_state_dir)
    results.cluster_info = core_helpers_store_parsers.extract_cluster_info(results.nodes_info)

    results.metrics = _extract_metrics(dirname)

    results.test_start_end_time = _parse_start_end_time(dirname)

    results.sft_training_metrics = _parse_sft_training_logs(dirname)
    results.allocated_resources = _parse_allocated_resources(dirname)


def _extract_metrics(dirname):
    db_files = {
        "sutest": (str(artifact_paths.CLUSTER_DUMP_PROM_DB_DIR / "prometheus.t*"), workload_prom.get_sutest_metrics()),
    }

    return core_helpers_store_parsers.extract_metrics(dirname, db_files)


@core_helpers_store_parsers.ignore_file_not_found
def _parse_start_end_time(dirname):
    ANSIBLE_LOG_TIME_FMT = '%Y-%m-%d %H:%M:%S'

    test_start_end_time = types.SimpleNamespace()
    test_start_end_time.start = None
    test_start_end_time.end = None

    with open(register_important_file(dirname, artifact_paths.CLUSTER_CAPTURE_ENV_DIR / "_ansible.log")) as f:
        for line in f.readlines():
            time_str = line.partition(",")[0] # ignore the MS
            if test_start_end_time.start is None:
                test_start_end_time.start = datetime.datetime.strptime(time_str, ANSIBLE_LOG_TIME_FMT)
        if test_start_end_time.start is None:
            raise ValueError("Ansible log file is empty :/")

        test_start_end_time.end = datetime.datetime.strptime(time_str, ANSIBLE_LOG_TIME_FMT)

    return test_start_end_time

SFT_TRAINER_RESULTS_KEYS = {
    "train_runtime": types.SimpleNamespace(lower_better=True, units="seconds", title="runtime"),
    "train_samples_per_second": types.SimpleNamespace(lower_better=False, units="samples/second"),
    "train_steps_per_second": types.SimpleNamespace(lower_better=False, units="steps/second"),
    "train_tokens_per_second": types.SimpleNamespace(lower_better=False, units="tokens/second"),
}

@core_helpers_store_parsers.ignore_file_not_found
def _parse_sft_training_logs(dirname):
    sft_training_metrics = types.SimpleNamespace()
    with open(register_important_file(dirname, artifact_paths.FINE_TUNING_RUN_FINE_TUNING_DIR / "artifacts/pod.log")) as f:
        for line in f.readlines():
            if line.startswith("{'train_runtime'"):
                results = json.loads(line.replace("'", '"'))
                # {'train_runtime': 1.5203, 'train_samples_per_second': 6.578, 'train_steps_per_second': 0.658, 'train_tokens_per_second': 306.518, 'train_loss': 4.817451000213623, 'epoch': 1.0}

                # this will raise a KeyError if a key is missing in `results`
                # this means that we are not parsing the data we're expecting.
                for key in SFT_TRAINER_RESULTS_KEYS:
                    setattr(sft_training_metrics, key, results[key])

    return sft_training_metrics


def _parse_allocated_resources(dirname):
    allocated_resources = types.SimpleNamespace()
    with open(register_important_file(dirname, artifact_paths.FINE_TUNING_RUN_FINE_TUNING_DIR / "artifacts/pod.json")) as f:
        pod_def = json.load(f)

    try:
        allocated_resources.gpu = int(pod_def["items"][0]["spec"]["containers"][0]["resources"]["limits"]["nvidia.com/gpu"])
        print(allocated_resources.gpu)
    except (IndexError, KeyError):
        allocated_resources.gpu = 0

    return allocated_resources