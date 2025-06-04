class Progress:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

    def add_task(self, *args, **kwargs):
        return 0

    def advance(self, *args, **kwargs):
        pass

    def update(self, *args, **kwargs):
        pass


class TextColumn:
    def __init__(self, *args, **kwargs):
        pass


class BarColumn:
    def __init__(self, *args, **kwargs):
        pass


class TimeElapsedColumn:
    def __init__(self, *args, **kwargs):
        pass


class TimeRemainingColumn:
    def __init__(self, *args, **kwargs):
        pass
