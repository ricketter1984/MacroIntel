#!/usr/bin/env python3
"""
MacroIntel Dashboard App

A Plotly Dash web application providing a local GUI for MacroIntel.
Features regime score timeline, market regime analysis, news headlines, and economic events.
"""

import dash
from dash import dcc, html, dash_table, Input, Output, State
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import data store functions
try:
    from data_store import (
        get_regime_scores_by_date_range,
        get_latest_regime_score,
        get_recent_news_by_symbol,
        get_economic_events_by_date,
        MacroIntelDataStore
    )
    DATA_STORE_AVAILABLE = True
except ImportError as e:
    print(f"❌ Error importing data store: {e}")
    DATA_STORE_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[
    'https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css'
])

app.title = "MacroIntel Dashboard"

# Initialize data store
if DATA_STORE_AVAILABLE:
    data_store = MacroIntelDataStore()
else:
    data_store = None

def get_regime_data(days=30):
    """Get regime score data for the specified number of days."""
    if not DATA_STORE_AVAILABLE:
        return pd.DataFrame()
    
    try:
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        scores = get_regime_scores_by_date_range(start_date, end_date)
        
        if scores:
            df = pd.DataFrame(scores)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"Error fetching regime data: {e}")
        return pd.DataFrame()

def get_today_regime():
    """Get today's latest regime score."""
    if not DATA_STORE_AVAILABLE:
        return None
    
    try:
        return get_latest_regime_score()
    except Exception as e:
        logger.error(f"Error fetching today's regime: {e}")
        return None

def get_headlines_data(symbol=None, limit=50):
    """Get recent headlines data."""
    if not DATA_STORE_AVAILABLE:
        return pd.DataFrame()
    
    try:
        if symbol:
            headlines = get_recent_news_by_symbol(symbol.upper(), limit=limit)
        else:
            # Get headlines for common symbols
            symbols = ['BTC', 'ETH', 'AAPL', 'TSLA', 'SPY', 'QQQ']
            all_headlines = []
            for sym in symbols:
                headlines = get_recent_news_by_symbol(sym, limit=10)
                all_headlines.extend(headlines)
            headlines = all_headlines[:limit]
        
        if headlines:
            df = pd.DataFrame(headlines)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp', ascending=False)
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"Error fetching headlines: {e}")
        return pd.DataFrame()

def get_events_data(date=None):
    """Get economic events data."""
    if not DATA_STORE_AVAILABLE:
        return pd.DataFrame()
    
    try:
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        events = get_economic_events_by_date(date)
        
        if events:
            df = pd.DataFrame(events)
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        return pd.DataFrame()

def create_regime_timeline_chart(df, show_components=False):
    """Create regime score timeline chart."""
    if df.empty:
        return go.Figure().add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Total Regime Score', 'Component Scores'),
        vertical_spacing=0.1,
        row_heights=[0.7, 0.3]
    )
    
    # Total score line
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['total_score'],
            mode='lines+markers',
            name='Total Score',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=6)
        ),
        row=1, col=1
    )
    
    # Add strategy annotations
    for _, row in df.iterrows():
        fig.add_annotation(
            x=row['timestamp'],
            y=row['total_score'],
            text=row['strategy'],
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor='#ff7f0e',
            ax=0, ay=-40,
            font=dict(size=8)
        )
    
    if show_components:
        # Component scores
        components = ['volatility', 'structure', 'momentum', 'breadth', 'institutional']
        colors = ['#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
        for i, component in enumerate(components):
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df[component],
                    mode='lines',
                    name=component.title(),
                    line=dict(color=colors[i], width=2),
                    opacity=0.7
                ),
                row=2, col=1
            )
    
    fig.update_layout(
        title='Regime Score Timeline',
        xaxis_title='Date',
        yaxis_title='Score',
        height=600,
        showlegend=True,
        hovermode='x unified'
    )
    
    return fig

def create_component_radar_chart(regime_data):
    """Create radar chart for component scores."""
    if not regime_data:
        return go.Figure().add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    components = ['volatility', 'structure', 'momentum', 'breadth', 'institutional']
    values = [regime_data[comp] for comp in components]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=[comp.title() for comp in components],
        fill='toself',
        name='Component Scores',
        line_color='#1f77b4',
        fillcolor='rgba(31, 119, 180, 0.3)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=False,
        title='Component Score Breakdown'
    )
    
    return fig

