import asyncio, functools

async def run_blocking_io(func, *args, **kwargs):
            def acquire_loop(running: bool = False) -> asyncio.AbstractEventLoop:
                try:
                    loop = asyncio._get_running_loop()

                except Exception:  # an error might occur actually
                    loop = None

                if running and loop is not None:
                    return loop

                else:
                    try:
                        loop = asyncio.get_event_loop()

                        if loop.is_running() and not running:
                            # loop is running while we have to get the non-running one,
                            # let us raise an error to go into <except> clause.
                            raise ValueError("Current event loop is already running.")

                    except Exception:
                        loop = asyncio.new_event_loop()

                return loop
            loop = acquire_loop(running=True)

            asyncio.set_event_loop(loop)

            return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))