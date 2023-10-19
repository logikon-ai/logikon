<!-- markdownlint-disable -->

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/base.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `logikon.debuggers.base`




**Global Variables**
---------------
- **ARTIFACT**
- **SCORE**


---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/base.py#L13"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `AbstractDebugger`
Base debugger class with default __call__ implementation. 

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/base.py#L18"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `__init__`

```python
__init__(debug_config: DebugConfig)
```






---

#### <kbd>property</kbd> logger

A :class:`logging.Logger` that can be used within the :meth:`run()` method. 

---

#### <kbd>property</kbd> product_type







---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/base.py#L33"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `get_requirements`

```python
get_requirements() → List[str]
```

Default implementation: no requirements. 


---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/base.py#L46"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `AbstractArtifactDebugger`
Base debugger class for creating artifacts. 

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/base.py#L18"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `__init__`

```python
__init__(debug_config: DebugConfig)
```






---

#### <kbd>property</kbd> logger

A :class:`logging.Logger` that can be used within the :meth:`run()` method. 

---

#### <kbd>property</kbd> product_type







---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/base.py#L33"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `get_requirements`

```python
get_requirements() → List[str]
```

Default implementation: no requirements. 


---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/base.py#L56"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `AbstractScoreDebugger`
Base debugger class for creating scroes. 

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/base.py#L18"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `__init__`

```python
__init__(debug_config: DebugConfig)
```






---

#### <kbd>property</kbd> logger

A :class:`logging.Logger` that can be used within the :meth:`run()` method. 

---

#### <kbd>property</kbd> product_type







---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/base.py#L33"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `get_requirements`

```python
get_requirements() → List[str]
```

Default implementation: no requirements. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