# App layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1([
            html.I(className="fas fa-chart-line mr-3"),
            "MacroIntel Dashboard"
        ], className="text-center text-primary mb-4"),
        html.Hr()
    ], className="container-fluid"),
    
    # Main content
    html.Div([
        # Row 1: Today's Regime and Component Chart
        html.Div([
            # Today's Market Regime
            html.Div([
                html.Div([
                    html.H3([
                        html.I(className="fas fa-brain mr-2"),
                        "Today's Market Regime"
                    ], className="card-title"),
                    html.Div(id="today-regime-content", className="mt-3")
                ], className="card-body")
            ], className="card h-100")
        ], className="col-md-6"),
        
        # Component Radar Chart
        html.Div([
            html.Div([
                html.H3([
                    html.I(className="fas fa-chart-pie mr-2"),
                    "Component Breakdown"
                ], className="card-title"),
                dcc.Graph(id="component-radar-chart", className="mt-3")
            ], className="card-body")
        ], className="col-md-6")
    ], className="row mb-4"),
    
    # Row 2: Regime Timeline
    html.Div([
        html.Div([
            html.Div([
                html.H3([
                    html.I(className="fas fa-chart-line mr-2"),
                    "Regime Score Timeline"
                ], className="card-title"),
                html.Div([
                    dcc.Checklist(
                        id="show-components",
                        options=[{'label': 'Show Component Scores', 'value': 'show'}],
                        value=[],
                        className="mb-3"
                    ),
                    dcc.Graph(id="regime-timeline-chart")
                ])
            ], className="card-body")
        ], className="card")
    ], className="row mb-4"),
    
    # Row 3: Headlines and Events
    html.Div([
        # Headlines Feed
        html.Div([
            html.Div([
                html.H3([
                    html.I(className="fas fa-newspaper mr-2"),
                    "GPT Headlines Feed"
                ], className="card-title"),
                html.Div([
                    dcc.Dropdown(
                        id="headline-symbol-filter",
                        options=[
                            {'label': 'All Symbols', 'value': 'all'},
                            {'label': 'BTC', 'value': 'BTC'},
                            {'label': 'ETH', 'value': 'ETH'},
                            {'label': 'AAPL', 'value': 'AAPL'},
                            {'label': 'TSLA', 'value': 'TSLA'},
                            {'label': 'SPY', 'value': 'SPY'},
                            {'label': 'QQQ', 'value': 'QQQ'}
                        ],
                        value='all',
                        className="mb-3"
                    ),
                    html.Div(id="headlines-content", style={'maxHeight': '400px', 'overflowY': 'scroll'})
                ])
            ], className="card-body")
        ], className="card h-100")
    ], className="col-md-6"),
    
    # Economic Events
    html.Div([
        html.Div([
            html.H3([
                html.I(className="fas fa-calendar-alt mr-2"),
                "Economic Events"
            ], className="card-title"),
            html.Div([
                dcc.DatePickerSingle(
                    id="events-date-picker",
                    date=datetime.now().date(),
                    className="mb-3"
                ),
                html.Div(id="events-content")
            ])
        ], className="card-body")
    ], className="col-md-6")
    ], className="row mb-4"),
    
    # Row 4: Backtest Launcher
    html.Div([
        html.Div([
            html.Div([
                html.H3([
                    html.I(className="fas fa-flask mr-2"),
                    "Backtest Launcher"
                ], className="card-title"),
                html.Div([
                    html.Div([
                        html.Label("Strategy:", className="font-weight-bold"),
                        dcc.Dropdown(
                            id="backtest-strategy",
                            options=[
                                {'label': 'Tier 1 Reversal', 'value': 'Tier 1 Reversal'},
                                {'label': 'Tier 2 Mean Reversion', 'value': 'Tier 2 Mean Reversion'},
                                {'label': 'Tier 3 Range Trading', 'value': 'Tier 3 Range Trading'},
                                {'label': 'Tier 4 Momentum', 'value': 'Tier 4 Momentum'},
                                {'label': 'Tier 5 Extreme Momentum', 'value': 'Tier 5 Extreme Momentum'}
                            ],
                            value='Tier 1 Reversal',
                            className="mb-3"
                        )
                    ], className="col-md-3"),
                    html.Div([
                        html.Label("Min Score:", className="font-weight-bold"),
                        dcc.Slider(
                            id="backtest-min-score",
                            min=0,
                            max=100,
                            step=5,
                            value=70,
                            marks={i: str(i) for i in range(0, 101, 20)},
                            className="mb-3"
                        )
                    ], className="col-md-3"),
                    html.Div([
                        html.Label("Date Range:", className="font-weight-bold"),
                        dcc.DatePickerRange(
                            id="backtest-date-range",
                            start_date=(datetime.now() - timedelta(days=30)).date(),
                            end_date=datetime.now().date(),
                            className="mb-3"
                        )
                    ], className="col-md-3"),
                    html.Div([
                        html.Button(
                            "Run Backtest",
                            id="run-backtest-btn",
                            className="btn btn-primary mt-4"
                        )
                    ], className="col-md-3")
                ], className="row"),
                html.Div(id="backtest-results")
            ], className="card-body")
        ], className="card")
    ], className="row mb-4"),
    
    # Refresh button
    html.Div([
        html.Button([
            html.I(className="fas fa-sync-alt mr-2"),
            "Refresh Data"
        ], id="refresh-btn", className="btn btn-secondary btn-lg btn-block")
    ], className="text-center mb-4"),
    
    # Hidden div for storing data
    html.Div(id="data-store", style={'display': 'none'}),
    
    # Interval component for auto-refresh
    dcc.Interval(
        id='interval-component',
        interval=5*60*1000,  # 5 minutes
        n_intervals=0
    )
], className="container-fluid")

