from typing import Any

import click

from .user_interface import errorEcho


class ClickExceptionInterceptor(click.Group):
    def invoke(self, ctx: click.Context) -> Any:
        try:
            return super().invoke(ctx)
        except BaseException as exc:
            self.handleException(ctx, exc)

    def handleException(self, ctx: click.Context, exc: BaseException) -> None:
        # Custom exception handling logic here
        errorEcho(f"An error occurred: {exc}")
