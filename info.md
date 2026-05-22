PS C:\Users\douzi457\.qclaw\workspace\intel-daily-astro> git reset --soft HEAD~1
PS C:\Users\douzi457\.qclaw\workspace\intel-daily-astro> git restore --staged .github/
PS C:\Users\douzi457\.qclaw\workspace\intel-daily-astro> git status
On branch main
Your branch is ahead of 'origin/main' by 1 commit.
  (use "git push" to publish your local commits)

Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
        modified:   astro.config.mjs
        new file:   info.md
        modified:   src/layouts/BaseLayout.astro
        modified:   src/pages/archive.astro
        modified:   src/pages/day/[date].astro
        new file:   src/pages/en/archive.astro
        new file:   src/pages/en/day/[date].astro
        new file:   src/pages/en/index.astro
        new file:   src/pages/en/stats.astro
        modified:   src/pages/index.astro
        modified:   src/pages/stats.astro
        modified:   src/scripts/collect_all.py
        modified:   src/scripts/db/db.py
        modified:   src/scripts/db/intel.db
        modified:   src/scripts/dump_astro_json.py
        modified:   src/utils/data.ts

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
        modified:   info.md

PS C:\Users\douzi457\.qclaw\workspace\intel-daily-astro> git commit -m "feat: 2026 global dual-language version (excluding workflow)"
[main d9fda1c] feat: 2026 global dual-language version (excluding workflow)
 16 files changed, 887 insertions(+), 243 deletions(-)
 create mode 100644 info.md
 create mode 100644 src/pages/en/archive.astro
 create mode 100644 src/pages/en/day/[date].astro
 create mode 100644 src/pages/en/index.astro
 create mode 100644 src/pages/en/stats.astro
PS C:\Users\douzi457\.qclaw\workspace\intel-daily-astro> git push
Enumerating objects: 239, done.
Counting objects: 100% (239/239), done.
Delta compression using up to 12 threads
Compressing objects: 100% (209/209), done.
Writing objects: 100% (226/226), 1.01 MiB | 1.34 MiB/s, done.
Total 226 (delta 36), reused 0 (delta 0), pack-reused 0 (from 0)
remote: Resolving deltas: 100% (36/36), completed with 7 local objects.
To https://github.com/douzi457/intel-daily-astro.git
 ! [remote rejected] main -> main (refusing to allow a Personal Access Token to create or update workflow `.github/workflows/collect.yml` without `workflow` scope)
error: failed to push some refs to 'https://github.com/douzi457/intel-daily-astro.git'
PS C:\Users\douzi457\.qclaw\workspace\intel-daily-astro>