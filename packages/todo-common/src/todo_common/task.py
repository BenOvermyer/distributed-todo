from dataclasses import dataclass

"""
This module defines the Task data structure.

We are not using class methods for stateful operations because
we want to decouple data representation and datastore operations.
This makes it easier to test and debug.
"""


@dataclass  # Why dataclass? Because it's my closest approximation to Typescript types.
class Task:
    id: int
    username: str
    content: str
    is_completed: bool
    is_deleted: bool
    due_date: str | None
    created_at: str
    updated_at: str
