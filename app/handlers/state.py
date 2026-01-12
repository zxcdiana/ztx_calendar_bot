from __future__ import annotations

from typing import cast

from aiogram.fsm.state import StatesGroup, State


class StateFactory(State):
    def __getattr__(self, state_name: str) -> StateFactory:
        assert self._state not in (None, "*")
        state = StateFactory(state=state_name, group_name=self._group_name)

        if self._group is None:
            self._group = cast(
                type[StatesGroup], type(self._state.capitalize(), (StatesGroup,), {})
            )

        state._group = self._group
        self._group.__states__ = (*self._group.__states__, state)
        self._group.__state_names__ = (*self._group.__state_names__, state_name)
        self._group.__all_states__ = (*self._group.__all_states__, state)
        self._group.__all_states_names__ = (
            *self._group.__all_states_names__,
            state_name,
        )

        return state


input_state = StateFactory("input_value")
