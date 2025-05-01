import typer

from .commands import show_activity, who_is_the_expert, risky_commits

app = typer.Typer()

app.command(name="sa")(show_activity.command)
app.command(name="wte")(who_is_the_expert.command)
app.command(name="rc")(risky_commits.command)

if __name__ == "__main__":
    app()
