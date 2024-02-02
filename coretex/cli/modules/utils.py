from typing import List, Any, Optional, Callable
from functools import wraps

from py3nvml import py3nvml

import click


def isGPUAvailable() -> bool:
    try:
        py3nvml.nvmlInit()
        py3nvml.nvmlShutdown()
        return True
    except:
        return False


def onBeforeCommandExecute(fun: Callable[..., Any], excludeOptions: Optional[List[str]] = None) -> Any:
    if excludeOptions is None:
        excludeOptions = []

    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for key, value in click.get_current_context().params.items():
                if key in excludeOptions and value:
                    return f(*args, **kwargs)

            fun()
            return f(*args, **kwargs)
        return wrapper
    return decorator


def CatchAllExceptions(cls, handler):

    class Cls(cls):

        _original_args = None

        def make_context(self, info_name, args, parent=None, **extra):

            # grab the original command line arguments
            self._original_args = ' '.join(args)

            try:
                return super(Cls, self).make_context(
                    info_name, args, parent=parent, **extra)
            except Exception as exc:
                # call the handler
                handler(self, info_name, exc)

                # let the user see the original error
                raise

        def invoke(self, ctx):
            try:
                return super(Cls, self).invoke(ctx)
            except Exception as exc:
                # call the handler
                handler(self, ctx.info_name, exc)

                # let the user see the original error
                raise

    return Cls


def handle_exception(cmd, info_name, exc):
    # send error info to rollbar, etc, here
    click.echo(':: Command line: {} {}'.format(info_name, cmd._original_args))
    click.echo(':: Raised error: {}'.format(exc))