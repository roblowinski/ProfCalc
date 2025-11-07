DATA management and policy
=========================

This project keeps generated outputs and large binary artifacts out of the main source tree. The purpose of this document is to make the expected workflow explicit so contributors avoid committing large files and sensitive data.

1. Where to put data
   - Short-lived generated outputs and export files (CSV summaries, TXT reports, shapefiles, etc.) belong in the top-level `data/` directory. This directory is excluded from Git by default.
   - Small metadata or manifest files that are required for tests or examples may stay in the repository (for example `data/README.md` or `data/sample-manifest.json`).

2. Why keep data out of Git
   - Large files bloat repository history and make cloning slow.
   - Binary formats (shapefiles, archives) are not delta-friendly and should be stored with Git LFS or external storage.

3. Recommended workflow
   - Do not commit generated outputs. Use `git status` and `git add -p` to review staged changes before committing.
   - If a large file must be versioned, use Git LFS:
     - Install: `git lfs install`
     - Track patterns:
       git lfs track "*.shp" "*.dbf" "*.shx" "*.zip"
     - Commit the generated `.gitattributes` and push to the remote.

4. If large files were accidentally committed
   - Create a backup bundle first: `git bundle create ../profcalc-backup.bundle --all`
   - Use `git filter-repo` or BFG to remove the files from history, then `git gc --prune=now --aggressive` and force-push. Coordinate with collaborators when you rewrite history.

5. Backups and snapshots
   - Periodic backups are recommended for active development. Two low-risk options:
     - Create a bundle: `git bundle create "C:/Backups/Profile_Analysis_$(Get-Date -Format yyyyMMdd_HHmmss).bundle" --all`
     - Create a zipped snapshot of HEAD: `git archive --format=zip --output="C:/Backups/Profile_Analysis_$(Get-Date -Format yyyyMMdd_HHmmss).zip" HEAD`

6. Local data directory (this repo)
   - The `data/` folder at the repository root is the canonical place for exported and cached outputs. It is listed in `.gitignore` to avoid accidental commits. If you need to keep small example files under version control, add them under `data/examples/` and commit only those.

7. Regenerating moved files
   - Recent tool runs produced `bounds_both_*` output files. These were moved to `data/` to keep the repo root clean. To regenerate them, run the corresponding CLI tool (for example `src/profcalc/cli/tools/bounds.py` or the top-level script that invokes it) with the same input and options used previously.

8. Contact
   - If you are unsure whether a file should be tracked, raise an issue or open a PR and tag maintainers. We can advise whether to add a placeholder file, use LFS, or keep the file out of git entirely.

Appendix: quick commands (PowerShell)

# ```powershell

# Check status

git status --porcelain=2 --branch

# Interactively stage changes

git add -p

# Move tracked generated files into data/ and stage the move

mkdir data; git mv bounds_both_* data/

# Remove a file from the index but keep it locally

git rm --cached path/to/largefile

# Initialize and track with Git LFS

git lfs install
git lfs track "*.shp" "*.dbf" "*.shx" "*.zip"
git add .gitattributes
git commit -m "Track large files with Git LFS"

```