# Callbacks
@app.callback(
    [Output("today-regime-content", "children"),
     Output("component-radar-chart", "figure")],
    [Input("refresh-btn", "n_clicks"),
     Input("interval-component", "n_intervals")]
)
def update_today_regime(n_clicks, n_intervals):
    """Update today's regime data."""
    regime_data = get_today_regime()
    
    if regime_data:
        content = html.Div([
            html.Div([
                html.H4(f"Total Score: {regime_data['total_score']:.1f}/100", 
                       className="text-primary"),
                html.P(f"Strategy: {regime_data['strategy']}", className="mb-2"),
                html.P(f"Instrument: {regime_data['instrument']}", className="mb-2"),
                html.P(f"Timestamp: {regime_data['timestamp'][:19]}", className="text-muted")
            ])
        ])
        
        radar_chart = create_component_radar_chart(regime_data)
    else:
        content = html.Div([
            html.P("No regime data available", className="text-muted")
        ])
        radar_chart = create_component_radar_chart(None)
    
    return content, radar_chart

@app.callback(
    Output("regime-timeline-chart", "figure"),
    [Input("show-components", "value"),
     Input("refresh-btn", "n_clicks"),
     Input("interval-component", "n_intervals")]
)
def update_regime_timeline(show_components, n_clicks, n_intervals):
    """Update regime timeline chart."""
    df = get_regime_data(days=30)
    show_comp = 'show' in show_components if show_components else False
    return create_regime_timeline_chart(df, show_comp)

@app.callback(
    Output("headlines-content", "children"),
    [Input("headline-symbol-filter", "value"),
     Input("refresh-btn", "n_clicks"),
     Input("interval-component", "n_intervals")]
)
def update_headlines(symbol_filter, n_clicks, n_intervals):
    """Update headlines feed."""
    if symbol_filter == 'all':
        df = get_headlines_data(limit=30)
    else:
        df = get_headlines_data(symbol=symbol_filter, limit=30)
    
    if df.empty:
        return html.P("No headlines available", className="text-muted")
    
    headlines = []
    for _, row in df.iterrows():
        sentiment_color = {
            'positive': 'success',
            'negative': 'danger',
            'neutral': 'secondary'
        }.get(row.get('sentiment', 'neutral'), 'secondary')
        
        headlines.append(html.Div([
            html.Div([
                html.H6(row['headline'], className="card-title"),
                html.P(row.get('summary', '')[:150] + "...", className="card-text"),
                html.Div([
                    html.Span(f"Source: {row['source']}", className="badge badge-info mr-2"),
                    html.Span(f"Symbol: {row.get('symbol', 'N/A')}", className="badge badge-primary mr-2"),
                    html.Span(f"Sentiment: {row.get('sentiment', 'neutral')}", 
                             className=f"badge badge-{sentiment_color}"),
                    html.Small(f" • {row['timestamp'][:19]}", className="text-muted ml-2")
                ])
            ], className="card-body")
        ], className="card mb-3"))
    
    return headlines

