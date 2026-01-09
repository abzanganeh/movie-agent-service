# Version Management Scripts

## push_with_version.sh

Automatically bumps the version, commits, pushes, and creates a release tag.

### Usage

```bash
# From the project root
./scripts/push_with_version.sh [commit message]

# Examples:
./scripts/push_with_version.sh
./scripts/push_with_version.sh "Fix bug in movie statistics"
./scripts/push_with_version.sh "Add new feature"
```

### What it does

1. Reads current version from `pyproject.toml`
2. Bumps the patch version (e.g., 0.1.3 → 0.1.4)
3. Updates `pyproject.toml` with new version
4. Stages all changes
5. Commits with message (default: "Bump version to X.Y.Z")
6. Pushes to `origin/main`
7. Creates annotated tag `vX.Y.Z`
8. Pushes tag to remote

### Git Alias (Optional)

Add this to your `~/.gitconfig` for easier access:

```bash
git config --global alias.pushv '!bash -c "cd \"$(git rev-parse --show-toplevel)\" && ./scripts/push_with_version.sh \"$@\"" --'
```

Then you can use:
```bash
git pushv "Your commit message"
```

