from typing import List, Any

import click
import inquirer


def checkIfGPUExists() -> bool:
    try:
        from py3nvml import py3nvml

        py3nvml.nvmlInit()
        py3nvml.nvmlShutdown()
        return True
    except:
        click.echo("This machine cannot utilize gpu image since it doesn't posses GPU.\bCPU image will be selected automatically")
        return False


def arrowPrompt(choices: List[Any]) -> Any:
    answers = inquirer.prompt([
        inquirer.List(
            "option",
            message = "Use arrow keys to select an option",
            choices = choices,
            carousel = True,
        )
    ])

    return answers["option"]


def makeExcludeHookGroup(callback):
    """ for any command that is not decorated, call the callback """

    hookAttrName = 'hook_' + callback.__name__

    class HookGroup(click.Group):
        """ group to hook context invoke to see if the callback is needed"""

        def invoke(self, ctx):
            """ group invoke which hooks context invoke """
            invoke = ctx.invoke

            def ctxInvoke(*args, **kwargs):
                """ monkey patched context invoke """
                subCmd = ctx.command.commands[ctx.invoked_subcommand]
                if not isinstance(subCmd, click.Group) and \
                        getattr(subCmd, hookAttrName, True):
                    # invoke the callback
                    callback()
                return invoke(*args, **kwargs)

            ctx.invoke = ctxInvoke

            return super(HookGroup, self).invoke(ctx)

        def group(self, *args, **kwargs):
            """ new group decorator to make sure sub groups are also hooked """
            if 'cls' not in kwargs:
                kwargs['cls'] = type(self)
            return super(HookGroup, self).group(*args, **kwargs)

    def decorator(func = None):
        if func is None:
            # if called other than as decorator, return group class
            return HookGroup

        setattr(func, hookAttrName, False)

    return decorator
