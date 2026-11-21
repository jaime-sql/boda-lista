"""Guest-question scoring hook.

TODO: guest_questions are out of scope for this harness. Do not fold them
into the RSVP or song comparison. When a later change wires the task in,
score each answer by exact string match. The gold answer for an unknown
question is exactly UNKNOWN_ANSWER.
"""

from __future__ import annotations

UNKNOWN_ANSWER = "No tengo esa información, pregúntale a los novios"


def exact_match(prediction: str, gold: str) -> bool:
    """Return whether a guest-question answer matches its gold string."""
    return prediction.strip() == gold.strip()


def is_unknown_answer(gold: str) -> bool:
    return gold.strip() == UNKNOWN_ANSWER
