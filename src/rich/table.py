class Table:
    def __init__(self, title: str | None = None, *args, **kwargs):
        self.title = title
        self.rows = []

    def add_column(self, *args, **kwargs):
        pass

    def add_row(self, *args, **kwargs):
        self.rows.append(args)
