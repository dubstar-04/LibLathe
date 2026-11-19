
# Contribution Guidelines: 

## Build and run locally

You need Git, Python 3.10 or later, and a C++14 compiler. On Linux, you may
also need the Python development headers for your Python version.

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/dubstar-04/LibLathe.git
cd LibLathe
python3 -m venv .venv
source .venv/bin/activate
```

On Windows, use `py -3 -m venv .venv` to create the environment and
`.venv\Scripts\Activate.ps1` to activate it in PowerShell instead.

Build the native extensions and install the project in editable mode:

```bash
python -m pip install -e .
```

Run this command again after changing the C++ sources or headers.

Run an example from the repository root:

```bash
python examples/ex1_profile_op.py
```

This opens a preview using your system's image viewer and writes
`examples/profile.gcode` and `image1.jpg`, overwriting those files if they
already exist. For an example that runs without opening a viewer:

```bash
python examples/ex4_performance.py --headless
```

Other examples are in the `examples/` directory. Generated toolpaths are
experimental and must be validated before machining.

## Coding Conventions

Code to follow PEP8 style guide https://www.python.org/dev/peps/pep-0008

### Naming conventions:

Type | Style
------------ | -------------
class Names | CappedWords
module, function and variables | under_scored
private functions and variables | _leading_underscore 
constants | UPPERCASE 

### Testing

After building the project, install pytest and run the test suite from the
repository root:

```bash
python -m pip install pytest
python -m pytest --ignore=extern
```

All additional functionalilty should be complete with relevant tests where possible. Please ask if you are unsure. 
