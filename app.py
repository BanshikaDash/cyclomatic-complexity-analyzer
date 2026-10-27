import json
from pathlib import Path

import streamlit as st

from analyzer.parser import analyze_source
from analyzer.complexity import calculate_from_decisions
from analyzer.graph import build_graph, draw_graph


st.set_page_config(
    page_title="Cyclomatic Complexity Analyzer",
    page_icon="📊",
    layout="wide",
)

st.title("Cyclomatic Complexity Analyzer")
st.write(
    "Upload a C++ source file to inspect its functions, "
    "decision points, logical operators, and estimated complexity."
)

st.info(
    "Prototype notice: the current analyzer uses regular expressions "
    "rather than a complete C++ parser. The displayed graph is illustrative, "
    "not a reconstruction of the source's actual control flow."
)

uploaded_file = st.file_uploader(
    "Upload a C++ file",
    type=["cpp", "cc", "cxx", "h", "hpp"],
)

if uploaded_file is not None:
    try:
        source = uploaded_file.getvalue().decode("utf-8-sig")
    except UnicodeDecodeError:
        st.error("The uploaded file could not be decoded as UTF-8.")
        st.stop()

    if not source.strip():
        st.warning("The uploaded file is empty.")
        st.stop()

    result = analyze_source(source)

    decision_count = result["decision_count"]
    logical_count = result["logical_operator_count"]

    # This is a source-level estimate, not a graph-derived measurement.
    estimated_complexity = calculate_from_decisions(
        decision_count + logical_count
    )

    st.subheader("Analysis summary")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Functions detected", result["function_count"])
    col2.metric("Decision keywords", decision_count)
    col3.metric("Logical operators", logical_count)
    col4.metric("Estimated complexity", estimated_complexity)

    st.caption(
        "Estimate = 1 + detected decision keywords + detected && and || operators. "
        "This convention is approximate and may not match a compiler-derived CFG."
    )

    st.subheader("Detected functions")

    if result["functions"]:
        function_rows = [
            {
                "Function": function["name"],
                "Signature": function["signature"],
                "Start line": function["start_line"],
                "End line": function["end_line"],
            }
            for function in result["functions"]
        ]
        st.dataframe(function_rows, use_container_width=True)
    else:
        st.warning(
            "No functions were detected. The regular-expression parser "
            "may not support the uploaded C++ syntax."
        )

    left, right = st.columns(2)

    with left:
        st.subheader("Decision points")

        if result["decisions"]:
            st.dataframe(
                result["decisions"],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.write("No decision keywords were detected.")

    with right:
        st.subheader("Logical operators")

        if result["logical_operators"]:
            st.dataframe(
                result["logical_operators"],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.write("No && or || operators were detected.")

    st.subheader("Illustrative control flow graph")

    graph = build_graph(decision_count)

    figure = draw_graph(graph)
    st.pyplot(figure)
    st.caption(
        "This diagram illustrates a sequence of decision nodes. "
        "It does not represent the actual branches or loops of the uploaded code."
    )

    report = {
        "filename": uploaded_file.name,
        "analysis_type": "prototype_source_level_estimate",
        "function_count": result["function_count"],
        "decision_count": decision_count,
        "logical_operator_count": logical_count,
        "estimated_complexity": estimated_complexity,
        "functions": [
            {
                "name": function["name"],
                "signature": function["signature"],
                "start_line": function["start_line"],
                "end_line": function["end_line"],
            }
            for function in result["functions"]
        ],
        "decisions": result["decisions"],
        "logical_operators": result["logical_operators"],
        "graph_is_illustrative": True,
    }

    st.download_button(
        label="Download analysis report (JSON)",
        data=json.dumps(report, indent=2),
        file_name="complexity_report.json",
        mime="application/json",
    )

else:
    st.write("Upload a C++ file to begin analysis.")
