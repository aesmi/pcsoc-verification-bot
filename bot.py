#!/usr/bin/env python3

"""Launches the Discord bot."""

import sys
import traceback
from logging import INFO
from discord import Intents
from discord.ext.commands import (
    Bot, CommandNotFound, DisabledCommand, BadArgument,
    TooManyArguments, ArgumentParsingError, MissingRequiredArgument
)

from iam.log import new_logger
from iam.config import BOT_TOKEN, PREFIX

LOG = None
INTENTS = Intents.all()

def main():
    global LOG
    new_logger("discord", f_level=INFO)
    LOG = new_logger(__name__)
    sys.excepthook = exception_handler

    BOT = Bot(command_prefix=PREFIX, intents=INTENTS)

    @BOT.event
    async def on_error(event, *args, **kwargs):
        """Handle exceptions raised by events/commands.

        If exception was raised during execution of event/command handler, 
        attempt to run its notify method if it has one. Otherwise, ignore but
        log error traceback.

        Args:
            event: Event that raised exception.
            args: Args supplied to event call.
            kwargs: Kwargs supplied to event call.
        """
        err = sys.exc_info()[1]
        LOG.error(f"Ignoring exception in {event}\n{traceback.format_exc()}")
    
    @BOT.event
    async def on_command_error(ctx, error):
        """Handle exceptions raised by commands.

        If exception is that command does not exist or is disabled, ignore.

        If exception is not handled here, will be raised and handled by 
        on_error.

        Args:
            ctx: Context object associated with event/command that raised.
            error: CommandError object generated by discord.py

        Raises:
            Any exception that is not handled by the above.
        """
        if isinstance(error, CommandNotFound) \
            or isinstance(error, DisabledCommand) \
            or isinstance(error, MissingRequiredArgument) \
            or isinstance(error, TooManyArguments) \
            or isinstance(error, ArgumentParsingError) \
            or isinstance(error, BadArgument):
            return

        if hasattr(error, "original"):
            err = error.original
            if hasattr(err, "notify") and callable(err.notify):
                await err.notify()
                return
            raise error.original
        
        if hasattr(err, "notify") and callable(err.notify):
            await err.notify()
            return

        await ctx.send("Oops! I encountered a problem. Please contact an "
            "admin.")
        
        raise error

    BOT.load_extension("iam.db")
    BOT.load_extension("iam.core")
    BOT.load_extension("iam.mail")
    BOT.load_extension("iam.verify")
    BOT.load_extension("iam.sign")
    BOT.load_extension("iam.newsletter")

    BOT.run(BOT_TOKEN)

def exception_handler(type, value, traceback):
    LOG.exception(f"Uncaught exception: {value}")

if __name__ == "__main__":
    main()
