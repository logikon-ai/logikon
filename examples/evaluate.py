"""Evaluation script for logikon argumentation analysts
"""

from typing import Optional

import dataclasses
import datetime
import json
import logging
import os
import pprint
import tempfile
import tqdm
import uuid

import datasets
import huggingface_hub as hf_hub
import logikon
import networkx as nx
import typer

from logikon.schemas.configs import ScoreConfig


logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logging.info(f"Installed `logikon` module version: {logikon.__version__}")


@dataclasses.dataclass
class ReferenceDataset:
    """Reference dataset metadata."""

    path: str
    id_field: str = None
    split: str = None
    revision: str = None


@dataclasses.dataclass
class EvalResultRecord:
    """Evaluation result record."""

    id: str
    reference_id: str
    reference_dataset: dict
    lang: str
    created_date: str
    argmap: dict
    scores: dict
    model: str
    metadata: dict


def load_results(results_dataset: dict) -> list[EvalResultRecord]:
    "download the eval results dataset (if exists)"
    eval_results = []

    if hf_hub.file_exists(
        results_dataset["path"],
        os.path.join(results_dataset["subfolder"], results_dataset["filename"]),
        repo_type="dataset",
        token=os.environ["HUGGINGFACEHUB_API_TOKEN"],
    ):
        eval_file = hf_hub.hf_hub_download(
            results_dataset["path"],
            filename=results_dataset["filename"],
            subfolder=results_dataset["subfolder"],
            repo_type="dataset",
        )

        with open(eval_file) as f:
            for line in f:
                record = EvalResultRecord(**json.loads(line))
                eval_results.append(record)

        logging.info(f"Loaded {len(eval_results)} eval results.")

    else:
        logging.info("No eval results loaded.")

    return eval_results


def upload_results(eval_results: list[EvalResultRecord], results_dataset: dict):
    "upload the eval results dataset"

    with tempfile.NamedTemporaryFile() as tmpf:
        for record in eval_results:
            tmpf.write(json.dumps(dataclasses.asdict(record)).encode("utf-8"))
            tmpf.write("\n".encode("utf-8"))
        tmpf.flush()

        api = hf_hub.HfApi()
        api.upload_file(
            path_or_fileobj=tmpf.name,
            path_in_repo=os.path.join(results_dataset["subfolder"], results_dataset["filename"]),
            repo_id=results_dataset["path"],
            repo_type="dataset",
            token=os.environ["HUGGINGFACEHUB_API_TOKEN"],
        )

        logging.info(f"Uploaded {len(eval_results)} eval results.")


