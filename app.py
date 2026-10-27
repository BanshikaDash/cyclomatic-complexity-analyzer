import json

import streamlit as st

from analyzer.graph import draw_graph
from analyzer.parser import analyze_source

st.set_page_config(
    page_title="Cyclomatic Complexity Analyzer",
    page_icon="📊",
    layout="wide",
)

st.title("Cyclomatic Complexity Analyzer")
st.write(
    "Upload a C++ file to see how complex each function is, "
    "and view the real control flow graph of any function."
)

uploaded_file = st.file_uploader(
    "Upload a C++ file",
    type=["cpp", "cc", "cxx", "h", "hpp"],
)

if uploaded_file is None:
    st.write("Upload a C++ file to begin analysis.")
    st.stop()

try:
    source = uploaded_file.getvalue().decode("utf-8-sig")
except UnicodeDecodeError:
    st.error("The uploaded file could not be decoded as UTF-8.")
    st.stop()

if not source.strip():
    st.warning("The uploaded file is empty.")
    st.stop()

result = analyze_source(source)

if result["has_syntax_errors"]:
    st.warning(
        "The parser found syntax it could not understand (for example, "
        "unexpanded macros). Results for the affected functions may be off."
    )

functions = result["functions"]
if not functions:
    st.warning("No functions with a body were found in this file.")
    st.stop()

st.subheader("Summary")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Functions", result["function_count"])
col2.metric("Highest complexity", result["max_complexity"])
col3.metric("Average complexity", result["average_complexity"])
col4.metric(
    "Functions above 10",
    sum(1 for function in functions if function["complexity"] > 10),
)
st.caption(
    "Each function is scored on its own. Every if, for, while, do-while, case, "
    "catch, &&, || and ?: adds 1 to a base of 1. Lambdas are not counted "
    "inside the function that contains them."
)

st.subheader("Functions")
st.dataframe(
    [
        {
            "Function": function["name"],
            "Lines": f'{function["start_line"]}-{function["end_line"]}',
            "Complexity": function["complexity"],
            "Risk": function["risk"],
            "Signature": function["signature"],
        }
        for function in functions
    ],
    width="stretch",
    hide_index=True,
)

labels = [
    f'{function["name"]} (line {function["start_line"]})' for function in functions
]
default_index = max(
    range(len(functions)), key=lambda index: functions[index]["complexity"]
)
choice = st.selectbox("Pick a function to inspect", labels, index=default_index)
selected = functions[labels.index(choice)]
graph = selected["graph"]

st.subheader(f'Control flow graph: {selected["name"]}')
nodes, edges = graph.number_of_nodes(), graph.number_of_edges()
st.caption(
    f"Complexity = edges - nodes + 2 = {edges} - {nodes} + 2 = "
    f'{selected["complexity"]}'
)

left, right = st.columns([2, 1])
with left:
    st.pyplot(
        draw_graph(graph, f'{selected["name"]} (complexity {selected["complexity"]})')
    )
with right:
    st.write("**Decision points**")
    if selected["decisions"]:
        st.dataframe(selected["decisions"], width="stretch", hide_index=True)
    else:
        st.write("None. This function has a single path.")

report = {
    "filename": uploaded_file.name,
    "function_count": result["function_count"],
    "max_complexity": result["max_complexity"],
    "average_complexity": result["average_complexity"],
    "functions": [
        {
            "name": function["name"],
            "signature": function["signature"],
            "start_line": function["start_line"],
            "end_line": function["end_line"],
            "complexity": function["complexity"],
            "risk": function["risk"],
            "decision_counts": function["decision_counts"],
            "decisions": function["decisions"],
        }
        for function in functions
    ],
}

st.download_button(
    label="Download analysis report (JSON)",
    data=json.dumps(report, indent=2),
    file_name="complexity_report.json",
    mime="application/json",
)
