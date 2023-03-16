"""Example of a pipeline to demonstrate mounting a pvc to a task in a pipeline."""
import os
import urllib

from dotenv import load_dotenv

import kfp

import kfp_tekton

import kubernetes

load_dotenv(override=True)

kubeflow_endpoint = os.environ["KUBEFLOW_ENDPOINT"]
bearer_token = os.environ["BEARER_TOKEN"]


def add(a: float, b: float) -> float:
    """Calculate the sum of the two arguments."""
    return a + b


add_op = kfp.components.create_component_from_func(
    add,
    base_image="image-registry.openshift-image-registry.svc:5000/openshift/python:latest",
)


@kfp.dsl.pipeline(
    name="PVC Pipeline",
)
def add_pipeline(a="1", b="7"):
    """
    Pipeline to add values.

    Pipeline to take the value of a, add 4 to it and then
    perform a second task to take the put of the first task and add b.
    """
    first_add_task = add_op(a, 4)

    vol = kubernetes.client.V1Volume(
        name="my-data",
        persistent_volume_claim=kubernetes.client.V1PersistentVolumeClaimVolumeSource(
            claim_name="my-data"
        ),
    )

    first_add_task.add_pvolumes({"/opt/data": vol})

    second_add_task = add_op(first_add_task.output, b)  # noqa: F841


if __name__ == "__main__":
    client = kfp_tekton.TektonClient(
        host=urllib.parse.urljoin(kubeflow_endpoint, "/pipeline"),
        existing_token=bearer_token,
    )
    arguments = {"a": "7", "b": "8"}
    client.create_run_from_pipeline_func(
        add_pipeline, arguments=arguments, experiment_name="pvc-example"
    )
