#!/usr/bin/env python
# Copyright 2023 The Logikon AI Team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Scoring script for logikon argumentation analysts

- Loads reasoning traces to score.
- Loads scoring config from yaml file / command args.
- Analyses and scores examples with `logikon`.
- Saves results in output folder.

Usage:

    > python scoring.py --help

"""

import argparse
import dataclasses
import json
import logging
import os
import sys

import networkx as nx
import pandas as pd
import tqdm
import yaml

import logikon
from logikon.schemas.configs import ScoreConfig

_MAX_WORDS = 900  # max word count of prompt+completion to analyze

logging.basicConfig(
    level=logging.INFO, filename="scoring.log", filemode="w", format="%(name)s - %(levelname)s - %(message)s"
)
logging.info(f"Installed `logikon` module version: {logikon.__version__}")


def get_parser() -> argparse.ArgumentParser:
    "get parser for scoring script"
    parser = argparse.ArgumentParser(description="Score reasoning traces with logikon module.")
    parser.add_argument(
        "--config-file",
        default=None,
        help="Path to yaml config file.",
    )
    parser.add_argument(
        "--artifacts",
        nargs="+",
        default=None,
        help="Artifacts to create.",
    )
    parser.add_argument(
        "--metrics",
        nargs="+",
        default=None,
        help="Metrics to calculate.",
    )
    parser.add_argument(
        "--expert-model-path",
        default=None,
        help="Expert model path to use.",
    )
    parser.add_argument(
        "--expert-tokenizer",
        default=None,
        help="Expert tokenizer to use.",
    )
    parser.add_argument(
        "--endpoint",
        default=None,
        help="LMQL serve-model endpoint.",
    )
    parser.add_argument(
        "--use-cuda",
        default=None,
        help="Use cuda. (With transformers framework)",
        action=argparse.BooleanOptionalAction,
    )
    parser.add_argument(
        "--load-in-8bit",
        default=None,
        help="Load model in 8bit. (With transformers framework)",
        action=argparse.BooleanOptionalAction,
    )
    parser.add_argument(
        "--low-cpu-mem-usage",
        default=None,
        help="Use low cpu mem usage. (With transformers framework)",
        action=argparse.BooleanOptionalAction,
    )
    parser.add_argument(
        "--n-ctx",
        default=None,
        help="Context length (with llama.cpp).",
        type=int,
    )
    parser.add_argument(
        "--n-gpu-layers",
        default=None,
        help="Number of GPU layers (with llama.cpp).",
        type=int,
    )
    parser.add_argument(
        "--llm-framework",
        choices=["transformers", "llama.cpp"],
        default=None,
        help="LLM framework to use.",
    )
    parser.add_argument(
        "--prompt-template",
        default=None,
        help="Prompt template to use (path-to-yaml-file or keyword).",
    )
    parser.add_argument(
        "--generation-max-len",
        default=None,
        type=int,
        help="Generation max length.",
    )
    parser.add_argument(
        "--reasoning-traces-file",
        default=None,
        required=True,
        help="Path to jsonl file with reasoning traces to analyze and score.",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Output directory.",
    )
    parser.add_argument(
        "--output-file",
        default=None,
        help="Custom output filename (defaults to '{{inputfile}}-scores.jsonl').",
    )
    return parser


def sanity_check_files(args: argparse.Namespace):
    "check if input and/or output files exist"
    if not os.path.isfile(args.reasoning_traces_file):
        msg = f"Reasoning traces file {args.reasoning_traces_file} does not exist."
        logging.error(msg)
        sys.stderr.write(msg)
        sys.exit(1)
    if not args.reasoning_traces_file.endswith(".jsonl") or not len(args.reasoning_traces_file) > len(
        ".jsonl"
    ):
        msg = f"Reasoning traces file {args.reasoning_traces_file} must be a jsonl file."
        logging.error(msg)
        sys.stderr.write(msg)
        sys.exit(1)
    if not args.output_file:
        root = os.path.splitext(os.path.basename(args.reasoning_traces_file))[0]
        args.output_file = f"{root}-scores.jsonl"
    if os.path.isfile(os.path.join(args.output_dir, args.output_file)):
        msg = (
            f"Output file {os.path.join(args.output_dir, args.output_file)} already exists. "
            f"Please delete it or choose another output file."
        )
        logging.error(msg)
        sys.stderr.write(msg)
        sys.exit(1)


def load_reasoning_traces_file(reasoning_traces_file: str) -> pd.DataFrame:
    "load reasoning traces from file"
    df_traces = pd.read_json(reasoning_traces_file, lines=True)
    if "id" not in df_traces.columns:
        df_traces["id"] = df_traces.index
    if "prompt" not in df_traces.columns:
        msg = (
            f"Reasoning traces file {reasoning_traces_file} must have 'prompt' column. "
            f"Found column names: {df_traces.columns}"
        )
        logging.error(msg)
        sys.stderr.write(msg)
        sys.exit(1)
    if "completion" not in df_traces.columns:
        msg = (
            f"Reasoning traces file {reasoning_traces_file} must have 'completion' column. "
            f"Found column names: {df_traces.columns}"
        )
        logging.error(msg)
        sys.stderr.write(msg)
        sys.exit(1)
    return df_traces


def save_results(eval_results: list[dict], output_dir: str, output_file: str):
    "save the scoring results by appending them to file"

    os.makedirs(output_dir, exist_ok=True)

    with open(os.path.join(output_dir, output_file), "a") as f:
        for record in eval_results:
            f.write(json.dumps(record) + "\n")

        logging.info(f"Saved {len(eval_results)} eval results to {output_file}.")


def main():
    parser = get_parser()
    args = parser.parse_args()
    sanity_check_files(args)

    # try to load config from yaml file
    if args.config_file:
        if not os.path.isfile(args.config_file):
            msg = f"Config file {args.config_file} does not exist."
            logging.error(msg)
            sys.exit(1)
        config_data = dict(ScoreConfig.from_yaml(args.config_file))
    else:
        config_data = {}

    # check if prompt template is file, parse yaml
    if args.prompt_template and os.path.isfile(args.prompt_template):
        with open(args.prompt_template) as f:
            prompt_template = yaml.safe_load(f)
    else:
        prompt_template = args.prompt_template

    expert_model_kwargs = {}
    if args.endpoint is not None:
        expert_model_kwargs["endpoint"] = args.endpoint
    if args.use_cuda is not None:
        expert_model_kwargs["cuda"] = args.use_cuda
    if args.load_in_8bit is not None:
        expert_model_kwargs["load_in_8bit"] = args.load_in_8bit
    if args.low_cpu_mem_usage is not None:
        expert_model_kwargs["low_cpu_mem_usage"] = args.low_cpu_mem_usage
    if args.expert_tokenizer is not None:
        expert_model_kwargs["tokenizer"] = args.expert_tokenizer
    if args.n_ctx is not None:
        expert_model_kwargs["n_ctx"] = args.n_ctx
    if args.n_gpu_layers is not None:
        expert_model_kwargs["n_gpu_layers"] = args.n_gpu_layers
    if prompt_template is not None:
        expert_model_kwargs["prompt_template"] = prompt_template

    if args.artifacts:
        config_data["artifacts"] = args.artifacts

    if args.metrics:
        config_data["metrics"] = args.metrics

    if not config_data.get("global_kwargs"):
        config_data["global_kwargs"] = {}

    if expert_model_kwargs:
        if not config_data["global_kwargs"].get("expert_model_kwargs"):
            config_data["global_kwargs"]["expert_model_kwargs"] = {}
        config_data["global_kwargs"]["expert_model_kwargs"].update(expert_model_kwargs)

    if args.expert_model_path:
        config_data["global_kwargs"]["expert_model"] = args.expert_model_path

    if args.llm_framework:
        config_data["global_kwargs"]["llm_framework"] = args.llm_framework

    if not config_data["global_kwargs"].get("generation_kwargs"):
        config_data["global_kwargs"]["generation_kwargs"] = {}
    if args.generation_max_len:
        config_data["global_kwargs"]["generation_kwargs"]["max_len"] = args.generation_max_len
    elif not config_data["global_kwargs"]["generation_kwargs"].get("max_len"):
        config_data["global_kwargs"]["generation_kwargs"]["max_len"] = 3072

    config = ScoreConfig(**config_data)
    logging.info(f"Scoring config: {dict(config)}")

    # load the reasoning traces
    df_traces = load_reasoning_traces_file(args.reasoning_traces_file)

    results: list[dict] = []

    # iterate over the reasoning dataset and score each example
    for i, row in tqdm.tqdm(df_traces.iterrows()):
        if len(row.prompt.split()) + len(row.completion.split()) > _MAX_WORDS:
            logging.warning(f"Too long: Skipping example {row.id}")
            continue

        logging.info(f"Scoring example {i} of {len(df_traces)} with id {row.id}.\n")
        logging.debug(row.prompt)
        logging.debug(row.completion)
        try:
            score_result = logikon.score(prompt=row.prompt, completion=row.completion, config=config)
        except Exception as e:
            logging.error(f"Error scoring {row.to_dict()}: {e}")
            score_result = None

        result_record = {"id": row.id}
        for metric_id in config.metrics:
            result_record[metric_id] = score_result.value(metric_id)
        for artifact_id in config.artifacts:
            artifact = score_result.get_artifact(artifact_id)
            if isinstance(artifact.data, nx.DiGraph):
                node_link_data = nx.node_link_data(artifact.data)
                result_record[artifact_id] = node_link_data
            else:
                result_record[artifact_id] = artifact.data if artifact else None

        # save new result
        save_results([result_record], args.output_dir, args.output_file)

        results.append(result_record)

    logging.info(f"Completed scoring {len(df_traces)} examples, created {len(results)} result records.")

if __name__ == "__main__":
    main()
