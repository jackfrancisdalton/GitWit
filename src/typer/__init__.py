class Exit(Exception):
    def __init__(self, code: int = 0):
        self.code = code


class Option:
    def __init__(self, default=None, *args, **kwargs):
        self.default = default


class Argument(Option):
    pass


def run(func):
    func()


def Typer(*args, **kwargs):
    class _App:
        def __init__(self):
            pass

        def command(self, *a, **k):
            def decorator(f):
                return f

            return decorator

    return _App()


def secho(message, fg=None):
    print(message)
