# Examples

All example notebooks are tested and run on a free [Google Colab](https://colab.research.google.com/) instance with GPU acceleration.

* [quickstart.ipynb](./quickstart.ipynb) - demonstrates configuration and basic usage of **Logikon `/\/`**.
* [metrics_artifacts_zoo.ipynb](./metrics_artifacts_zoo.ipynb) - showcases the different metrics and artifacts that can be created with **Logikon `/\/`**.
* [monitor_cot_workflow.ipynb](./monitor_cot_workflow.ipynb) - illustrates how to monitor the intermediary (chain-of-thought) reasoning processes of an advanced LLM app.
* [legal_hallucination_detection.ipynb](./legal_hallucination_detection.ipynb) - shows how to build your own metrics and evaluations on top of **Logikon `/\/`** artifacts (here: detect hallucinations by Legal AI).

The Jupyter notebooks analyze reasoning traces by evoking the python script `scoring.py`, which is simply a convenient wrapper around the `logikon.score()` function. As such, `scoring.py` also illustrates how to use the `logikon` API. (Why not call `logikon.score()` directly from Jupyter notebooks? Doesn't work as `logikon` is built with [`LMQL`](https://lmql.ai).)

For more info on how to use `scoring.py`, see the [Quickstart](./quickstart.ipynb) notebook or run `python scoring.py --help`.

