# Logikon – Debugging and Scoring Reasoning Traces of LLMs


### Score completions with one extra line of code

```python
"""Score completions with one extra line of code"""

import openai
import logikon

# LLM generation
prompt = "Vim or Emacs? Reason carefully before submitting your choice."
completion = openai.Completion.create(model="text-davinci-003", prompt=prompt).choices[0].text

# Debug and score reasoning
score = logikon.score(prompt=prompt, completion=completion)

#  >>> print(score)
#  n_arguments=5
#  redundancy=.13
#  pros_cons_balance=.6
```


### Configure metrics, artifacts and debugging methods

```python
"""Configure metrics, artifacts and debugging methods"""

import logikon

# Configure scoring methods
config = logikon.DebugConfig(
    expert_model = "code-davinci-002",  # expert LLM for logical analysis
    metrics = ["argmap_attack_ratio"],  # ratio of objections
    artifacts = ["svg_argmap"],         # argument map as svg
)

# LLM generation
...

# Debug and score reasoning
score = logikon.score(config=config, prompt=prompt, completion=completion)
```


### Simple reporting

```python
"""Simple reporting"""

import logikon

your_mlops_platforms = ["wandb", "langfuse", ...]


# Log scores and artifacts to wandb and langfuse
config = logikon.DebugConfig(
    report_to=your_mlops_platforms
)

# LLM generation
...

# Debug and score reasoning
score = logikon.score(config=config, prompt=prompt, completion=completion)
```


### LangChain integration

```python
"""LangChain integration"""

from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

import logikon

# Configure logikon debugger
config = logikon.DebugConfig(report_to=your_mlops_platforms)
lgk_handler = logikon.CallbackHandler(config=config)

# Set up chain and register debugger
llm = OpenAI()
prompt = PromptTemplate(
    input_variables=["question"],
    template="{question} Reason carefully before submitting your choice.",
)
chain = LLMChain(llm=llm, prompt=prompt, callbacks=[lgk_handler])

# Run chain
print(chain.run("Vim or Emacs?", callbacks=[lgk_handler]))
```



### Evaluate Human -- AI interaction

```python
"""Evaluate a chat history"""

´import logikon

# Chat between human user and AI assistant
...

chat_history = retrieve_chat_history()

# Debug and score reasoning
score = logikon.score(messages=chat_history)
```


