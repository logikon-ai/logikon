#!/bin/bash

# N.B.: Must be called from root dir in logikon2 repo

### APT INSTALLS ##

apt-get update && apt install graphviz -y


### PIP INSTALLS ##

pip uninstall -y transformer-engine
pip install -e ".[vllm]"
pip uninstall flash-attn -y
pip install flash-attn -U --no-build-isolation
pip install -q gradio

