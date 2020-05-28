# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd

################################## APP SETTING ###############################
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'Dash Testing'

server = app.server # the Flask app
################################## APP SETTING ###############################


################################### RAW PYTHON ###############################
df = pd.read_csv('https://gist.githubusercontent.com/chriddyp/c78bf172206ce24f77d6363a2d754b59/raw/c353e8ef842413cae56ae3920b8fd78468aa4cb2/usa-agricultural-exports-2011.csv')


def generate_table(dataframe, max_rows=10):
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in dataframe.columns])
        ),
        html.Tbody([
            html.Tr([
                html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
            ]) for i in range(min(len(dataframe), max_rows))
        ])
    ])
################################### RAW PYTHON ###############################
















################################## APP LAYOUT ###################################

app.layout = html.Div(children=[

    # titulo
    html.H2(children='Hello Dash'),

    html.Div(children='''
                          Dash: A web application framework for Python.
                      '''),

    # grafico de barras
    dcc.Graph(
        id='example-graph',
        figure={
            'data': [
                {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'SF'},
                {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'bar', 'name': u'Montréal'},
            ],
            'layout': { 'title': 'Dash Data Visualization' }
               }
    ),

    dcc.Dropdown(
        options=[
            {'label': 'New York City', 'value': 'NYC'},
            {'label': 'Montréal', 'value': 'MTL'},
            {'label': 'San Francisco', 'value': 'SF'}
        ],
        value='MTL'
    ),
    html.Div(children=[
        html.H4(children='US Agriculture Exports (2011)'),
        generate_table(df)
    ]),



# end of layout
])

if __name__ == '__main__':
    app.run_server(debug=True)