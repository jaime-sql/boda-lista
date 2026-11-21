"""Map labeled data tasks to app feature keys.

Rows keep their task values. Harness outputs use the feature names.
"""

TASK_TO_FEATURE = {
    "rsvp": "rsvp",
    "song": "songs",
    "guest_question": "qa",
}


def feature_for(task: str) -> str:
    return TASK_TO_FEATURE[task]
