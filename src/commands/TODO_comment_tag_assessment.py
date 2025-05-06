# Complete an implementation for this file:

# Purpose: identify the oldest comment tags in the codease to review if they are still relevant

# Output aim:

# Oldest Unresolved Comment Tags
# | Tag     | File Path                   | Line | Author   | Date Added  | Excerpt                          |
# |---------|-----------------------------|------|----------|-------------|----------------------------------|
# | TODO    | /services/auth/login.js     | 87   | Alice    | 2023-11-12  | "TODO: Migrate to new token lib" |
# | FIXME   | /utils/timezone.js          | 120  | Charlie  | 2024-01-03  | "FIXME: Wrong offset on DST"     |
# | BUG     | /frontend/components/Menu.tsx | 22  | Bob      | 2023-09-18  | "BUG: Menu doesn’t collapse"     |
# | TEMP    | /api/user/data.ts           | 203  | Dana     | 2024-02-11  | "TEMP: Hardcoded ID for testing" |


# Tag Counts by Type:
# - TODO: 15
# - FIXME: 9
# - BUG: 3
# - TEMP: 5

# 📂 Top Directories with Legacy Comments:
# - /services/auth — 4 comment tags > 90 days old
# - /frontend      — 3 comments tags > 6 months old
