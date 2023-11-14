
<div align="center">

<img src="./docs/logo_logikon_notext_withborder.png" alt="Logikon Logo" width=100></img>

# Logikon

Analytics for LLM Reasoning Traces.

[Highlights](#highlights) •
[Analytics](#analytics) •
[Examples](#examples) •
[Stay tuned](#stay-tuned-for) •
Docs 🚧

</div>


**Logikon `/\/`** is a library for analyzing and scoring the quality of plain-text reasoning traces produced by LLMs (or humans). It reveals the argumentative structure of LLM outputs, visualizes reasoning complexity, and evaluates its quality.

**Logikon `/\/`** allows you to automatically supervise the AI agents in your advanced LLM apps. This can be used for debugging and monitoring your AI assistants, or for evaluating the quality of human–AI interaction.

**Logikon `/\/`** is highly customizable and extensible. You can choose from a variety of metrics, artifacts, and evaluation methods, pick an expert LLM for logical analysis, and even build your own metrics on top of **Logikon**'s artifacts.


> [!WARNING]
> **Logikon `/\/`** is currently in early beta. The API is subject to change. Please be patient, and report any issues you encounter.

## Installation

```sh
pip install git+https://github.com/logikon-ai/logikon@v0.0.1-dev1
```

See [examples folder](./examples) for more details.

## Highlights

### Analyze and score completions with one extra line of code

```python
# LLM generation
prompt = "Vim or Emacs? Reason carefully before submitting your choice."
completion = llm.predict(prompt)

# Debug and score reasoning 🚀
import logikon

score = logikon.score(prompt=prompt, completion=completion)

#  >>> print(score.info())
#  argmap_size: 13
#  n_root_nodes: 3
#  global_balance: -.23
```


### Configure metrics, artifacts and evaluation methods

```python
import logikon

# Configure scoring methods
config = logikon.ScoreConfig(
    expert_model = "code-davinci-002",  # expert LLM for logical analysis
    metrics = ["argmap_attack_ratio"],  # ratio of objections
    artifacts = ["svg_argmap"],         # argument map as svg
)

# LLM generation
...

# Debug and score reasoning
score = logikon.score(config=config, prompt=prompt, completion=completion)
```

## Analytics


### Argumentation quantity metrics

Score the quantity of arguments in the reasoning trace.

* [x] number of arguments
* [x] number of central claims
* [x] density of argumentation network

> **🤔 What for?**
>
> 👉 Detect where your LLM fails to generate (sufficiently many) reasons when deliberating a decision or justifying an answer it has given—which may lead to poor AI decision-making and undermine AI explainability.


### Argumentative bias metrics

Score the balance of arguments in the reasoning trace.

* [x] mean support/attack bias averaged over all central claims
* [x] global support/attack balance
* [x] naive pros/cons ratio

> **🤔 What for?**
>
> 👉 Detect whether your (recently updated) advanced LLM app suddenly produces biased reasoning—which may indicate flawed reasoning that reduces your app's performance.

### Argumentation clarity metrics 🚧

Score the presentation of arguments in the reasoning trace.

* [ ] transparency of exposition 
* [ ] redundancy of presentation
* [ ] ambiguity of argument articulation
* [ ] veracity of surface logical structure 

> **🤔 What for?**
>
> 👉 Detect whether your LLM fails to render its reasoning in comprehensible ways—which may impair human-AI interaction, or prevent other AI agents from taking the reasoning fully into account.


For more technical info on our metrics, see our [Critical Thinking Zoo notebook](./examples/metrics_artifacts_zoo.ipynb) and the code's [analyst registry](https://github.com/logikon-ai/logikon/blob/eaa41db5763ce8aca24818fd3130078b20d8ed90/src/logikon/analysts/registry.py#L30).


### Argument mapping artifacts

Reveal, represent or visualize the argumentation, based on a charitable and systematic reconstruction of the reasoning trace.

- [x] pros and cons list
- [x] ✨fuzzy✨ argument map
- [x] argument map as svg
- [x] nested pros cons sunburst 

> **🤔 What for?**
>
> 👉 Check visualizations rather then read lengthy reasoning traces when debugging your LLM app. <br/>
> 👉 Build your own metrics and evaluations exploiting the deep structure revealed by our artifacts.



### Argumentative text annotation artifacts 🚧

Annotate reasons, arguments and argumentative relations in LLM-generated argumentative texts.

- [ ] argumentative entity annotation
- [ ] argumentative relation annotation


> **🤔 What for?**
>
> 👉 Check visualizations rather then read lengthy reasoning traces when debugging your LLM app. <br/>
> 👉 Build your own metrics and evaluations exploiting our annotations of LLM-generated texts.



For more technical info on our artifacts, see our [Critical Thinking Zoo notebook](./examples/metrics_artifacts_zoo.ipynb) and the code's [analyst registry](https://github.com/logikon-ai/logikon/blob/eaa41db5763ce8aca24818fd3130078b20d8ed90/src/logikon/analysts/registry.py#L30).


## Examples

* [Quickstart](./examples/quickstart.ipynb)
* [Critical Thinking Zoo](./examples/metrics_artifacts_zoo.ipynb)
* ...

See [examples folder](./examples) for details and more.


## Known limitations

* ...


## Stay tuned for

* More examples [#1](https://github.com/logikon-ai/logikon/issues/1)
* Integrations with MLOps tools [#2](https://github.com/logikon-ai/logikon/issues/2)
* Model benchmarks and validation
* More metrics and artifacts
* Speedups and optimizations
* **Logikon `/\/` Cloud**







