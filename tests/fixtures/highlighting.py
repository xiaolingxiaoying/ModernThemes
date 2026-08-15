from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    name: str


def greet(user: User) -> str:
    message = f"Hello, {user.name}"
    return message
