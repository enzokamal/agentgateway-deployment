def chart_tool(spec, analysis_context=None):
    """
    Convert reporting-agent chart_spec into Plotly-compatible format
    """
    chart_type = spec.get("chart_type", "bar")
    title = spec.get("title", "Chart")
    x = spec.get("x_axis", [])
    y = spec.get("y_axis", [])

    # fallback context if x/y not provided
    if analysis_context:
        x = analysis_context.get("x", x)
        y = analysis_context.get("y", y)

    if not x or not y:
        x = ["Jan", "Feb", "Mar"]
        y = [10, 20, 15]

    if chart_type == "bar":
        return {
            "data": [{"type": "bar", "x": x, "y": y}],
            "layout": {"title": title, "autosize": True}
        }
    if chart_type == "line":
        return {
            "data": [{"type": "scatter", "mode": "lines+markers", "x": x, "y": y}],
            "layout": {"title": title, "autosize": True}
        }
    if chart_type == "pie":
        return {
            "data": [{"type": "pie", "labels": x, "values": y}],
            "layout": {"title": title, "autosize": True}
        }
    return None
