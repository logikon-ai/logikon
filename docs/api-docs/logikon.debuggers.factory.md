<!-- markdownlint-disable -->

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/factory.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `logikon.debuggers.factory`






---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/factory.py#L15"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `DebuggerFactory`
Factory for creating a debugger pipeline based on a config. 


---

#### <kbd>property</kbd> logger

A :class:`logging.Logger` that can be used within the :meth:`run()` method. 



---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/factory.py#L49"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `create`

```python
create(config: 'DebugConfig') → Optional[Callable]
```

Create a debugger pipeline based on a config. 

---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/factory.py#L18"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `run_pipeline`

```python
run_pipeline(
    pipeline: 'List[Debugger]',
    inputs: 'List[Artifact]' = [],
    debug_state: 'Optional[DebugState]' = None
)
```

runs debugger pipeline 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
