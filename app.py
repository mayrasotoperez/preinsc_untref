################################### IMPORTING ################################
# -*- coding: utf-8 -*-
import numpy as np ; import pandas as pd

import time ; import datetime
from datetime import date
from dateutil.relativedelta import relativedelta

import plotly.graph_objs as go
import psycopg2, psycopg2.extras

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input


#import xlsxwriter.utility as xls
#from xlsxwriter.utility import xl_rowcol_to_cell

################################### IMPORTING #################################


################################### CONSULTA DB ###############################

pre = pd.read_csv('consulta.csv', sep='|')

propuestas = list(pre.Carrera.unique())


pre.fillna('No informa', inplace=True)
pre = pre.sort_values(by='Fecha')
pre['cant'] = range(1,len(pre)+1)


siglas = pd.read_csv('assets/siglas.csv', sep='|', header=None)
siglas[2] = [siglas[0].iloc[i].split(' ')[0] for i in range(len(siglas))]

siglas = siglas.loc[siglas[0].isin(propuestas)]
siglas.reset_index(inplace=True,drop=True)

siglas_dic = {siglas[0].iloc[i]:siglas[1].iloc[i] for i in range(len(siglas))}
siglas_dic.update({'Total Institución': ''})

niveles = ['Total Institución','Curso', 'Doctorado', 'Diplomatura', 'Especialización', 'Maestría']


all_options = {}

for niv in niveles:
    cont = list(siglas.loc[siglas[2] == niv][0].unique())
    all_options.update({niv:cont})


################################### RAW PYTHON ###############################

trace_totales = go.Scatter()
trace_sexo = go.Bar()

data_sexo_dic = dict(pre['Sexo'].value_counts())

labels = ['Femenino','Masculino','No informa']
values = []

for i in labels:
    try:         value = data_sexo_dic[i]
    except:      value = 0
    values.append(value)


print('************************* DATA LISTA**************************************')
print(pre['Sexo'].value_counts())

################################### RAW PYTHON ###############################

################################## APP SETTING ###############################


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.title = 'Dash Testing'

server = app.server # the Flask app

################################## APP SETTING ###############################
################################## APP LAYOUT ################################
input_value = 'Total Institución'

app.layout = html.Div([

    # titulo
    html.Div([
        html.H2('Preinscripciones de Posgrados', className='eight columns'),
        html.Img(src='/assets/untref.jpg', className='four columns'),
    ], className='row'),
    html.Hr(className='linea'),

    dcc.RadioItems(
        id='nivel_elegido',
        options=[{'label': k, 'value': k} for k in all_options.keys()],
        value='Total Institución',
        labelStyle={'display': 'inline-block','margin-right':'15px'},
        className='niveles'
    ),

    #dcc.RadioItems(id='cities-radio'),
    html.Hr(className='linea'),

    html.Div([
        html.Label('Seleccione una propuesta',className='row'),
        dcc.Dropdown(options=[dict({'label': propuestas[i],
                                    'value': propuestas[i]})
                              for i in range(len(propuestas))],
                     id = 'carrera_elegida',
                     value='',
                     clearable=False,
                     ),

    ], className='row'),

    html.Div([
        html.H4(children='',
                id='subtitulo',
                className='twelve columns, carrera'
                ),
        html.P(
                id='subtitulo_sigla',
                className='two columns, sigla'
                ),
    ], className='row'),

    # Graficos
    html.Div([
        html.Div([
            dcc.Graph(
                id='graph_fechas',
            ),
        ],className="eight columns"),

    # SEXO
        html.Div([
            dcc.Graph(
                id='graph_sexo',
            ),
        ],className="four columns"),
    ],className="row"),

],className='cuerpo')
################################## APP LAYOUT ###################################
################################## CALL BACKS ###################################

@app.callback(
    Output('carrera_elegida', 'options'),
    [Input('nivel_elegido', 'value')])
def set_cities_options(selected_country):

    niveles_lst = [{'label': i, 'value': i} for i in all_options[selected_country]]

    niveles_lst.append({'label':'Total Institución','value':'Total Institución'})

    return niveles_lst


@app.callback(
    Output('carrera_elegida', 'value'),
    [Input('carrera_elegida', 'options')])
def set_cities_value(available_options):
    return available_options[0]['value']



@app.callback(
            [dash.dependencies.Output('subtitulo', 'children'),
             dash.dependencies.Output('subtitulo_sigla', 'children'),
             dash.dependencies.Output('graph_fechas', 'figure'),
             dash.dependencies.Output('graph_sexo', 'figure'),],

            [dash.dependencies.Input('carrera_elegida', 'value')])


def update_datos(input_value):

    if input_value == 'Total Institución':
        vista = pre[['Fecha','cant']].copy()
        layout_a = {'title': 'Inscripciones Totales'}

        vista_b = pre[['Sexo']].copy
        data_sexo_dic = dict(pre['Sexo'].value_counts())
        layout_b = {'title': 'Inscripciones Totales por Sexo'}

    else:
        vista = pre.loc[pre.Carrera == input_value][['Fecha','cant']].copy()
        vista['cant'] = range(1,len(vista)+1)

        layout_a = {'title': 'Detalle por fecha'}

        vista_b = pre.loc[pre.Carrera == input_value][['Sexo']].copy()
        data_sexo_dic = dict(vista_b['Sexo'].value_counts())
        layout_b = {'title': 'Detalle por sexo'}

    # GRAFICO DE FECHAS
    data_fechas = []
    trace_fechas = go.Scatter(x=list(vista.Fecha),
                             y=list(vista.cant),
                             name='fechas',
                             line=dict(color='#f44242'),
                             )
    data_fechas.append(trace_fechas)

    # GRAFICO DE SEXOS
    sex_labels = ['Femenino', 'Masculino', 'No informa']
    sex_values = []
    for i in sex_labels:
        try:
            value = data_sexo_dic[i]
        except:
            value = 0
        sex_values.append(value)

    data_sexo_lst = []
    trace_sexo = go.Bar(x=sex_labels,
                        y=sex_values,
                        name='sexos',
                        text=sex_values,
                        textposition='auto',
                        )
    data_sexo_lst.append(trace_sexo)

    if input_value == 'Total Institución':
        return [input_value,
                siglas_dic[input_value],
                {
                'data':data_fechas,
                'layout':layout_a,
                },
                {
                'data': data_sexo_lst,
                'layout': layout_b,
                }
                ]
    else:
        return [input_value,
                'Sigla: ' + siglas_dic[input_value],
                {
                    'data': data_fechas,
                    'layout': layout_a,
                },
                {
                    'data': data_sexo_lst,
                    'layout': layout_b,
                }
                ]

################################### APP LOOP ####################################
if __name__ == '__main__':
    app.run_server(debug=True)