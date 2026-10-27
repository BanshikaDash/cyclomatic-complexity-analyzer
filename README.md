app.py                 Streamlit app
analyzer/
  parser.py            Finds functions with tree-sitter and scores them
  cfg.py               Builds the control flow graph for one function
  complexity.py        McCabe formula and risk levels
  graph.py             Draws the graph
tests/test_analyzer.py Tests
samples/mixed.cpp      Sample C++ file