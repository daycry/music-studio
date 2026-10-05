"""Factoría HTTP: importación ligera; los modelos viven en el proceso hijo."""

import os

from descriptor import CHECKPOINT, LM, descriptor
from engine_common import create_app as common_app
from preflight import preflight


def create_app(**kwargs):
    checkpoint = os.getenv("STUDIO_ACESTEP_CHECKPOINT", CHECKPOINT)
    lm = os.getenv("STUDIO_ACESTEP_LM", LM)
    return common_app(
        [descriptor(checkpoint=checkpoint, lm=lm)],
        "adapter:AceStepAdapter",
        adapter_options={"checkpoint": checkpoint, "lm": lm},
        engine_id="acestep",
        preflight=lambda request: preflight(
            request, lm=lm, checkpoint=checkpoint, timeout=min(60, request["timeout_s"])
        ),
        **kwargs,
    )
