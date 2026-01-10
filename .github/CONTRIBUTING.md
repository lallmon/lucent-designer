## Contributing to Lucent Designer

## Dual-License Model
This project uses a dual-license model:
- **Community:** GPLv3 (free, open source)
- **Commercial:** Proprietary license (paid)

## For Contributors
All contributions require signing our CLA (Contributor License Agreement).

There's plenty to do but the end goal is pretty clear for me, so if you want to help out, I appreciate any contributions.

What I'd love are people who wish there were modern design applications on Linux, to play with the software and contribute bug reports, feature requests, and Documentation.

- What tools are missing from the software?
- What UX can be improved?
- What isn't working as expected?

### Feature Requests

Feature requests are driven with User Stories and Acceptance Criteria defined.

#### User Stories

User stories are written with the template of:
- **As a** [kind of user],
- **I want** [what the feature does],
- **So that** [the value I get out of this feature]" 

Example: 

- *As a designer,*
- *I want items on the canvas to snap to a grid,* 
- *So I can make layouts with better precision*

#### Acceptance Criteria 
Acceptance criteria are defined with the "Given, When, Then" approach.
- **Given** [state of the system]
- **And** [optional other states]
- **When** [I perform this action]
- **Then** [the output of the action]
- **And** [optional other outputs]

So for the example user story above:

- *Given I have an item selected on the canvas,*
- *And the snapping function is enabled,*
- *When I drag the item around the canvas,*
- *The item snaps to the grid at it's default fidelity.*

Reasoning: This allows us to have conversations about the app and it's functionality that aren't overly technical and can look for intrinsic user value.

### Developing the App

Prerequisites: Python 3.10

- Clone the Repo: `git clone git@github.com:lallmon/lucent-designer.git`
- Create/activate the project venv: `python -m venv .venv && source .venv/bin/activate`
- Install deps: `pip install -r requirements.txt -r requirements-dev.txt`
- Install the app package: `pip install -e .`
- Install pre-commit hooks: `pre-commit install`

Run the app: `python main.py`

Run tests: `pytest -q`

### Lint/type checks:
- QML format: `pyside6-qmlformat -i components/*.qml`
- QML lint: `pyside6-qmllint -I components App.qml`
- Python format: `ruff format .`
- Python lint: `ruff check .`
- Type check: `mypy --config-file mypy.ini src tests main.py`
- All hooks: `pre-commit run --all-files`

Notes: 
- The CI/CD Pipeline **will fail** the build if these don't pass, so make sure you're installing pre-commit as stated above.

- If a commit fails because of a formatter, commit again because the it should automatically have reformatted the code (it will say how many files it modified on this)

## AI Usage and VibeCoding
I am not against this at all, but will be scrutinizing architectural decisions and especially critical of QML layouts, which are easy to slop up.

Make sure your LLM is following some general rules:
- scan the app and try to follow already established conventions
- use functions and variable names that mean something, call variables what they are and functions what they do.
- remove/avoid low value comments that just reiterate what a function does.
- functions and methods should use the Single Responsibility Principle, which is do one thing and do it well.
- write unit tests of expected functionality first, then write code that passes the tests in a Red/Green TDD fashion.
- Aim for at 90% code coverage on backend python code per patch.
- NEVER use JavaScript for coding or debug tooling, this is a QML + Python app.
- we use the python virtual environment in the .venv folder in the root of the project, activate and use that for python commands.