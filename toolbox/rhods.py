import sys

from toolbox._common import RunAnsibleRole, AnsibleRole, AnsibleMappedParams, AnsibleConstant, AnsibleSkipConfigGeneration


class RHODS:
    """
    Commands relating to RHODS
    """

    @AnsibleRole("rhods_deploy_ods")
    @AnsibleMappedParams
    def deploy_ods(self, catalog_image, tag, channel="", version=""):
        """
        Deploy ODS operator from its custom catalog

        Args:
          catalog_image: Container image containing the RHODS bundle.
          tag: Catalog image tag to use to deploy RHODS.
          channel: The channel to use for the deployment. Let empty to use the default channel.
          version: The version to deploy. Let empty to install the last version available.
        """

        return RunAnsibleRole(locals())

    @AnsibleRole("rhods_wait_ods")
    @AnsibleMappedParams
    @AnsibleConstant("Comma-separated list of the RHODS images that should be awaited",
                     "images", "s2i-minimal-notebook,s2i-generic-data-science-notebook")
    def wait_ods(self):
        """
        Wait for ODS to finish its deployment
        """

        return RunAnsibleRole()

    @AnsibleRole("ocm_deploy_addon")
    @AnsibleConstant("Identifier of the addon that should be deployed",
                     "ocm_deploy_addon_id", "managed-odh")
    @AnsibleMappedParams
    @AnsibleSkipConfigGeneration
    def deploy_addon(self,
                     cluster_name, notification_email, wait_for_ready_state=True):
        """
        Installs the RHODS OCM addon

        Args:
          cluster_name: The name of the cluster where RHODS should be deployed.
          notification_email: The email to register for RHODS addon deployment.
          wait_for_ready_state: If true (default), will cause the role to wait until addon reports ready state. (Can time out)
        """

        addon_parameters = '[{"id":"notification-email","value":"'+notification_email+'"}]'

        return RunAnsibleRole(locals())

    @AnsibleRole("rhods_notebook_ods_ci_scale_test")
    @AnsibleMappedParams
    def notebook_ods_ci_scale_test(self,
                                   namespace,
                                   idp_name, username_prefix, user_count: int,
                                   secret_properties_file,
                                   notebook_url,
                                   minio_namespace,
                                   user_index_offset: int = 0,
                                   sut_cluster_kubeconfig="",
                                   artifacts_collected="all",
                                   user_sleep_factor=1.0,
                                   user_batch_size: int = 1,
                                   ods_ci_istag="",
                                   ods_ci_exclude_tags="None",
                                   ods_ci_test_case="notebook_dsg_test.robot",
                                   artifacts_exporter_istag="",
                                   notebook_image_name="s2i-generic-data-science-notebook",
                                   notebook_size_name="Small",
                                   notebook_benchmark_name="pyperf_bm_go.py",
                                   notebook_benchmark_number=20,
                                   notebook_benchmark_repeat=2,
                                   state_signal_redis_server="",
                                   toleration_key="",
                                   capture_prom_db: bool = True,
                                   stop_notebooks_on_exit: bool = True,
                                   only_create_notebooks: bool = False,
                                   ):

        """
        End-to-end scale testing of RHODS notebooks, at  user level.

        Args:
          namespace: Namespace in which the scale test should be deployed.
          idp_name: Name of the identity provider to use.
          username_prefix: Prefix of the usernames to use to run the scale test.
          user_count: Number of users to run in parallel.
          user_index_offset: Offset to add to the user index to compute the user name.
          secret_properties_file: Path of a file containing the properties of LDAP secrets. (See 'deploy_ldap' command)
          notebook_url: URL from which the notebook will be downloaded.
          minio_namespace: Namespace where the Minio server is located.
          sut_cluster_kubeconfig: Path of the system-under-test cluster's Kubeconfig. If provided, the RHODS endpoints will be looked up in this cluster.
          artifacts_collected:
           - 'all': collect all the artifacts generated by ODS-CI.
           - 'no-screenshot': exclude the screenshots (selenium-screenshot-*.png) from the artifacts collected.
           - 'no-screenshot-except-zero': exclude the screenshots, except if the job index is zero.
           - 'no-screenshot-except-failed': exclude the screenshots, except if the test failed.
           - 'no-screenshot-except-failed-and-zero': exclude the screenshots, except if the test failed or the job index is zero.
           - 'none': do not collect any ODS-CI artifact.
          user_sleep_factor: Delay to sleep between users
          user_batch_size: Number of users to launch at the same time.
          ods_ci_istag: Imagestream tag of the ODS-CI container image.
          ods_ci_scale_test_case: ODS-CI test case to execute.
          ods_ci_exclude_tags: Tags to exclude in the ODS-CI test case.
          artifacts_exporter_istag: Imagestream tag of the artifacts exporter side-car container image.
          ods_ci_notebook_image_name: Name of the RHODS image to use when launching the notebooks.
          ods_ci_notebook_size_name: Name of the RHODS notebook size to select when launching the notebook.
          ods_ci_notebook_benchmark_name: Name of the benchmark to execute in the notebook.
          ods_ci_notebook_benchmark_repeat: Number of repeats of the benchmark to perform.
          ods_ci_notebook_benchmark_number: Number of times the benchmark should be executed within one repeat.
          state_signal_redis_server: Hostname and port of the Redis server for StateSignal synchronization (for the synchronization of the beginning of the user simulation)
          toleration_key: Toleration key to use for the test Pods.
          capture_prom_db: If True, captures the Prometheus DB of the systems.
          stop_notebooks_on_exit: If False, keep the user notebooks running at the end of the test.
          only_create_notebooks: If True, only create the notebooks, but don't start them. This will overwrite the value of 'ods_ci_exclude_tags'.
        """

        ARTIFACTS_COLLECTED_VALUES = ("all", "none", "no-screenshot", "no-screenshot-except-zero", "no-screenshot-except-failed", "no-screenshot-except-failed-and-zero")
        if artifacts_collected not in ARTIFACTS_COLLECTED_VALUES:
            print(f"ERROR: invalid value '{artifacts_collected}' for 'artifacts_collected'. Must be one of {', '.join(ARTIFACTS_COLLECTED_VALUES)}")
            sys.exit(1)

        del ARTIFACTS_COLLECTED_VALUES

        return RunAnsibleRole(locals())

    @AnsibleRole("rhods_cleanup_notebooks")
    @AnsibleMappedParams
    def cleanup_notebooks(self, username_prefix):
        """
        Clean up the resources created along with the notebooks, during the scale tests.

        Args:
          username_prefix: Prefix of the usernames who created the resources.
        """

        return RunAnsibleRole(locals())

    @AnsibleRole("rhods_notebook_locust_scale_test")
    @AnsibleMappedParams
    def notebook_locust_scale_test(self,
                                   namespace,
                                   idp_name,
                                   secret_properties_file,
                                   test_name,
                                   minio_namespace,
                                   username_prefix,
                                   user_count: int,
                                   user_index_offset: int,
                                   locust_istag,
                                   artifacts_exporter_istag,
                                   run_time="1m",
                                   spawn_rate="1",
                                   sut_cluster_kubeconfig="",
                                   notebook_image_name="s2i-generic-data-science-notebook",
                                   notebook_size_name="Small",
                                   toleration_key="",
                                   cpu_count: int = 1,
                                   user_sleep_factor: float = 1.0,
                                   capture_prom_db: bool = True,
                                   ):

        """
        End-to-end testing of RHODS notebooks at scale, at API level

        Args:
          namespace: Namespace where the test will run
          idp_name: Name of the identity provider to use.
          secret_properties_file: Path of a file containing the properties of LDAP secrets. (See 'deploy_ldap' command).
          minio_namespace: Namespace where the Minio server is located.
          username_prefix: Prefix of the RHODS users.
          test_name: Test to perform.
          user_count: Number of users to run in parallel.
          user_index_offset: Offset to add to the user index to compute the user name.
          notebook_image_name: Name of the RHODS image to use when launching the notebooks.
          locust_istag: Imagestream tag of the locust container.
          run_time: Test run time (eg, 300s, 20m, 3h, 1h30m, etc.)
          spawn_rate: Rate to spawn users at (users per second)
          sut_cluster_kubeconfig: Path of the system-under-test cluster's Kubeconfig. If provided, the RHODS endpoints will be looked up in this cluster.
          toleration_key: Toleration key to use for the test Pods.
          artifacts_exporter_istag: Imagestream tag of the artifacts exporter side-car container.
          cpu_count: Number of Locust processes to launch (one per Pod with 1cpu).
          user_sleep_factor: Delay to sleep between users
          capture_prom_db: If True, captures the Prometheus DB of the systems.
        """

        return RunAnsibleRole(locals())


    @AnsibleRole("rhods_benchmark_notebook_performance")
    @AnsibleConstant("Address where the imagestreams are stored. Used only when use_rhods=false.",
                     "imagestream_source_location", "https://raw.githubusercontent.com/red-hat-data-services/odh-manifests/master/jupyterhub/notebook-images/overlays/additional")
    @AnsibleMappedParams
    def benchmark_notebook_performance(self,
                                       namespace="rhods-notebooks",
                                       imagestream="s2i-generic-data-science-notebook",
                                       imagestream_tag="",
                                       use_rhods: bool = True,
                                       notebook_directory="testing/ods/notebooks/",
                                       notebook_filename="benchmark_entrypoint.ipynb",
                                       benchmark_name="pyperf_bm_go.py",
                                       benchmark_repeat: int = 1,
                                       benchmark_number: int = 1,
                                       ):
        """
        Benchmark the performance of a notebook image.

        Args:
          namespace: Namespace in which the notebook will be deployed, if not deploying with RHODS.
          imagestream: Imagestream to use to look up the notebook Pod image.
          imagestream_tag: Imagestream tag to use to look up the notebook Pod image. If emtpy and and the image stream has only one tag, use it. Fails otherwise.
          use_rhods: If true, deploy a RHODS notebook, If false, deploy directly a Pod.
          notebook_directory: Directory containing the files to mount in the notebook.
          notebook_filename: Name of the ipynb notebook file to execute with JupyterLab.
          benchmark_name: Name of the benchmark to execute in the notebook.
          benchmark_repeat: Number of repeats of the benchmark to perform for one time measurement.
          benchmark_number: Number of times the benchmark time measurement should be done.
        """

        return RunAnsibleRole(locals())

    @AnsibleRole("rhods_undeploy_ods")
    @AnsibleMappedParams
    def undeploy_ods(self,
                     namespace="redhat-ods-operator",
                     wait: bool = True):
        """
        Undeploy ODS operator

        Args:
          namespace: Namespace where RHODS is installed.
          wait: Wait for the operator full deletion.
        """

        return RunAnsibleRole(locals())

    @AnsibleRole("rhods_cleanup_aws")
    @AnsibleMappedParams
    def cleanup_aws(self, openshift_installer=""):
        """
        Cleanup AWS from RHODS dangling resources

        Args:
          openshift_installer: path of the openshift_installer to use. If empty, download it.
        """

        return RunAnsibleRole()

    @AnsibleRole("cluster_prometheus_db")
    @AnsibleSkipConfigGeneration # see cluster.reset_prometheus_db
    @AnsibleConstant("", "cluster_prometheus_db_mode", "reset")
    @AnsibleConstant("", "cluster_prometheus_db_label", "deployment=prometheus")
    @AnsibleConstant("", "cluster_prometheus_db_namespace", "redhat-ods-monitoring")
    def reset_prometheus_db(self):
        """
        Resets RHODS Prometheus database, by destroying its Pod.
        """

        return RunAnsibleRole()

    @AnsibleRole("cluster_prometheus_db")
    @AnsibleSkipConfigGeneration # see cluster.reset_prometheus_db
    @AnsibleConstant("", "cluster_prometheus_db_mode", "dump")
    @AnsibleConstant("", "cluster_prometheus_db_label", "deployment=prometheus")
    @AnsibleConstant("", "cluster_prometheus_db_namespace", "redhat-ods-monitoring")
    @AnsibleConstant("", "cluster_prometheus_db_directory", "/prometheus/data")
    @AnsibleMappedParams
    def dump_prometheus_db(self, dump_name_prefix="prometheus"):
        """
        Dump Prometheus database into a file

        Args:
          name_prefix: Name prefix for the archive that will be stored.c
        """

        return RunAnsibleRole(locals())

    @AnsibleRole("rhods_capture_state")
    @AnsibleMappedParams
    def capture_state(self):
        """
        Capture information about the cluster and the RHODS deployment
        """

        return RunAnsibleRole()
