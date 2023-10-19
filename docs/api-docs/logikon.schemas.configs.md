<!-- markdownlint-disable -->

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/schemas/configs.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `logikon.schemas.configs`






---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/schemas/configs.py#L11"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `DebugConfig`
Configuration for scoring reasoning traces. 



**Args:**
 
 - <b>`expert_model`</b>:  The name of the expert model to use. 
 - <b>`expert_model_kwargs`</b>:  Keyword arguments to pass to the expert model. 
 - <b>`llm_framework`</b>:  The name of the language model framework to use (e.g., OpenAI, VLLM). 
 - <b>`inputs`</b>:  The inputs to the expert model (Artifacts or Scores). 
 - <b>`metrics`</b>:  The metrics to use for scoring (keyword or debugger class). 
 - <b>`artifacts`</b>:  The artifacts to generate (keyword or debugger class). 
 - <b>`report_to`</b>:  Integrations. 

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/schemas/configs.py#L34"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `__init__`

```python
__init__(**data: 'Any')
```











---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
