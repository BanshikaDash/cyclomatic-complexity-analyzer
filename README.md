# Cyclomatic Complexity Analyzer

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://cyclomatic-complexity-analyzer.streamlit.app/)

A Python and Streamlit app that measures the cyclomatic complexity of every function in a C++ file and draws the real control flow graph of any function you pick.

**Live app:** https://cyclomatic-complexity-analyzer.streamlit.app/

> Free Streamlit apps go to sleep when nobody uses them. If you see a "gone to sleep" page, click the wake-up button and wait a few seconds.

## What it does

- Upload a C++ file (`.cpp`, `.cc`, `.cxx`, `.h`, `.hpp`).
- Finds every function, including class methods, constructors and templates.
- Gives each function its own complexity score and a risk level (Low, Moderate, High, Very high).
- Draws the control flow graph of the function you select.
- Lists every decision point with its line number.
- Lets you download the full report as JSON.

## How the score is calculated

Each function starts at 1. Each of these adds 1:

`if`, `else if`, `for`, `while`, `do-while`, `case`, `catch`, `&&`, `||`, `?:`

The score comes from the control flow graph using McCabe's formula:

```
M = E - N + 2
```

where `E` is the number of edges and `N` is the number of nodes. This always equals 1 plus the number of decision points.

Comments and strings are ignored. A lambda is counted as its own function, so its branches do not add to the function that contains it.

### Risk levels

| Complexity | Risk |
|-----------|------|
| 1 to 10 | Low |
| 11 to 20 | Moderate |
| 21 to 50 | High |
| Above 50 | Very high |

## Example

```cpp
int classify(int number) {
    if (number < 0) {
        return -1;
    } else if (number == 0) {
        return 0;
    }

    if (number > 10 && number < 100) {
        return 1;
    }

    return 2;
}
```

`classify` scores **5**: the base of 1, plus two `if`s, one `else if` and one `&&`.

## Run it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app opens at http://localhost:8501. Try it with `samples/mixed.cpp`.

## Run the tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

## Project structure

```
app.py                 Streamlit app
analyzer/
  parser.py            Finds functions with tree-sitter and scores them
  cfg.py               Builds the control flow graph for one function
  complexity.py        McCabe formula and risk levels
  graph.py             Draws the graph
tests/test_analyzer.py Tests
samples/mixed.cpp      Sample C++ file
```

## Limitations

- Code that depends on macros the parser cannot expand may be scored slightly off. The app shows a warning when it finds syntax it cannot read.
- `goto` is not followed.
- `?:` and `&&` / `||` inside a lambda are not counted in the enclosing function.
- Very large functions produce very large graphs.

## Built with

Python, Streamlit, tree-sitter, NetworkX and Matplotlib.