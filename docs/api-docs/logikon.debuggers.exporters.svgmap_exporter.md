<!-- markdownlint-disable -->

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/exporters/svgmap_exporter.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `logikon.debuggers.exporters.svgmap_exporter`






---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/exporters/svgmap_exporter.py#L17"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `SVGMapExporter`
SVGMapExporter Debugger 

This debugger exports an a networkx graph as svg via graphviz. 

It requires the following artifacts: 
- networkx_graph 

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/exporters/svgmap_exporter.py#L34"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `__init__`

```python
__init__(debug_config: 'DebugConfig')
```






---

#### <kbd>property</kbd> logger

A :class:`logging.Logger` that can be used within the :meth:`run()` method. 

---

#### <kbd>property</kbd> product_type







---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/exporters/svgmap_exporter.py#L47"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `get_product`

```python
get_product() → str
```





---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/exporters/svgmap_exporter.py#L51"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `get_requirements`

```python
get_requirements() → list[str]
```








---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
