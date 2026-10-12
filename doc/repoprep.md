Notes on repository preparation for contributors

There are two layers to ensure code quality:
* Server-side checks: `master` branch is protected in the configuration of the GitHub repository. Only commits that pass the `ruff` GitHub actions workflow are accepted.
* Client-side checks (they require special one-time preparation steps by the developer directly after cloning the repository on their machine)


To prepare a local copy of the repository for code development, do the following:

* Clone the repository as usual.

* After cloning the repository run once in repository root:
```
pre-commit install
```
This installs a pre-commit hook in `.git/hooks/` subdirectory. Only code in `src/` that passes the client-side quality checks (using the `ruff` linter) will be committed to the repository.
For manual tests before issuing `git commit`, you can launch `./run_ruff.sh`.
