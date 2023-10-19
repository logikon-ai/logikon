<!-- markdownlint-disable -->

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/exporters/networkx_exporter.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `logikon.debuggers.exporters.networkx_exporter`






---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/exporters/networkx_exporter.py#L13"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `NetworkXExporter`
NetworkXExporter Debugger 

This debugger exports an informal argmap as a networkx graph. 

It requires the following artifacts: 
- informal_argmap 


---

#### <kbd>property</kbd> logger

A :class:`logging.Logger` that can be used within the :meth:`run()` method. 

---

#### <kbd>property</kbd> product_type







---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/exporters/networkx_exporter.py#L26"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `get_product`

```python
get_product() → str
```





---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/exporters/networkx_exporter.py#L30"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `get_requirements`

```python
get_requirements() → list[str]
```





---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/exporters/networkx_exporter.py#L34"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `to_nx`

```python
to_nx(argument_map: 'InformalArgMap') → DiGraph
```

builds nx graph from nodes-links argument map 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
