"""Store used for holding state and globals that don't change."""
from typing import Any

from rx.subject import BehaviorSubject  # type: ignore


class Store(BehaviorSubject):
    """Simple immutable store."""

    def get(self, key: str) -> Any:
        """Short method to get values from the store."""
        return self.value[key]

    def update(self, key: str, value: Any) -> None:
        """Immutable way to update the store."""
        if key in self.value:
            self.on_next({**self.value, **dict({key: value})})


store = Store({
    'active_bank': 0,
    'mappings': [],
    'inports': None,
    'outports': None,
})
