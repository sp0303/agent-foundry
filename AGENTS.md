# Rules for every agent in this repo

These apply to every coding agent, whatever the vendor (Claude Code, Codex, Antigravity).

- Work only on the task you were given, only in its `allowed_paths`, only on its branch.
- Never push to `main`. Open a PR linked to the task ID.
- Never change a file listed in `interfaces_frozen`.
- If anything is ambiguous, stop and exit with a question. Do not guess.
- List every assumption you made in the PR description.
- Write tests with the code. Meet the task's Definition of Done before opening the PR.
- Commits follow Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, `chore:`).
- Never put secrets, keys or tokens in code, prompts, logs or commits.
