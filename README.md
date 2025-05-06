# GitWit
GitWit is a CLI tool that extracts, analyzes, and summarizes Git activity to help both engineering leaders and individual developers make better, faster decisions.

## Problem Statment
This project aims to synergise two statements:

1. In fast-moving software teams git history(s) holds a wealth of insight into team dynamics, code health, and development velocity. 

2.  Engineering leads need visibility into contributions, review cycles, etc.. and new developers need to ramp up quickly by understanding who's working on what, which parts of the codebase are active, etc...

By analysing the data available in *1* and exposing it in an appealing way, we can improve the ways all of the needs in *2* are addressed  


# Project Overview
GitWit exlusivly uses project directories, files and git history to generate its anlysis and can run on any enviornment that supports python 3


It offers the following commands:

| Command | CLI name | Arguments | Summary |
| ------- | -------- | ----------| --------|
|Who is the expert| wte | `--path` `--num-experts` | Provides an output for a target directory or file on who owns the most lines, who has touched it last, and what they did |
| Show Activity | `sa` | `--since` `--until` | Provides an overview of activity during a given period such as the largest commits, the most active developers, etc...

<!-- TODO all commands -->


## Future Development


# TODO: 
- clean up arguments to be standardised (likely move to a days model instead of a from-to model)
- clean up option vs argument approach for commands to simplify UX
- clean up test coverage/names
- add loading bars to all commands
- add gitwork flow unit testing