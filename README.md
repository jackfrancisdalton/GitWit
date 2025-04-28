# GitWit

<!-- TODO info -->


## Target Use Cases

### Style Summary

### File Audit 

### Risk Assessment
Assess risky commits as a way of determining where something may have gone wrong in your application

```
gitwit risky-commits
```

```
⚠️  2 unreviewed risky commits:
- jack_smith | "Quick refactor session timeout" | server/auth/session.py
- mark_white | "Temp fix DB reconnect" | server/db/connection.js

⚠️  1 large risky commits:
- jane_doe | "Quick refactor session timeout" | 10 files, 800 lines

```


### File History

```
gitwit history --file controllers/userController.js
```

```
Recent Changes:
- emily_zhou | 2025-04-25 | "Add user 2FA"
- jack_smith | 2025-04-20 | "Refactor login validation"
```

### Directory Activity

```
gitwit who-touched --path server/payment/
```

```
Top Contributors:
- jack_smith (15 commits)
- sarah_lee (9 commits)
- emily_zhou (5 commits)
```

### Repo Activity

```
gitwit activity --since 2025-04-01 --until 2025-04-25
```

```
Activity Report:
- 123 commits
- 7 contributors
- Top contributors: jack_smith (25 commits), emily_zhou (18 commits)
```


### Weekly Summary
```
gitwit weekly-summary
```

```
Week ending 2025-04-27:
- 47 commits
- 6 contributors
- 2 features merged
- 1 bugfix hotpatch
```


### PR Overview
```
gitwit pr-status
```

```
Open PRs:
- #242 "Refactor signup API" by sarah_lee (2d old)
- #243 "Fix billing retries" by raj_kumar (1d old)
- #244 "Cleanup auth tokens" by emily_zhou (new)
```


### Who knows the file

```
gitwit ownership --file server/cache/cache.py
```

```
Ownership Summary:
- 42% jack_smith
- 33% emily_zhou
- 25% others
```

### Grep Commits

```
gitwit grep-commits --keywords "password,token,secret"
```

```
Sensitive Commits:
- jack_smith | "Store API token securely"   | 2025-05-01
- emily_zhou | "Rotate password encryption" | 2025-05-01
```


### First Time a developer is creating a file type
```
gitwit first-time --author emily_zhou
```

```
First-time Created Files:

- services/notificationService.js
- models/notificationModel.py
- docs/notifications.md
```
