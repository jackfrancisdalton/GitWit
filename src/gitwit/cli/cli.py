import typer

from gitwit.commands import repo_hot_zones, show_activity, who_is_the_expert, risky_commits, team_activity, latest_examples_of

app = typer.Typer()

app.command(name="ta")(team_activity.command)
app.command(name="sa")(show_activity.command)
app.command(name="wte")(who_is_the_expert.command)
app.command(name="rc")(risky_commits.command)
app.command(name="leo")(latest_examples_of.command)
app.command(name="hz")(repo_hot_zones.command)

if __name__ == "__main__":
    app()
