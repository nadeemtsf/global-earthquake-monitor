from pathlib import Path
import sys

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import chart_utils  # noqa: E402


def test_darken_fig_applies_dark_colors():
    fig, ax = plt.subplots()
    chart_utils.darken_fig(fig, ax)
    assert fig.get_facecolor() == plt.matplotlib.colors.to_rgba(chart_utils.DARK_BG)
    assert ax.xaxis.label.get_color() == chart_utils.DARK_FG
    plt.close(fig)


def test_dark_chart_calls_show_fig(monkeypatch):
    called = {"count": 0}

    def fake_show(_fig):
        called["count"] += 1

    monkeypatch.setattr(chart_utils, "show_fig", fake_show)

    with chart_utils.dark_chart(title="Test", xlabel="X", ylabel="Y", legend="Legend") as (fig, ax):
        ax.plot([1, 2], [3, 4], label="line")

    assert called["count"] == 1
    plt.close(fig)

