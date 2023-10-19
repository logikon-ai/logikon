<!-- markdownlint-disable -->

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/interface.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `logikon.debuggers.interface`






---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/interface.py#L7"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `Debugger`
Abstract base class for all debuggers. 

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/interface.py#L10"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `__init__`

```python
__init__(debug_config)
```






---

#### <kbd>property</kbd> product_type







---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/interface.py#L23"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `get_product`

```python
get_product() → str
```

Get config keyword of artifact / metric produced by debugger. 

---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/interface.py#L29"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `get_requirements`

```python
get_requirements() → List[str]
```

Get config keywords of metrics / artifacts that are required for the debugger. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
