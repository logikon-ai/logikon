#!/bin/bash

# framework llamacpp or transformers()
if [ -z "${LGK_FRAMEWORK}" ]; then
  FRAMEWORK="llamacpp"  # default
else
  FRAMEWORK="${LGK_FRAMEWORK}"
fi

# device (gpu or cpu)
if [ -z "${LGK_DEVICE}" ]; then
  DEVICE="gpu"  # default
else
  DEVICE="${LGK_DEVICE}"
fi

# model to download
if [ -z "${LGK_HUBREPO}" ]; then
  HUBREPO="TheBloke/zephyr-7B-beta-GGUF"  # default
else
  HUBREPO="${LGK_HUBREPO}"
fi
if [ -z "${LGK_MODELWEIGHTS}" ]; then
  MODELWEIGHTS="zephyr-7b-beta.Q6_K.gguf"  # default
else
  MODELWEIGHTS="${LGK_MODELWEIGHTS}"
fi

# logikon release tag
if [ -z "${LGK_RELEASE}" ]; then
  RELEASE="v0.0.1-dev1"  # default
else
  RELEASE="${LGK_RELEASE}"
fi

# install graphviz (needed for svg argument maps)
if [ -z "${LGK_GRAPHVIZ}" ]; then
  GRAPHVIZ=1  # default
else
  GRAPHVIZ="${LGK_GRAPHVIZ}"
fi

# install in venv
if [ -z "${LGK_VENV}" ]; then
  VENV="" # ".venv"  # default
else
  VENV="${LGK_VENV}"
fi

echo "Setting up environment with:"
echo "  framework: ${FRAMEWORK}"
echo "  device: ${DEVICE}"
echo "  hub repo: ${HUBREPO}"
echo "  model weights: ${MODELWEIGHTS}"
echo "  logikon release: ${RELEASE}"
echo "  install graphviz: ${GRAPHVIZ}"
echo "  install in venv: ${VENV}"


### APT INSTALLS ##

if [ $GRAPHVIZ -gt 0 ]; then
    apt-get update && apt install graphviz -y
fi


### PIP INSTALLS ##

if [ "$VENV" != "" ]; then
    python3 -m venv $VENV
    . ${VENV}/bin/activate
fi

pip install --upgrade pip
pip install -r ./requirements.txt

if [ "$FRAMEWORK" = "llamacpp" ]; then
    if [ "$DEVICE" = "gpu" ]; then
        CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python
    else
        pip install llama-cpp-python
    fi
fi

if [ "$FRAMEWORK" = "transformers" ]; then
    pip install accelerate bitsandbytes
fi

pip install -U git+https://${GH_ACCESS_TOKEN}@github.com/logikon-ai/logikon.git@${RELEASE}


## DOWNLOADS ##

if [ "$FRAMEWORK" = "llamacpp" ]; then
    # download gguf model weights only
    HF_HUB_ENABLE_HF_TRANSFER=1 huggingface-cli download $HUBREPO $MODELWEIGHTS --local-dir=./models
elif [ "$FRAMEWORK" = "transformers" ]; then
    # download entire repo
    HF_HUB_ENABLE_HF_TRANSFER=1 huggingface-cli download $HUBREPO --local-dir=./models/${HUBREPO}
fi