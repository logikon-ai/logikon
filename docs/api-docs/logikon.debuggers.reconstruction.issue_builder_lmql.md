<!-- markdownlint-disable -->

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/reconstruction/issue_builder_lmql.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `logikon.debuggers.reconstruction.issue_builder_lmql`




**Global Variables**
---------------
- **N_DRAFTS**
- **LABELS**
- **QUESTIONS_EVAL**

---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/reconstruction/issue_builder_lmql.py#L24"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `strip_issue_tag`

```python
strip_issue_tag(text: 'str') → str
```

Strip issue tag from text. 


---

<a href="https://github.com/logikon-ai/logikon/blob/main/.virtualenvs/logikon/lib/python3.11/site-packages/lmql/api/queries.py#L29"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `key_issue`

```python
key_issue(prompt, completion)
```

 sample(n=3, temperature=.4)  "### System 

"  "You are a helpful argumentation analysis assistant. 

"  "### User 

"  "Assignment: Analyse and reconstruct a text's argumentation. 

"  "The argumentative analysis proceeds in three steps: 

"  "1. Identify central issue "  "2. Identify key claims discussed "  "3. Set up a pros & cons list 

"  "Before we start, let's study the text to-be-analysed carefully. 

"  "<TEXT> "  "{prompt}{completion} "  "</TEXT> 

"  "## Step 1 

"  "State the central issue / decision problem discussed in the TEXT in a few words. "  "Be as brief and concise as possible. Think of your answer as the headline of an argument or debate. "  "Enclose your answer in "<ISSUE>" / "</ISSUE>" tags. 

"  "### Assistant 

"  "<ISSUE> "  "[@strip_issue_tag ISSUE]"  where  STOPS_AT(ISSUE, "</ISSUE>")  




---

<a href="https://github.com/logikon-ai/logikon/blob/main/.virtualenvs/logikon/lib/python3.11/site-packages/lmql/api/queries.py#L57"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `rate_issue_drafts`

```python
rate_issue_drafts(alternatives, questions, prompt, completion)
```

lmql  argmax  labels = [alternative.get('label') for alternative in alternatives]  "### System 

"  "You are a helpful argumentation analysis assistant. 

"  "### User 

"  "Assignment: Rate different summarizations of a text's key issue. 

"  "Before we start, let's study the text to-be-analysed carefully. 

"  "<TEXT> "  "{prompt}{completion} "  "</TEXT> 

"  "Consider the following alternatives, which attempt to summarize the central issue / basic decision discussed in the TEXT in a single sentence. 

"  "<ALTERNATIVES> "  for alternative in alternatives:  "({alternative.get('label')}) "{alternative.get('text')}" "  "</ALTERNATIVES> 

"  "Compare and evaluate the different alternatives according to {len(alternatives)} relevant criteria which are put as questions. (At this point, just answer each question with {'/'.join(labels)}; you'll be asked to explain your answers later.) "  "Conclude with an aggregate assessment of the alternatives. 

"  "### Assistant 

"  for question in questions:  "{question}  "  "Answer: ([ANSWER]) 

" where ANSWER in set(labels)  "So, all in all and given the above assessments, the best summarization of the text's key issue is which alternative? "  "Answer: ([FINAL_ANSWER])" where FINAL_ANSWER in set(labels)  




---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/reconstruction/issue_builder_lmql.py#L86"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>class</kbd> `IssueBuilderLMQL`
IssueBuilderLMQL 

This LMQLDebugger is responsible for summarizing the issue discussed in a text. 


---

#### <kbd>property</kbd> logger

A :class:`logging.Logger` that can be used within the :meth:`run()` method. 

---

#### <kbd>property</kbd> product_type







---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/reconstruction/issue_builder_lmql.py#L99"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `get_description`

```python
get_description() → str
```





---

<a href="https://github.com/logikon-ai/logikon/blob/main/src/logikon/debuggers/reconstruction/issue_builder_lmql.py#L95"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>method</kbd> `get_product`

```python
get_product() → str
```








---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
