import typer

app = typer.Typer()

@app.command()
def hello():
    typer.echo("Hello GitWit user!")

if __name__ == "__main__":
    app()   # ✅ run app if executed directly