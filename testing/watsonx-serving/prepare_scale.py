import logging
import pathlib
import os
import yaml

from common import env, config, run, prepare_gpu_operator, prepare_user_pods, prepare_gpu_operator, merge_dicts, sizing
import prepare_watsonx_serving

TESTING_THIS_DIR = pathlib.Path(__file__).absolute().parent

def prepare_sutest():
    with run.Parallel("prepare_sutest_1") as parallel:
        parallel.delayed(prepare_watsonx_serving.prepare)
        parallel.delayed(scale_up_sutest)

    with run.Parallel("prepare_sutest_2") as parallel:
        parallel.delayed(prepare_watsonx_serving.preload_image)
        parallel.delayed(prepare_gpu)


def prepare_gpu():
    if not config.ci_artifacts.get_config("gpu.prepare_cluster"):
        return

    prepare_gpu_operator.prepare_gpu_operator()

    if config.ci_artifacts.get_config("clusters.sutest.compute.dedicated"):
        toleration_key = config.ci_artifacts.get_config("clusters.sutest.compute.machineset.taint.key")
        toleration_effect = config.ci_artifacts.get_config("clusters.sutest.compute.machineset.taint.effect")
        prepare_gpu_operator.add_toleration(toleration_effect, toleration_key)

    run.run("./run_toolbox.py gpu_operator wait_stack_deployed")


def prepare():
    """
    Prepares the cluster and the namespace for running the Watsonx scale tests
    """

    test_mode = config.ci_artifacts.get_config("tests.mode")
    if test_mode == "scale":
        consolidate_model_config("tests.scale.model")
        config.ci_artifacts.set_config("tests.scale.model.consolidated", True)
        user_count = config.ci_artifacts.get_config("tests.scale.namespace.replicas")
    elif test_mode == "e2e":
        user_count = len(config.ci_artifacts.get_config("tests.e2e.models"))
    else:
        raise KeyError(f"Invalid test mode: {test_mode}")


    with run.Parallel("prepare_scale") as parallel:
        # prepare the sutest cluster
        parallel.delayed(prepare_sutest)

        # prepare the driver cluster
        namespace = config.ci_artifacts.get_config("base_image.namespace")

        parallel.delayed(prepare_user_pods.prepare_user_pods, user_count)
        parallel.delayed(prepare_user_pods.cluster_scale_up, namespace, user_count)


def scale_compute_sutest_node_requirement():
    ns_count = config.ci_artifacts.get_config("tests.scale.namespace.replicas")
    models_per_ns = config.ci_artifacts.get_config("tests.scale.model.replicas")
    models_count = ns_count * models_per_ns

    cpu_rq = config.ci_artifacts.get_config("tests.scale.model.serving_runtime.resource_request.cpu")
    mem_rq = config.ci_artifacts.get_config("tests.scale.model.serving_runtime.resource_request.memory")

    kwargs = dict(
        cpu = cpu_rq,
        memory = mem_rq,
        machine_type = config.ci_artifacts.get_config("clusters.sutest.compute.machineset.type"),
        user_count = models_count,
        )

    machine_count = sizing.main(**kwargs)

    # the sutest Pods must fit in one machine.
    return min(models_count, machine_count)


def e2e_compute_sutest_node_requirement():
    return 1

def scale_up_sutest():
    if config.ci_artifacts.get_config("clusters.sutest.is_metal"):
        return

    test_mode = config.ci_artifacts.get_config("tests.mode")
    if test_mode == "scale":
        node_count = scale_compute_sutest_node_requirement()
    elif test_mode == "e2e":
        node_count = e2e_compute_sutest_node_requirement()
    else:
        raise KeyError(f"Invalid test mode: {test_mode}")

    extra = dict(scale=node_count)
    run.run(f"ARTIFACT_TOOLBOX_NAME_SUFFIX=_sutest ./run_toolbox.py from_config cluster set_scale --prefix=sutest --extra \"{extra}\"")


def cluster_scale_up():

    with run.Parallel("cluster_scale_up") as parallel:
        namespace = config.ci_artifacts.get_config("base_image.namespace")
        user_count = config.ci_artifacts.get_config("tests.scale.namespace.replicas")
        parallel.delayed(prepare_user_pods.cluster_scale_up, namespace, user_count)

        parallel.delayed(prepare_sutest)


def cluster_scale_down():
    extra = dict(scale=1)
    with run.Parallel("cluster_scale_down") as parallel:
        parallel.delayed(run.run, f"./run_toolbox.py from_config cluster set_scale --prefix=sutest --extra \"{extra}\"")
        parallel.delayed(run.run, f"./run_toolbox.py from_config cluster set_scale --prefix=driver --extra \"{extra}\"")


def consolidate_model_config(config_location=None, _model_name=None, index=None, show=True, save=True):
    # test = <config_location>
    test_config = config.ci_artifacts.get_config(config_location) if config_location \
        else {}

    model_name = _model_name or test_config.get("name")
    if not model_name:
        raise RuntimeError(f"Couldn't find a name for consolidating the model configuration ... {config_location}={test_config} and model_name={_model_name}")

    def get_file_config(file_model_name):
        with open(TESTING_THIS_DIR / "models" / f"{file_model_name}.yaml") as f:
            return yaml.safe_load(f)

    # base = testing/models/<model_name>
    base_config = get_file_config(model_name)
    if extends_name := base_config.pop("extends", False):
        config_to_extend = get_file_config(extends_name)
        base_config = merge_dicts(config_to_extend, base_config)

    # watsonx = config(watsonx_serving.model)
    watsonx_config = config.ci_artifacts.get_config("watsonx_serving.model")

    # model = base
    model_config = base_config
    # model += watsonx
    model_config = merge_dicts(model_config, watsonx_config)
    # base += test
    model_config = merge_dicts(model_config, test_config)

    model_config["name"] = model_name
    if index is not None:
        model_config["index"] = index

    if config_location:
        config.ci_artifacts.set_config(config_location, model_config)

    if show or save:
        dump = yaml.dump(model_config,  default_flow_style=False, sort_keys=False).strip()
        if show:
            logging.info(f"Consolidated configuration for model '{model_name}':\n{dump}")

        if save:
            with open(env.ARTIFACT_DIR / "model_config.yaml", "w") as f:
                print(dump, file=f)

    return model_config
