# DeepEval bridge example

Wrap a DeepEval metric as a judge-tier assertion:

```python
from deepeval_bridge import wrap_deepeval_metric

# from deepeval.metrics import AnswerRelevancyMetric
# metric = AnswerRelevancyMetric()
# judge = wrap_deepeval_metric(metric.measure, name="answer_relevancy")
```

Install optional deps: `pip install invarianteval[deepeval]`

Judge results are warn-only unless you wire them into suite YAML explicitly.
