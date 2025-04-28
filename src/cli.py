import typer

from commands import show_activity

app = typer.Typer()
app.command()(show_activity.command)

if __name__ == "__main__":
    app()
#     