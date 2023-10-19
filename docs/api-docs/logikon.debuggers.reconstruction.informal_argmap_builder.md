<!-- markdownlint-disable -->

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/reconstruction/informal_argmap_builder.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `logikon.debuggers.reconstruction.informal_argmap_builder`






---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/reconstruction/informal_argmap_builder.py#L23"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `PromptRegistry`
A registry of prompts to be used in building an informal argmap. 

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/reconstruction/informal_argmap_builder.py#L28"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `__init__`

```python
__init__()
```








---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/reconstruction/informal_argmap_builder.py#L31"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `register`

```python
register(name, prompt: 'PromptTemplate')
```

Register a prompt to the registry. 


---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/reconstruction/informal_argmap_builder.py#L38"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `PromptRegistryFactory`
Creates Prompt Registries 




---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/reconstruction/informal_argmap_builder.py#L43"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `create`

```python
create() → PromptRegistry
```






---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/reconstruction/informal_argmap_builder.py#L372"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `InformalArgMapChain`




<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/reconstruction/informal_argmap_builder.py#L382"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `__init__`

```python
__init__(**kwargs)
```






---

#### <kbd>property</kbd> InputType

The type of input this runnable accepts specified as a type annotation. 

---

#### <kbd>property</kbd> OutputType

The type of output this runnable produces specified as a type annotation. 

---

#### <kbd>property</kbd> config_specs

List configurable fields for this runnable. 

---

#### <kbd>property</kbd> input_keys





---

#### <kbd>property</kbd> input_schema





---

#### <kbd>property</kbd> lc_attributes

List of attribute names that should be included in the serialized kwargs. 

These attributes must be accepted by the constructor. 

---

#### <kbd>property</kbd> lc_secrets

A map of constructor argument names to secret ids. 

For example,  {"openai_api_key": "OPENAI_API_KEY"} 

---

#### <kbd>property</kbd> output_keys





---

#### <kbd>property</kbd> output_schema







---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/reconstruction/informal_argmap_builder.py#L395"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `parse_list`

```python
parse_list(inputs: 'dict[str, str]') → dict[str, list[str]]
```






---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/reconstruction/informal_argmap_builder.py#L744"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `InformalArgMapBuilder`
InformalArgMap Debugger 

This debugger is responsible for extracting informal argument maps from the deliberation in the completion. It uses plain and non-technical successive LLM calls to gradually sum,m,arize reasons and build an argmap. 

It requires the following artifacts: 
- claims 


---

#### <kbd>property</kbd> logger

A :class:`logging.Logger` that can be used within the :meth:`run()` method. 

---

#### <kbd>property</kbd> product_type







---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/reconstruction/informal_argmap_builder.py#L767"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `get_description`

```python
get_description() → str
```





---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/reconstruction/informal_argmap_builder.py#L759"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `get_product`

```python
get_product() → str
```





---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/reconstruction/informal_argmap_builder.py#L763"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `get_requirements`

```python
get_requirements() → list[str]
```








---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
