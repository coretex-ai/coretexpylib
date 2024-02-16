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
        errorEcho(str(exc))
        logging.getLogger("cli").debug(exc, exc_info = exc)
