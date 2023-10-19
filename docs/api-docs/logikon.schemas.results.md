<!-- markdownlint-disable -->

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/schemas/results.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `logikon.schemas.results`




**Global Variables**
---------------
- **INPUT_KWS**


---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/schemas/results.py#L17"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `BaseCTModel`
Base model for all entities processed or created through logical analysis. 





---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/schemas/results.py#L25"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `Artifact`
An artifact serving as input and/or generated through logical debugging. 





---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/schemas/results.py#L32"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `Score`
A score for a completion / reasoning trace. 





---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/schemas/results.py#L39"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `DebugState`
Scores for the completion. 




---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/schemas/results.py#L46"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `get_prompt_completion`

```python
get_prompt_completion() → Tuple[Optional[str], Optional[str]]
```

convenience method that returns prompt and completion from inputs 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
