from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from logikon.analysts.base import SYSTEM_MESSAGE_PROMPT
from logikon.backends.chat_models_with_grammar import LogitsModel

_TOP_LOGPROBS = 20


class MultipleChoiceResult(BaseModel):
    probs: dict[str, float] = Field(description="Label probabilities")
    label_max: str = Field(description="Most likely label")
    idx_max: int = Field(description="Most likely label index")
    choices: list = Field(default=[], description="List of choices")

    def probs_choices(self) -> dict[str, float]:
        if len(self.choices) != len(self.probs):
            msg = "Choices and probs must have the same length"
            raise ValueError(msg)
        return dict(zip(self.choices, self.probs.values()))

    def prob_choice(self, choice) -> float:
        if choice not in self.choices:
            msg = f"Choice {choice} not in choices {self.choices}"
            raise ValueError(msg)
        return self.probs_choices()[choice]


async def multiple_choice_query(
    question: str | list[BaseMessage],
    labels: list[str],
    model: LogitsModel,
    system_message: str = SYSTEM_MESSAGE_PROMPT,
    top_logprobs: int = _TOP_LOGPROBS,
) -> MultipleChoiceResult:
    """Query a multiple choice question

    Args:
        question (str | list[MessageLikeRepresentation]): Prompt question or list of messages
        labels (list[str]): List of permissible labels
        model (ChatOpenAI): Base model

    Raises:
        ValueError: Failed to extract logprobs from generation result

    Returns:
        MultipleChoiceResult: label probabilities and most likely label
    """

    # FIXME
    # check for:
    # - empty labels (disallowed)
    # - duplicate labels (disallowed)
    # - whitespace in labels (disallowed)
    # - multi-letter labels (disallowed)

    # if only one label, don't need to query
    if len(labels) == 1:
        return MultipleChoiceResult(
            probs={labels[0]: 1.0},
            label_max=labels[0],
            idx_max=0,
        )

    messages: list[BaseMessage] = [SystemMessage(content=system_message)]
    if isinstance(question, str):
        messages.append(HumanMessage(content=question))
    elif isinstance(question, list):
        messages.extend(question)
    else:
        msg = f"Question is of type {type(question)}. Expected str or list."
        raise ValueError(msg)

    probs = await model.get_labelprobs(messages=messages, labels=labels, top_logprobs=top_logprobs)
    label_max = sorted(probs.items(), key=lambda x: x[-1], reverse=True)[0][0]
    idx_max = labels.index(label_max)

    result = MultipleChoiceResult(
        probs=probs,
        label_max=label_max,
        idx_max=idx_max,
    )

    return result
