import typer

from src.commands import show_activity, who_is_the_expert

app = typer.Typer()

app.command(name="sa")(show_activity.command)
app.command(name="wte")(who_is_the_expert.command)

if __name__ == "__main__":
    app()
