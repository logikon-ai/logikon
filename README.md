# Logikon – Debugging and Scoring Reasoning Traces of LLMs


### Score completions with one extra line of code

```python
import openai
import logikon

# LLM generation
prompt = "Vim or Emacs? Reason carefully before submitting your choice."
completion = openai.Completion.create(model="text-davinci-003", prompt=prompt).choices[0].text

# Debug and score reasoning
score = logikon.score(prompt=prompt, completion=completion)
```


### Configure metrics, artifacts and debugging methods

```python
import logikon

# Configure scoring methods
lgk_config = logikon.Config(
    expert_model = "code-davinci-002",  # expert LLM to use
    metrics = "REASON_DEPTH",
    artifacts = "ARGDOWN_SVG",
)

...

# Debug and score reasoning
score = logikon.score(config=lgk_config, prompt=prompt, completion=completion)
```


### Simple reporting

```python
import logikon

# Log scores and artifacts to wandb and langfuse
lgk_config = logikon.Config(
    report_to = ["wandb", "langfuse"]
)

...

# Debug and score reasoning
score = logikon.score(config=lgk_config, prompt=prompt, completion=completion)
```


### LangChain integration

```python
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

import logikon

# Configure logikon debugger
lgk_handler = logikon.CallbackHandler(config=logikon.Config(report_to=["wandb"]))

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




