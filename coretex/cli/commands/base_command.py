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

from typing import Optional, Any, Callable

import click


def base_command(name: Optional[str] = None, cls: Any = None, **attrs: Any) -> Any:
    def decorator(f: Callable[..., Any]) -> Any:
        f = click.option('--verbose', is_flag = True, help = "Enables berbose mode")(f)

        # Wrapper function to handle the verbose argument internally
        def wrapper(*args, **kwargs):
            verbose = kwargs.pop('verbose', False)
            if verbose:
                click.echo("Verbose mode is enabled.")
            else:
                click.echo("Verbose mode is disabled.")
            return f(*args, **kwargs)

        return click.command(name = name, cls = cls, **attrs)(f)
    return decorator
