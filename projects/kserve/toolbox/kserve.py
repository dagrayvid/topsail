import sys

from projects.core.library.ansible_toolbox import (
    RunAnsibleRole, AnsibleRole,
    AnsibleMappedParams, AnsibleConstant,
    AnsibleSkipConfigGeneration
)

class Kserve:
    """
    Commands relating to RHOAI KServe component
    """

    @AnsibleRole("kserve_deploy_model")
    @AnsibleMappedParams
    def deploy_model(self,
                     namespace,
                     sr_name,
                     sr_kserve_image, sr_kserve_resource_request,
                     sr_transformer_image, sr_transformer_resource_request,
                     inference_service_name,
                     inference_service_model_format,
                     storage_uri,
                     sa_name,
                     sr_container_flavor,
                     sr_kserve_extra_env_values={},
                     sr_transformer_extra_env_values={},
                     sr_shared_memory=False,
                     inference_service_min_replicas : int = None,
                     secret_env_file_name=None,
                     secret_env_file_key=None,
                     sr_mute_logs=False,
                     delete_others=True,
                     limits_equals_requests=True,
                     raw_deployment=False,
                     ):
        """
        Deploy a KServe model

        Args:
          name: the name of the resource to create
          namespace: the namespace in which the model should be deployed

          sr_name: the name to give to the serving runtime
          sr_container_flavor: name of the container flavor to use in the serving runtime (tgis+caikit or tgis)
          sr_shared_memory: if True, create a 2 Gi in-memory volume mounted on /dev/shm (for shards to communicate).
          sr_kserve_image: the image of the Kserve serving runtime container
          sr_kserve_resource_request: the resource request of the kserve serving runtime container
          sr_kserve_extra_env_values: extra key/value pairs for the kserve container (will override the values from the secret file)

          sr_transformer_image: the image of the Transformer serving runtime container
          sr_transformer_resource_request: the resource request of the Transformer serving runtime container
          sr_mute_logs: if True, mute the serving runtime containers logs
          sr_transformer_extra_env_values: extra key/value pairs for the transformer container (will override the values from the secret file)

          inference_service_name: the name to give to the inference service
          inference_service_min_replicas: the minimum number of replicas. If none, the field is left unset.
          inference_service_model_format: the name of the inference service format (caikit, pytorch, ...)

          sa_name: name of the service account to use for running the Pod
          storage_uri: [S3] URI where the model is stored

          secret_env_file_name: name of the YAML file containing the secret environment key/values
          secret_env_file_key: key to the secret environment key/values in the secret file

          delete_others: if True, deletes the other serving runtime/inference services of the namespace

          limits_equals_requests: if True, sets use the requests values to define the limits. If False, do not define any limits (except for GPU)
          raw_deployment: if True, do not try to configure anything related to Serverless.
        """

        if sr_container_flavor not in ("tgis+caikit", "tgis"):
            raise ValueError(f"Unsupported container flavor: {sr_container_flavor}")

        return RunAnsibleRole(locals())


    @AnsibleRole("kserve_undeploy_model")
    @AnsibleMappedParams
    def undeploy_model(self,
                       namespace,
                       sr_name="",
                       inference_service_name="",
                       all=False,
                     ):
        """
        Undeploy a KServe model

        Args:
          namespace: the namespace in which the model should be deployed
          sr_name: the name to give to the serving runtime
          inference_service_name: the name to give to the inference service
          all: delete all the inference services/servingruntime of the namespace
        """

        return RunAnsibleRole(locals())


    @AnsibleRole("kserve_validate_model")
    @AnsibleMappedParams
    def validate_model(self,
                       inference_service_names,
                       method,
                       query_count,
                       sr_container_flavor,
                       model_id="not-used",
                       namespace="",
                       raw_deployment=False,
                       proto=None,
                       ):
        """
        Validate the proper deployment of a KServe model

        Warning:
          This command requires `grpcurl` to be available in the PATH.

        Args:
          inference_service_names: a list of names of the inference service to validate
          sr_container_flavor: name of the container flavor to use in the serving runtime (tgis+caikit or tgis)
          method: the gRPC method to call
          model_id: the model-id to pass to the inference service
          query_count: number of query to perform
          namespace: the namespace in which the Serving stack was deployed. If empty, use the current project.
          raw_deployment: if True, do not try to configure anything related to Serverless. Works only in-cluster at the moment.
          proto: if not empty, the proto file to pass to grpcurl
        """

        if sr_container_flavor not in ("tgis+caikit", "tgis"):
            raise ValueError(f"Unsupported container flavor: {sr_container_flavor}")

        return RunAnsibleRole(locals())


    @AnsibleRole("kserve_capture_state")
    @AnsibleMappedParams
    def capture_state(self, namespace=""):
        """
        Captures the state of the KServe stack in a given namespace

        Args:
          namespace: the namespace in which the Serving stack was deployed. If empty, use the current project.
        """

        return RunAnsibleRole(locals())

    @AnsibleRole("kserve_capture_operators_state")
    @AnsibleMappedParams
    def capture_operators_state(self,
                                raw_deployment=False,
                                ):
        """
        Captures the state of the operators of the KServe serving stack

        Args:
          raw_deployment: if True, do not try to capture any Serverless related resource
        """

        return RunAnsibleRole(locals())


    @AnsibleRole("kserve_extract_protos")
    @AnsibleMappedParams
    def extract_protos(self,
                       namespace,
                       inference_service_name,
                       dest_dir,
                       copy_to_artifacts=True,
                       ):
        """
        Extracts the protos of an inference service

        Args:
          namespace: the namespace in which the model was deployed
          inference_service_name: the name of the inference service
          dest_dir: the directory where the protos should be stored
          copy_to_artifacts: if True, copy the protos to the command artifacts. If False, don't.
        """

        return RunAnsibleRole(locals())


    @AnsibleRole("kserve_extract_protos_grpcurl")
    @AnsibleMappedParams
    def extract_protos_grpcurl(self,
                               namespace,
                               inference_service_name,
                               dest_file,
                               methods: list,
                               copy_to_artifacts=True,
                       ):
        """
        Extracts the protos of an inference service, with GRPCurl observe

        Args:
          namespace: the namespace in which the model was deployed
          inference_service_name: the name of the inference service
          dest_file: the path where the proto file will be stored
          methods: the list of methods to extract
          copy_to_artifacts: if True, copy the protos to the command artifacts. If False, don't.
        """

        return RunAnsibleRole(locals())
