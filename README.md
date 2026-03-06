

# GitHub Actions for continuous integration and delivery of Seedcase repositories

<!-- TODO: Include DOI after uploading -->

<!-- [![PyPI Version](https://img.shields.io/pypi/v/actions.svg)](https://pypi.org/project/actions/) -->

[![Copier](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-inverted-border-teal.json?raw=true.svg)](https://github.com/copier-org/copier)
[![Python Version from PEP 621
TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https://raw.githubusercontent.com/seedcase-project/actions/refs/heads/main/pyproject.toml)](https://github.com/seedcase-project/actions/blob/main/pyproject.toml)
[![GitHub
License](https://img.shields.io/github/license/seedcase-project/actions.svg)](https://github.com/seedcase-project/actions/blob/main/LICENSE.md)
[![GitHub
Release](https://img.shields.io/github/v/release/seedcase-project/actions.svg)](https://github.com/seedcase-project/actions/releases/latest)
[![Build
documentation](https://github.com/seedcase-project/actions/actions/workflows/build-website.yml/badge.svg)](https://github.com/seedcase-project/actions/actions/workflows/build-website.yml)
[![Check
package](https://github.com/seedcase-project/actions/actions/workflows/check-package.yml/badge.svg)](https://github.com/seedcase-project/actions/actions/workflows/check-package.yml)
[![OpenSSF
Scorecard](https://api.scorecard.dev/projects/github.com/seedcase-project/actions/badge?raw=true.svg)](https://scorecard.dev/viewer/?uri=github.com/seedcase-project/actions)
[![CodeQL](https://github.com/seedcase-project/actions/actions/workflows/github-code-scanning/codeql/badge.svg?branch=main)](https://github.com/seedcase-project/actions/actions/workflows/github-code-scanning/codeql)
[![code
coverage](https://raw.githubusercontent.com/seedcase-project/actions/coverage/coverage.svg?raw=true)](https://htmlpreview.github.io/?https://raw.githubusercontent.com/seedcase-project/actions/coverage/index.html)
[![pre-commit.ci
status](https://results.pre-commit.ci/badge/github/seedcase-project/actions/main.svg)](https://results.pre-commit.ci/latest/github/seedcase-project/actions/main)
[![lifecycle](https://lifecycle.r-lib.org/articles/figures/lifecycle-experimental.svg)](https://lifecycle.r-lib.org/articles/stages.html#experimental)
[![Project Status: WIP – Initial development is in progress, but there
has not yet been a stable, usable release suitable for the
public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)
<!-- [![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active) -->

This repository contains GitHub [reusable
workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)
and [actions](https://docs.github.com/en/actions/get-started/quickstart)
that we use in the Seedcase Project for making our work easier and more
efficient. We also use these workflows in projects that we collaborate
on, such as [ON-LiMiT](https://onlimit.org) and
[DP-Next](https://dp-next.github.io).

Check out our [website](https://actions.seedcase-project.org) for more
information, such as the features it provides and a
[guide](https://actions.seedcase-project.org/docs/guide/) to using the
GitHub actions and workflows.

> [!TIP]
>
> This Python package was generated from the
> [`template-python-package`](https://github.com/seedcase-project/template-python-package)
> Seedcase template :tada:

## Project files and folders

- `.github/`: Contains GitHub-specific files, such as issue and pull
  request templates, workflows,
  [dependabot](https://docs.github.com/en/code-security/tutorials/secure-your-dependencies/dependabot-quickstart-guide)
  configuration, pull request templates, and a
  [CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
  file.
- `tools/vulture-allowlist.py`: List of variables that shouldn’t be
  flagged by [Vulture](https://github.com/jendrikseipp/vulture) as
  unused.
- `tools/get-contributors.sh`: Script to get list of project
  contributors.
- `tests/`: Test files for the package.
- `src/`: Source code for the package.
- `docs/`: Documentation about using and developing the Python package.
- `_renderer.py`: Custom
  [`quartodoc`](https://machow.github.io/quartodoc/) renderer.
- `pytest.ini`: Pytest configuration file.
- `mypy.ini`: [`mypy`](https://mypy.readthedocs.io/en/stable/)
  configuration file for type checking Python code.
- `.copier-answers.yml`: Contains the answers you gave when copying the
  project from the template. **You should not modify this file
  directly.**
- `.cz.toml`:
  [Commitizen](https://commitizen-tools.github.io/commitizen/)
  configuration file for managing versions and changelogs.
- `.pre-commit-config.yaml`: [Pre-commit](https://pre-commit.com/)
  configuration file for managing and running checks before each commit.
- `.typos.toml`: [typos](https://github.com/crate-ci/typos) spell
  checker configuration file.
- `justfile`: [`just`](https://just.systems/man/en/) configuration file
  for scripting project tasks.
- `.editorconfig`: Editor configuration file for
  [EditorConfig](https://editorconfig.org/) to maintain consistent
  coding styles across different editors and IDEs.
- `CHANGELOG.md`: Changelog file for tracking changes in the project.
- `CITATION.cff`: Structured citation metadata for your project.
- `CONTRIBUTING.md`: Guidelines for contributing to the project.
- `_metadata.yml`: Quarto metadata file for the website, including
  information about the project, such as the titles and GitHub names.
- `pyproject.toml`: Main Python project configuration file defining
  metadata and dependencies.
- `_quarto.yml`: Quarto configuration file for the website, including
  settings for the website, such as the theme, navigation, and other
  options.
- `ruff.toml`: [Ruff](https://docs.astral.sh/ruff/) configuration file
  for linting and formatting Python code.
- `uv.lock`: Lockfile used by [`uv`](https://docs.astral.sh/uv/) to
  record exact versions of installed dependencies.
- `.rumdl.toml`: [rumdl](https://rumdl.dev/) configuration file for
  formatting Markdown files so that they are standardized and consistent

## Contributing

Check out our [contributing document](CONTRIBUTING.md) for information
on how to contribute to the project, including how to set up your
development environment.

Please note that this project is released with a [Contributor Code of
Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree
to abide by its terms.

## Licensing

This project is licensed under the [MIT License](LICENSE.md).

## Changelog

For a list of changes, see our [changelog](CHANGELOG.md) page.
