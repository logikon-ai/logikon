
<center>
<h1><code>/\/</code> Logikon</h1>
<h4>Analytics for LLM Reasoning Traces</h3>
[Docs🚧] &nbsp; [<a href="./examples">Examples</a>]
<p>
</center>



**Logikon `/\/`** is a library for analyzing and scoring the quality of plain-text reasoning traces produced by LLMs (or humans). It reveals the argumentative structure of LLM outputs, visualizes reasoning complexity, and evaluates its quality.

**Logikon `/\/`** allows you to automatically supervise the AI agents in your advanced LLM apps. This can be used for debugging and monitoring your AI assistants, or for evaluating the quality of human–AI interaction.

**Logikon `/\/`** is highly customizable and extensible. You can choose from a variety of metrics, artifacts, and methods, choose the expert LLM for logical analysis, and even build your own metrics on top of **logikon**'s artifacts.


> [!WARNING]
> **Logikon `/\/`** is currently in beta. The API is subject to change. Please be patient, and report any issues you encounter.


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

Under the hood, 

### Configure metrics, artifacts and debugging methods

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


### Installation and Quickstart

See [examples](./examples).






