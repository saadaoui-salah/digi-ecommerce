"""The geometry of the charts of the admin dashboard.

The dashboard is server rendered, so the shapes are prepared here and the
template only has to print them. The same figures feed the frontend page,
which draws its own SVG.
"""

#: The size of the line chart, in user units.
WIDTH = 640
HEIGHT = 200
PADDING = {"top": 14, "right": 10, "bottom": 26, "left": 56}


def _number(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def bar_chart(rows, limit: int = 8):
    """The bars of the "bought products by count" chart.

    ``rows`` are ``(label, count)`` pairs; the widest bar is 100%.
    """
    rows = list(rows)[:limit]
    if not rows:
        return {"bars": [], "max": 0}

    top = max((_number(count) for _, count in rows), default=0) or 1
    bars = []
    for label, count in rows:
        value = _number(count)
        bars.append(
            {
                "label": label,
                "value": int(value),
                "width": max(round((value / top) * 100, 2), 1.5),
            }
        )
    return {"bars": bars, "max": int(top)}


def line_chart(points, decimals: int = 0):
    """The points of a line chart.

    ``points`` are ``(label, value)`` pairs. The returned dictionary holds the
    coordinates of every point, the path of the line and the path of the area
    under it, ready to be printed inside an ``<svg>``.
    """
    points = list(points)
    if not points:
        return {
            "points": [],
            "line": "",
            "area": "",
            "grid": [],
            "labels": [],
            "max": 0,
            "min": 0,
        }

    values = [_number(value) for _, value in points]
    top = max(values)
    bottom = min(values)
    span = (top - bottom) or 1

    inner_width = WIDTH - PADDING["left"] - PADDING["right"]
    inner_height = HEIGHT - PADDING["top"] - PADDING["bottom"]

    def x_of(index: int) -> float:
        if len(points) == 1:
            return PADDING["left"] + inner_width / 2
        return PADDING["left"] + (index / (len(points) - 1)) * inner_width

    def y_of(value: float) -> float:
        return PADDING["top"] + inner_height - ((value - bottom) / span) * inner_height

    plotted = []
    for index, (label, value) in enumerate(points):
        plotted.append(
            {
                "label": label,
                "value": value,
                "x": round(x_of(index), 2),
                "y": round(y_of(_number(value)), 2),
            }
        )

    line = " ".join(
        f"{'M' if index == 0 else 'L'}{point['x']},{point['y']}"
        for index, point in enumerate(plotted)
    )
    area = (
        f"{line} L{plotted[-1]['x']},{PADDING['top'] + inner_height} "
        f"L{plotted[0]['x']},{PADDING['top'] + inner_height} Z"
    )

    # The grid lines and their values.
    grid = []
    for step in (0, 0.25, 0.5, 0.75, 1):
        value = bottom + span * step
        grid.append(
            {
                "y": round(y_of(value), 2),
                "label": f"{value:,.{decimals}f}",
            }
        )

    # A label every few points keeps the axis readable.
    step = max(1, -(-len(plotted) // 8))
    labels = [
        point for index, point in enumerate(plotted) if index % step == 0
    ]

    # The first and the last label lean away from the plot, so they never
    # land on the value axis.
    for index, label in enumerate(labels):
        if index == 0:
            label["anchor"] = "start"
        elif index == len(labels) - 1:
            label["anchor"] = "end"
        else:
            label["anchor"] = "middle"

    return {
        "points": plotted,
        "line": line,
        "area": area,
        "grid": grid,
        "labels": labels,
        "max": top,
        "min": bottom,
        "width": WIDTH,
        "height": HEIGHT,
        "padding_left": PADDING["left"],
        "padding_right": PADDING["right"],
    }
