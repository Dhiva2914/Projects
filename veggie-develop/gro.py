import requests
from bs4 import BeautifulSoup
import pandas as pd
import dash
from dash import html, dcc, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
from datetime import datetime

def parse_price(price_str):
    """Extract the minimum price from a price range string"""
    try:
        # Remove '₹' and 'per kg' if present
        price = price_str.replace('₹', '').replace('per kg', '').strip()
        # If there's a range (e.g., "40-50"), take the first number
        if '-' in price:
            price = price.split('-')[0]
        return float(price)
    except:
        return None

def scrape_vegetable_prices():
    """Scrape vegetable prices and return as DataFrame"""
    url = "https://www.livechennai.com/Vegetable_price_chennai.asp"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'class': 'table table-bordered table-striped gold-rates'})
        
        data = []
        if table:
            for row in table.find_all('tr')[2:]:  # Skip header rows
                columns = row.find_all('td')
                if len(columns) >= 3:
                    vegetable_name = columns[1].text.strip()
                    price_range = columns[2].text.strip()
                    price = parse_price(price_range)
                    if price is not None:
                        data.append({
                            'Vegetable': vegetable_name,
                            'Price Range': price_range,
                            'Min Price': price
                        })
        
        return pd.DataFrame(data)
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()

def create_dashboard():
    """Create and configure the Dash dashboard"""
    app = dash.Dash(__name__)
    
    df = scrape_vegetable_prices()
    
    app.layout = html.Div([
        html.H1('Chennai Vegetable Price Dashboard',
                style={'textAlign': 'center', 'color': '#2c3e50', 'padding': '20px'}),
        
        html.Div([
            html.H3(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    style={'textAlign': 'center', 'color': '#7f8c8d'}),
            
            # Price range filter
            html.Div([
                html.Label('Filter by Price Range:'),
                dcc.RangeSlider(
                    id='price-filter',
                    min=df['Min Price'].min(),
                    max=df['Min Price'].max(),
                    value=[df['Min Price'].min(), df['Min Price'].max()],
                    marks={int(i): f'₹{i}' for i in range(
                        int(df['Min Price'].min()),
                        int(df['Min Price'].max()),
                        20
                    )},
                    step=5
                )
            ], style={'margin': '20px'}),
            
            # Charts
            html.Div([
                dcc.Graph(id='price-chart'),
                dcc.Graph(id='price-distribution')
            ], style={'display': 'flex', 'flexWrap': 'wrap'}),
            
            # Interactive Data Table
            html.Div([
                html.H3('Detailed Price List'),
                dash_table.DataTable(
                    id='price-table',
                    columns=[
                        {'name': 'Vegetable', 'id': 'Vegetable'},
                        {'name': 'Price Range', 'id': 'Price Range'},
                        {'name': 'Min Price (₹)', 'id': 'Min Price'}
                    ],
                    data=df.to_dict('records'),
                    sort_action='native',
                    filter_action='native',
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '10px',
                        'minWidth': '100px'
                    },
                    style_header={
                        'backgroundColor': '#2c3e50',
                        'color': 'white',
                        'fontWeight': 'bold'
                    }
                )
            ], style={'margin': '20px'})
        ])
    ])
    
    @app.callback(
        [Output('price-chart', 'figure'),
         Output('price-distribution', 'figure'),
         Output('price-table', 'data')],
        [Input('price-filter', 'value')]
    )
    def update_charts(price_range):
        filtered_df = df[
            (df['Min Price'] >= price_range[0]) &
            (df['Min Price'] <= price_range[1])
        ]
        
        # Bar chart
        bar_fig = px.bar(
            filtered_df,
            x='Vegetable',
            y='Min Price',
            title='Vegetable Prices',
            color='Min Price',
            color_continuous_scale='Viridis'
        )
        bar_fig.update_layout(
            xaxis_tickangle=-45,
            margin=dict(b=100)
        )
        
        # Distribution plot
        hist_fig = px.histogram(
            filtered_df,
            x='Min Price',
            title='Price Distribution',
            nbins=20
        )
        
        return bar_fig, hist_fig, filtered_df.to_dict('records')
    
    return app

if __name__ == '__main__':
    app = create_dashboard()
    app.run_server(debug=True)