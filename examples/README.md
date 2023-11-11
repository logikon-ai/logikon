# Examples

All example notebooks are tested and run on a free [Google Colab](https://colab.research.google.com/) instance with GPU acceleration.

* [quickstart.ipynb](./quickstart.ipynb) - demonstrates configuration and basic usage of **Logikon `/\/`**.
* [metrics_artifacts_zoo.ipynb](./metrics_artifacts_zoo.ipynb) - showcases the different metrics and artifacts that can be created with **Logikon `/\/`**.

The Jupyter notebooks analyze reasoning traces by evoking the python script `scoring.py`, which is simply a convenient wrapper around the `logikon.score()` function. As such, `scoring.py` also illustrates how to use the `logikon` API. (Why not call `logikon.score()` directly from Jupyter notebooks? Doesn't work as `logikon` is built with [`LMQL`](https://lmql.ai).)

For more info on how to use `scoring.py`, see the [Quickstart](./quickstart.ipynb) notebook or run `python scoring.py --help`.