def main(
    artifacts: list[str] = typer.Option(["fuzzy_argmap_nx"], help="Artifacts to create."),
    metrics: list[str] = typer.Option(
        ["argmap_size", "n_root_nodes", "argmap_avg_katz_centrality", "argmap_attack_ratio"], help="Metrics to compute."
    ),
    expert_model: str = typer.Option("stabilityai/StableBeluga-13B", help="Expert model to use."),
    expert_tokenizer: str = typer.Option("stabilityai/StableBeluga-13B", help="Expert tokenizer to use."),
    use_cuda: bool = typer.Option(True, help="Use cuda."),
    load_in_8bit: bool = typer.Option(True, help="Load model in 8bit."),
    low_cpu_mem_usage: bool = typer.Option(True, help="Use low cpu mem usage."),
    llm_framework: str = typer.Option("transformers", help="LLM framework to use."),
    reference_dataset_path: str = typer.Option("logikon/oasst1-delib", help="Source dataset path."),
    reference_dataset_split: str = typer.Option("validation", help="Source dataset split."),
    reference_dataset_revision: str = typer.Option(None, help="Source dataset revision."),
    reference_dataset_id_field: str = typer.Option('message_id', help="Source dataset id field."),
    results_dataset_path: str = typer.Option('logikon/delib-evals', help="Results dataset path."),
    lang: str = typer.Option('en', help="Language."),
    upload_steps: int = typer.Option(5, help="Upload results every n steps."),
):
    expert_model_kwargs = {}
    if use_cuda is not None:
        expert_model_kwargs["cuda"] = use_cuda
    if load_in_8bit is not None:
        expert_model_kwargs["load_in_8bit"] = load_in_8bit
    if low_cpu_mem_usage is not None:
        expert_model_kwargs["low_cpu_mem_usage"] = low_cpu_mem_usage
    if expert_tokenizer is not None:
        expert_model_kwargs["tokenizer"] = expert_tokenizer

    config = ScoreConfig(
        artifacts=artifacts,
        metrics=metrics,
        global_kwargs=dict(
            expert_model=expert_model,
            expert_model_kwargs=expert_model_kwargs,
            generation_kwargs=dict(
                max_len=3072,
            ),
            llm_framework=llm_framework,
        ),
    )

    reference_dataset = ReferenceDataset(
        path=reference_dataset_path,
        id_field=reference_dataset_id_field,
        split=reference_dataset_split,
        revision=reference_dataset_revision,
    )

    results_dataset = dict(
        path=results_dataset_path,
        filename=f"{expert_model.replace('/','_')}_{reference_dataset.split}.jsonl",
        subfolder=os.path.join("data", reference_dataset.path),
    )

    if not os.environ.get("HUGGINGFACEHUB_API_TOKEN"):
        logging.warning(
            "No HUGGINGFACEHUB_API_TOKEN found in environment. Please set one to upload results to huggingface.co."
        )

    # load the reference dataset
    ref_ds = datasets.load_dataset(
        reference_dataset.path,
        split=reference_dataset.split,
        revision=reference_dataset.revision,
    )

    assert (
        reference_dataset.id_field in ref_ds.features
    ), f"Reference dataset must have {reference_dataset.id_field} field."

    # load the results dataset
    eval_results = load_results(results_dataset)

    n_records_unsaved = 0

    # iterate over the reference dataset
    for enum, example in enumerate(tqdm(ref_ds)):
        if any(r.reference_id == example[reference_dataset.id_field] for r in eval_results):
            logging.debug(f"Skipping {example[reference_dataset.id_field]}: alreday scored.")
            continue

        if len(example["history"].split()) + len(example["text"].split()) > 900:
            logging.warning(f"Too long: Skipping {example[reference_dataset.id_field]}")
            continue

        logging.debug(f"Scoring example {enum} of {len(ref_ds)}.\n")
        logging.debug(example["history"])
        logging.debug(example["text"])
        debug_results = logikon.score(prompt=example["history"], completion=example["text"], config=config)

        argmap = next((a.data for a in debug_results.artifacts if a.id == "fuzzy_argmap_nx"), None)
        argmap = nx.node_link_data(argmap) if argmap else {}

        scores = {
            "id": [],
            "value": [],
            "comment": [],
        }
        for score in debug_results.scores:
            for key in scores:
                scores[key].append(score.__getattribute__(key))
        scores["names"] = scores.pop("id")
        scores["values"] = scores.pop("value")
        scores["comments"] = scores.pop("comment")

        eval_record = EvalResultRecord(
            id=str(uuid.uuid4()),
            reference_id=example[reference_dataset.id_field],
            reference_dataset=dataclasses.asdict(reference_dataset),
            lang=example.get("lang", lang),
            created_date=datetime.datetime.now().isoformat(),
            argmap=argmap,
            scores=scores,
            model=expert_model,
            metadata={"logikon_config": config.dict(), "logikon_version": logikon.__version__},
        )

        eval_results.append(eval_record)
        n_records_unsaved += 1

        if n_records_unsaved >= upload_steps:
            upload_results(eval_results, results_dataset)
            n_records_unsaved = 0

    # upload pending results
    if n_records_unsaved > 0:
        upload_results(eval_results, results_dataset)


if __name__ == "__main__":
    typer.run(main)
