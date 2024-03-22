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

from typing import Any

import logging

import click

from .ui import errorEcho


class ClickExceptionInterceptor(click.Group):

    def invoke(self, ctx: click.Context) -> Any:
        try:
            return super().invoke(ctx)
        except BaseException as exc:
            if isinstance(exc, KeyboardInterrupt):
                raise

            if isinstance(exc, click.exceptions.Exit) and exc.exit_code == 0:
                raise

            self.handleException(ctx, exc)

    def handleException(self, ctx: click.Context, exc: BaseException) -> None:
        click.echo(click.style(str(exc), fg = "red"))
        logging.getLogger("cli").debug(exc, exc_info = exc)
