#     Copyright (C) 2023  Coretex LLC

#     This file is part of Coretex.ai

#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU Affero General Public License as
#     published by the Free Software Foundation, either version 3 of the
#     License, or (at your option) any later version.

#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.

#     You should have received a copy of the GNU Affero General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

from typing import Optional, Any, Callable, List, Tuple
from functools import wraps

import click

from ..settings import CLISettings


def base_group(
    name: Optional[str] = None,
    initFuncs: Optional[List[Tuple[Callable[[], None], List[str]]]] = None,
    **attrs: Any
) -> Callable[..., Any]:

    def decorator(group: Callable[..., Any]) -> Callable[..., Any]:

        @wraps(group)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            ctx = click.get_current_context()

            # Execute initialization functions if provided
            if initFuncs:
                for initFunc, excludedSubs in initFuncs:
                    if ctx.invoked_subcommand not in excludedSubs:
                        initFunc()

            # Call the main group function
            return group(*args, **kwargs)

        return click.group(name = name, **attrs)(wrapper)  # type: ignore

    return decorator


def base_command(
    name: Optional[str] = None,
    cls: Any = None,
    initFuncs: Optional[List[Callable[[], None]]] = None,
    **attrs: Any
) -> Callable[..., Any]:
    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        f = click.option("--verbose", is_flag = True, help = "Enables verbose mode")(f)

        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Handle the verbose option
            CLISettings.verbose = kwargs.pop("verbose", False)

            # Execute initialization functions if provided
            if initFuncs:
                for initFunc in initFuncs:
                    initFunc()

            # Call the main command function
            return f(*args, **kwargs)

        return click.command(name = name, cls=cls, **attrs)(wrapper)  # type: ignore

    return decorator
