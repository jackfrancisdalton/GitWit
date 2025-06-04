class Console:
    def print(self, *args, **kwargs):
        for arg in args:
            if hasattr(arg, "rows"):
                if getattr(arg, "title", None):
                    print(arg.title)
                for row in arg.rows:
                    print(" ".join(str(c) for c in row))
            else:
                print(arg)
