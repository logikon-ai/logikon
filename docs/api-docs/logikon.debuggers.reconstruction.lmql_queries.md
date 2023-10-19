<!-- markdownlint-disable -->

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/reconstruction/lmql_queries.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `logikon.debuggers.reconstruction.lmql_queries`
LMQL Queries shared by Logikon Reconstruction Debuggers 

**Global Variables**
---------------
- **PRO**
- **CON**

---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/reconstruction/lmql_queries.py#L15"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `system_prompt`

```python
system_prompt() → str
```

Returns the system prompt used in all lmql queries 


---

<a href="https://github.com/logikon-ai/logikon/blob/main/.virtualenvs/logikon/lib/python3.11/site-packages/lmql/api/queries.py#L26"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `supports_q`

```python
supports_q(argument_data: 'dict', claim_data: 'dict')
```

lmql argmax  argument = Claim(**argument_data)  claim = Claim(**claim_data)  """  {system_prompt()} 

 ### User 

 Assignment: Identify if an argument supports a claim. 

 Read the following argument carefully. 

 <argument>  {argument.label}: {argument.text}  </argument> 

 Does this argument provide evidence for the following claim? 

 <claim>  [[{claim.label}]]: {claim.text}  </claim> 

 (A) Yes, the argument supports the claim.  (B) No, the argument does not support the claim. 

 Just answer with "(A)" or "(B)". No explanations or comments. You'll be asked to justify your answer later on. 

 ### Assistant 

 Answer: ([LABEL]""" distribution  LABEL in ["A", "B"] 


---

<a href="https://github.com/logikon-ai/logikon/blob/main/.virtualenvs/logikon/lib/python3.11/site-packages/lmql/api/queries.py#L64"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `attacks_q`

```python
attacks_q(argument_data: 'dict', claim_data: 'dict')
```

lmql argmax  argument = Claim(**argument_data)  claim = Claim(**claim_data)  """  {system_prompt()} 

 ### User 

 Assignment: Identify if an argument speaks against a claim. 

 Read the following argument carefully. 

 <argument>  {argument.label}: {argument.text}  </argument> 

 Does this argument provide evidence against the following claim? 

 <claim>  [[{claim.label}]]: {claim.text}  </claim> 

 (A) Yes, the argument disconfirms the claim.  (B) No, the argument does not disconfirm the claim. 

 Just answer with "(A)" or "(B)". No explanations or comments. You'll be asked to justify your answer later on. 

 ### Assistant 

 Answer: ([LABEL]""" distribution  LABEL in ["A", "B"] 


---

<a href="https://github.com/logikon-ai/logikon/blob/main/.virtualenvs/logikon/lib/python3.11/site-packages/lmql/api/queries.py#L102"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `most_confirmed`

```python
most_confirmed(argument_data: 'dict', claims_data: 'list')
```

lmql  argmax  argument = Claim(**argument_data)  claims = [Claim(**claim_data) for claim_data in claims_data]  assert len(claims) <= 10  labels = [l for l in "ABCDEFGHIJ"][:len(claims)]  """  {system_prompt()} 

 ### User 

 Assignment: Identify the claim which is most strongly supported by an argument. 

 Read the following argument carefully. 

 <argument>  {argument.label}: {argument.text}  </argument> 

 I'll show you a list of claims. Please identify the claim which is most strongly supported by the argument. 

 The argument speaks in favor of: 

 """  for label, claim in zip(labels, claims):  "({label}) "{claim.label}: {claim.text}" "  """  Just answer with ({'/'.join(labels)}). You'll be asked to justify your answer later on. 

 ### Assistant 

 Answer: ([LABEL]"""  distribution  LABEL in labels  




---

<a href="https://github.com/logikon-ai/logikon/blob/main/.virtualenvs/logikon/lib/python3.11/site-packages/lmql/api/queries.py#L140"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `most_disconfirmed`

```python
most_disconfirmed(argument_data: 'dict', claims_data: 'list')
```

lmql  argmax  argument = Claim(**argument_data)  claims = [Claim(**claim_data) for claim_data in claims_data]  assert len(claims) <= 10  labels = [l for l in "ABCDEFGHIJ"][:len(claims)]  """  {system_prompt()} 

 ### User 

 Assignment: Identify the claim which is supported by an argument. 

 Read the following argument carefully. 

 <argument>  {argument.label}: {argument.text}  </argument> 

 I'll show you a list of claims. Please identify the claim which is supported by the argument. 

 Note that all these claims are negations. 

 The argument speaks in favor of: 

 """  for label, claim in zip(labels, claims):  text = claim.text  text = text[0].lower() + text[1:]  "({label}) "It is not the case that {text}" "  """  Just answer with ({'/'.join(labels)}). You'll be asked to justify your answer later on. 

 ### Assistant 

 Answer: ([LABEL]"""  distribution  LABEL in labels  




---

<a href="https://github.com/logikon-ai/logikon/blob/main/.virtualenvs/logikon/lib/python3.11/site-packages/lmql/api/queries.py#L182"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `valence`

```python
valence(argument_data: 'dict', claim_data: 'dict')
```

lmql argmax  argument = Claim(**argument_data)  claim = Claim(**claim_data)  """  {system_prompt()} 

 ### User 

 Assignment: Identify whether an argument speaks for or against a claim. 

 Read the following argument and claim carefully. 

 <argument>  {argument.label}: {argument.text}  </argument>  <claim>  {claim.label}: {claim.text}  </claim> 

 Does the argument a pro reason for, or a con reason against against the claim? 

 Here is a simple test: Which of the following is more plausible: 

 (A) "{claim.text} BECAUSE {argument.text}"  (B) "{claim.text} ALTHOUGH {argument.text}" 

 In case (A), the argument speaks for (supports) the claim. In case (B) the argument speaks against (disconfirms) the claim. 

 So, given your thorough assessment, which is correct: 

 (A) The argument speaks for the claim.  (B) The argument speaks against the claim. 

 Just answer with (A/B). You'll be asked to justify your answer later on. 

 ### Assistant 

 Answer: ([LABEL]""" distribution  LABEL in ["A", "B"] 


---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/reconstruction/lmql_queries.py#L228"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `get_distribution`

```python
get_distribution(result: 'LMQLResult') → List[Tuple[str, float]]
```

Extracts the distribution from an LMQL result 



**Args:**
 
 - <b>`result`</b> (lmql.LMQLResult):  LMQL Result object obtained from distribution query 



**Raises:**
 
 - <b>`ValueError`</b>:  No distribution found in LMQL result 



**Returns:**
 
 - <b>`List[Tuple[str,float]]`</b>:  Discrete distribution over labels (label, probability) 


---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/reconstruction/lmql_queries.py#L246"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `label_to_idx`

```python
label_to_idx(label)
```






---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/reconstruction/lmql_queries.py#L254"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `label_to_claim`

```python
label_to_claim(label, claims)
```






---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/reconstruction/lmql_queries.py#L261"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `label_to_valence`

```python
label_to_valence(label)
```








---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
