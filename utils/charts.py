"""
charts.py
---------
All Plotly visualisations for the Employee Recognition dashboard.
Kept separate from app.py to keep the UI file clean.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


# Brand colours
PRIMARY   = "#1B5E96"
SECONDARY = "#2E75B6"
ACCENT    = "#FFC107"
LIGHT_BG  = "#F0F7FF"
GREY      = "#6C757D"


def score_bar_chart(df: pd.DataFrame) -> go.Figure:
    """
    Horizontal bar chart — all employees ranked by composite score.
    Eligible employees shown in primary blue, ineligible in grey.
    """
    df_sorted = df.sort_values("composite_score", ascending=True).copy()
    df_sorted["colour"] = df_sorted["eligible"].map({True: PRIMARY, False: "#CCCCCC"})
    df_sorted["label"] = df_sorted.apply(
        lambda r: r["name"] if r["eligible"] else f"{r['name']} (ineligible)", axis=1
    )

    fig = go.Figure(go.Bar(
        x=df_sorted["composite_score"],
        y=df_sorted["label"],
        orientation="h",
        marker_color=df_sorted["colour"],
        text=df_sorted["composite_score"].apply(lambda x: f"{x:.1f}"),
        textposition="outside",
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Score: %{x:.2f}<br>"
            "<extra></extra>"
        )
    ))

    fig.update_layout(
        title="Employee Scores — Current Month",
        title_font=dict(size=16, color=PRIMARY),
        xaxis_title="Composite Score (0–100)",
        yaxis_title="",
        xaxis=dict(range=[0, 115]),
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=max(300, len(df) * 42),
        margin=dict(l=20, r=40, t=50, b=20),
        font=dict(family="Arial", size=13),
        showlegend=False,
    )
    fig.update_xaxes(showgrid=True, gridcolor="#F0F0F0")
    fig.update_yaxes(showgrid=False)
    return fig


def score_breakdown_radar(winner: pd.Series, weights: dict) -> go.Figure:
    """
    Radar chart showing the winner's normalised scores across each criterion.
    """
    metrics = list(weights.keys())
    labels  = [m.replace("_", " ").title() for m in metrics]
    values  = [float(winner.get(f"{m}_norm", 0)) for m in metrics]
    values += values[:1]   # close the polygon
    labels += labels[:1]

    fig = go.Figure(go.Scatterpolar(
        r=values,
        theta=labels,
        fill="toself",
        fillcolor=f"rgba(27, 94, 150, 0.18)",
        line=dict(color=PRIMARY, width=2),
        marker=dict(size=6, color=PRIMARY),
        name=winner["name"],
        hovertemplate="%{theta}: %{r:.1f}<extra></extra>",
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=11)),
            angularaxis=dict(tickfont=dict(size=12)),
        ),
        title=f"Score Breakdown — {winner['name']}",
        title_font=dict(size=15, color=PRIMARY),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=40, r=40, t=60, b=40),
        height=380,
        showlegend=False,
    )
    return fig


def department_avg_bar(df: pd.DataFrame) -> go.Figure:
    """Bar chart of average composite score by department."""
    dept = (
        df.groupby("department")["composite_score"]
        .mean()
        .reset_index()
        .sort_values("composite_score", ascending=False)
    )

    fig = px.bar(
        dept,
        x="department",
        y="composite_score",
        color="composite_score",
        color_continuous_scale=[[0, "#BDD7EE"], [1, PRIMARY]],
        text=dept["composite_score"].apply(lambda x: f"{x:.1f}"),
        labels={"composite_score": "Avg Score", "department": "Department"},
        title="Average Score by Department",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        coloraxis_showscale=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
        font=dict(family="Arial", size=13),
        title_font=dict(size=15, color=PRIMARY),
        yaxis=dict(range=[0, 115], showgrid=True, gridcolor="#F0F0F0"),
        xaxis=dict(showgrid=False),
    )
    return fig


def metric_contribution_pie(winner: pd.Series, weights: dict) -> go.Figure:
    """
    Pie chart showing each criterion's weighted contribution
    to the winner's final score.
    """
    metrics = list(weights.keys())
    labels  = [m.replace("_", " ").title() for m in metrics]
    contributions = [
        float(winner.get(f"{m}_norm", 0)) * w
        for m, w in weights.items()
    ]

    colours = [PRIMARY, SECONDARY, "#4FA3D1", ACCENT]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=contributions,
        hole=0.45,
        marker=dict(colors=colours),
        textinfo="label+percent",
        hovertemplate="%{label}<br>Contribution: %{value:.1f} pts<extra></extra>",
    ))

    fig.update_layout(
        title=f"Score Composition — {winner['name']}",
        title_font=dict(size=15, color=PRIMARY),
        paper_bgcolor="white",
        height=350,
        margin=dict(l=20, r=20, t=60, b=20),
        font=dict(family="Arial", size=13),
        showlegend=True,
        legend=dict(orientation="v", x=1.02),
        annotations=[dict(
            text=f"{winner['composite_score']:.1f}",
            x=0.5, y=0.5,
            font_size=22,
            font_color=PRIMARY,
            showarrow=False
        )]
    )
    return fig


def history_line_chart(history_df: pd.DataFrame) -> go.Figure:
    """Line chart of winner scores over time."""
    if history_df.empty:
        fig = go.Figure()
        fig.update_layout(title="No history yet", height=250)
        return fig

    fig = px.line(
        history_df,
        x="month",
        y="composite_score",
        markers=True,
        text="name",
        labels={"composite_score": "Score", "month": "Month"},
        title="Winner Scores Over Time",
        color_discrete_sequence=[PRIMARY],
    )
    fig.update_traces(
        textposition="top center",
        line=dict(width=2.5),
        marker=dict(size=9),
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        font=dict(family="Arial", size=12),
        title_font=dict(size=15, color=PRIMARY),
        yaxis=dict(range=[0, 110], showgrid=True, gridcolor="#F0F0F0"),
        xaxis=dict(showgrid=False),
    )
    return fig
