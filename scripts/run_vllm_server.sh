#!bin/bash

MODEL_ID="openchat/openchat_3.5"

HF_HUB_ENABLE_HF_TRANSFER="1" python -m vllm.entrypoints.openai.api_server \
  --model $MODEL_ID \
  --max-logprobs 100