@app.callback(
    Output("events-content", "children"),
    [Input("events-date-picker", "date"),
     Input("refresh-btn", "n_clicks"),
     Input("interval-component", "n_intervals")]
)
def update_events(selected_date, n_clicks, n_intervals):
    """Update economic events."""
    if selected_date:
        date_str = selected_date[:10]  # Extract YYYY-MM-DD
        df = get_events_data(date_str)
    else:
        df = get_events_data()
    
    if df.empty:
        return html.P("No events for this date", className="text-muted")
    
    # Create table
    table_data = []
    for _, row in df.iterrows():
        impact_color = {
            'High': 'danger',
            'Medium': 'warning',
            'Low': 'success'
        }.get(row.get('impact_level', 'Low'), 'secondary')
        
        table_data.append({
            'Time': row.get('time', ''),
            'Event': row.get('event_name', ''),
            'Impact': row.get('impact_level', ''),
            'Category': row.get('category', ''),
            'Forecast': row.get('forecast', ''),
            'Actual': row.get('actual', '')
        })
    
    return dash_table.DataTable(
        data=table_data,
        columns=[
            {'name': 'Time', 'id': 'Time'},
            {'name': 'Event', 'id': 'Event'},
            {'name': 'Impact', 'id': 'Impact'},
            {'name': 'Category', 'id': 'Category'},
            {'name': 'Forecast', 'id': 'Forecast'},
            {'name': 'Actual', 'id': 'Actual'}
        ],
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '10px'},
        style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
        style_data_conditional=[
            {
                'if': {'column_id': 'Impact', 'filter_query': '{Impact} = High'},
                'backgroundColor': '#ffebee',
                'color': '#c62828'
            },
            {
                'if': {'column_id': 'Impact', 'filter_query': '{Impact} = Medium'},
                'backgroundColor': '#fff3e0',
                'color': '#ef6c00'
            }
        ]
    )

@app.callback(
    Output("backtest-results", "children"),
    [Input("run-backtest-btn", "n_clicks")],
    [State("backtest-strategy", "value"),
     State("backtest-min-score", "value"),
     State("backtest-date-range", "start_date"),
     State("backtest-date-range", "end_date")]
)
def run_backtest(n_clicks, strategy, min_score, start_date, end_date):
    """Run backtest simulation."""
    if not n_clicks or not DATA_STORE_AVAILABLE:
        return html.Div()
    
    try:
        # Query for matches
        with data_store.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT timestamp, total_score, volatility, structure, momentum, 
                       breadth, institutional, strategy, instrument
                FROM regime_scores 
                WHERE strategy = ? 
                AND total_score >= ?
                AND date(timestamp) >= ?
                AND date(timestamp) <= ?
                ORDER BY timestamp DESC
            """
            cursor.execute(query, [strategy, min_score, start_date, end_date])
            results = cursor.fetchall()
        
        if not results:
            return html.Div([
                html.P("No matches found for the specified criteria", className="text-muted")
            ])
        
        # Create results table
        table_data = []
        for row in results:
            table_data.append({
                'Date': row[0][:10],
                'Total Score': f"{row[1]:.1f}",
                'Strategy': row[7],
                'Instrument': row[8],
                'Volatility': f"{row[2]:.1f}",
                'Structure': f"{row[3]:.1f}",
                'Momentum': f"{row[4]:.1f}"
            })
        
        return html.Div([
            html.H5(f"Backtest Results: {len(results)} matches found"),
            dash_table.DataTable(
                data=table_data,
                columns=[
                    {'name': 'Date', 'id': 'Date'},
                    {'name': 'Total Score', 'id': 'Total Score'},
                    {'name': 'Strategy', 'id': 'Strategy'},
                    {'name': 'Instrument', 'id': 'Instrument'},
                    {'name': 'Volatility', 'id': 'Volatility'},
                    {'name': 'Structure', 'id': 'Structure'},
                    {'name': 'Momentum', 'id': 'Momentum'}
                ],
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'padding': '8px'},
                style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
            )
        ])
        
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        return html.Div([
            html.P(f"Error running backtest: {e}", className="text-danger")
        ])

if __name__ == '__main__':
    print("🚀 Starting MacroIntel Dashboard...")
    print("📊 Dashboard will be available at: http://127.0.0.1:8050")
    print("🔄 Auto-refresh every 5 minutes")
    print("⏹️  Press Ctrl+C to stop")
    
    try:
        app.run_server(debug=True, host='127.0.0.1', port=8050)
    except KeyboardInterrupt:
        print("\n⏹️  Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}") 