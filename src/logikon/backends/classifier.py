import asyncio
import logging
from typing import Any

import requests  # type: ignore
from pydantic import BaseModel
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)

_DEFAULT_BATCH_SIZE = 800
_MAX_CLASSES = 12


class HfClassification(BaseModel):
    sequence: str
    labels: list[str]
    scores: list[float]


class HfClassifier:
    """HfClassifier
    Wrapper around HF Inference Endpoint for sequence classification
    """

    def __init__(self, model_id: str, api_key: str, inference_server_url: str, batch_size: int = _DEFAULT_BATCH_SIZE):
        self.model_id = model_id
        self.api_key = api_key
        self.inference_server_url = inference_server_url
        self.batch_size = batch_size

    async def __call__(
        self,
        inputs: list[str] | str,
        hypothesis_template: str,
        classes_verbalized: list[str],
        batch_size: int | None = None,
    ) -> list[HfClassification | dict[str, Any]]:

        if not classes_verbalized:
            msg = "No classes provided"
            raise ValueError(msg)
        if isinstance(inputs, str):
            inputs = [inputs]
        if len(classes_verbalized) > _MAX_CLASSES:
            msg = "Maximum number of categories exceeded."
            logging.getLogger(__name__).error(f"{msg} {classes_verbalized}")
            raise ValueError(msg)

        if batch_size is None:
            batch_size = self.batch_size
        batch_size = min(len(inputs), self.batch_size)

        headers = {"Authorization": f"Bearer {self.api_key}"}

        @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
        async def query(payload):
            response = requests.post(self.inference_server_url, headers=headers, json=payload, timeout=30)
            return response.json()

        coros = []

        for batch_idx in range(0, len(inputs), self.batch_size):
            input_batch = inputs[batch_idx : batch_idx + self.batch_size]

            coros.append(
                query(
                    {
                        "inputs": input_batch,
                        "parameters": {
                            "batch_size": batch_size,
                            "candidate_labels": classes_verbalized,
                            "hypothesis_template": hypothesis_template,
                        },
                    }
                )
            )

        outputs = await asyncio.gather(*coros)
        outputs = [x for batch in outputs for x in batch]  # flatten

        # postprocess
        for i, res in enumerate(outputs):
            if "sequence" in res:
                try:
                    outputs[i] = HfClassification(**res)
                except Exception as e:
                    msg = f"Error parsing response: {e}"
                    logging.getLogger(__name__).warning(msg)

        return outputs
