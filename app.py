##################################### IMPORTING ################################
# -*- coding: utf-8 -*-
import numpy as np ; import pandas as pd
import time ; import datetime ; from datetime import date
import plotly.graph_objs as go

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Output, Input

import urllib
import urllib.parse
import openpyxl

#import xlsxwriter.utility as xls
#from xlsxwriter.utility import xl_rowcol_to_cell
##################################### IMPORTING ################################
#################################### CONSULTA DB ###############################
import consulta
pre = consulta.consulta_db()

pre['cant'] = [i+1 for i in range(len(pre))]


#################################### CONSULTA DB ###############################
################################### TABLAS DATOS ###############################
propuestas_lst = list(pre.carrera.unique())
propuestas_lst.sort()


siglas = pd.read_csv('assets/siglas.csv', sep='|', header=None)
siglas[2] = [siglas[0].iloc[i].split(' ')[0] for i in range(len(siglas))]

siglas = siglas.loc[siglas[0].isin(propuestas_lst)]
siglas = siglas.sort_values(by=0)
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

data_sexo_dic = dict(pre['sexo'].value_counts())

labels = ['Femenino','Masculino','No informa']
values = []

for i in labels:
    try:         value = data_sexo_dic[i]
    except:      value = 0
    values.append(value)

tabla_a = pre.copy()
dic_columns = {'fecha': 'Fecha',
               'nivel': 'Nivel',
               'carrera': 'Carrera',
               'ape': 'Apellido/s',
               'nom': 'Nombre/s',
               'nac': 'Nacionalidad',
               'edad': 'Edad',
               'tipo_doc': 'Tipo Documento',
               'nro_doc': 'Nro. Documento',
               'sexo': 'Sexo',
               'celular': 'Nro. Celular',
               'e_mail': 'e-Mail',
               'cant': 'Cantidad',
               }
################################### RAW PYTHON ###############################
################################## APP SETTING ###############################

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.title = 'Inscripciones de POSGRADOS'

server = app.server # the Flask app

################################## APP SETTING ###############################
def generate_table(dataframe, max_rows=100):
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
################################## APP LAYOUT ################################
input_value = 'Total Institución'

app.layout = html.Div([
    html.Div([
        html.H2('Preinscripciones de Posgrados', className='eight columns'),
        html.Img(src='/assets/untref.jpg', className='four columns'),
    ], className='row'),
    html.Hr(className='linea'),

    # SELECCION DE NIVEL
    dcc.RadioItems(
        id='nivel_elegido',
        options=[{'label': k, 'value': k} for k in all_options.keys()],
        value='Total Institución',
        labelStyle={'display': 'inline-block', 'margin-right':'15px'},
        className='niveles'
    ),
    html.Hr(className='linea'),

    # DROPDOWN CARRERAS X NIVEL
    html.Div([
        html.Label('Seleccione una propuesta:', className='row'),
        dcc.Dropdown(options=[dict({'label': propuestas_lst[i],
                                    'value': propuestas_lst[i]})
                              for i in range(len(propuestas_lst))],
                     id = 'carrera_elegida',
                     value='',
                     clearable=False,
                     ),
    ], className='row'),

    # CUERPO POR NIVEL
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

    # GRAFICOS
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

    # BOTON DE DESCARGA
    html.A(
        'Descargar tabla',
        id='download-link',
        download="tabla-preinscriptos.csv",
        href="",
        target="_blank",
    ),html.P('(formato CSV)',className='span'),

    # TABLA DE DATOS
    dash_table.DataTable(
        id='tabla-datos',

    ),

],className='cuerpo')



################################## APP LAYOUT ###################################
################################## CALL BACKS ###################################

@app.callback(
    Output('carrera_elegida', 'options'),
    [Input('nivel_elegido', 'value')])
def set_nivel(selected_carrera):
    niveles_lst = [{'label': i, 'value': i} for i in all_options[selected_carrera]]
    niveles_lst.append({'label': 'Total Institución', 'value': 'Total Institución'})
    return niveles_lst

@app.callback(
    Output('carrera_elegida', 'value'),
    [Input('carrera_elegida', 'options')])
def set_carreras(available_options):
    return available_options[0]['value']

@app.callback(
            [dash.dependencies.Output('subtitulo', 'children'),
             dash.dependencies.Output('subtitulo_sigla', 'children'),
             dash.dependencies.Output('graph_fechas', 'figure'),
             dash.dependencies.Output('graph_sexo', 'figure'),
             dash.dependencies.Output('tabla-datos', 'data'),
             dash.dependencies.Output('tabla-datos', 'columns'),
             dash.dependencies.Output('download-link', 'href'),
             ],
            [dash.dependencies.Input('carrera_elegida', 'value')])

def update_datos(input_value):

    # PARA LA PANTALLA INICIAL
    if input_value == 'Total Institución':
        vista = pre.copy()
        layout_a = {'title': 'Inscripciones Totales'}
        tabla = pre[['nivel','carrera']].copy()
        tabla['cant'] = 1
        tabla = tabla.groupby('carrera').sum()
        tabla.reset_index(inplace=True)

        vista_b = pre.copy
        data_sexo_dic = dict(pre['sexo'].value_counts())
        layout_b = {'title': 'Inscripciones Totales por sexo'}

    # PARA CADA CARRERA
    else:
        vista = pre.loc[pre.carrera == input_value][['fecha','cant']].copy()
        vista['cant'] = range(1,len(vista)+1)
        tabla = pre.loc[pre.carrera == input_value][['fecha','ape','nom','nac','edad','tipo_doc','nro_doc','sexo']].copy() # agregar 'celular','e_mail' en produccion

        layout_a = {'title': 'Detalle por fecha'}

        vista_b = pre.loc[pre.carrera == input_value][['sexo']].copy()
        data_sexo_dic = dict(vista_b['sexo'].value_counts())
        layout_b = {'title': 'Detalle por sexo'}

    # GRAFICO DE FECHAS
    data_fechas_lst = []
    trace_fechas = go.Scatter(x=list(vista.fecha),
                              y=list(vista.cant),
                              name='fechas',
                              line=dict(color='#f44242'),
                              )
    data_fechas_lst.append(trace_fechas)

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

    try:
        tabla.fecha = pd.DatetimeIndex(tabla.fecha).strftime("%d/%m/%Y")
    except:
        pass

    # FILE EXPORTING
    csv_string = tabla.to_csv(index=False, encoding='Latin-1')
    csv_string = "data:text/csv;charset=Latin-1," + urllib.parse.quote(csv_string)

    if input_value == 'Total Institución':
        return [input_value,
                siglas_dic[input_value],
                {
                'data':data_fechas_lst,
                'layout':layout_a,
                },
                {
                'data': data_sexo_lst,
                'layout': layout_b,
                },
                tabla.to_dict('records'),
                [{"name": dic_columns[i], "id": i} for i in tabla.columns],
                csv_string
                ]
    else:
        return [input_value,
                'Sigla: ' + siglas_dic[input_value],
                {
                    'data': data_fechas_lst,
                    'layout': layout_a,
                },
                {
                    'data': data_sexo_lst,
                    'layout': layout_b,
                },
                tabla.to_dict('records'),
                [{"name": dic_columns[i], "id": i} for i in tabla.columns],
                csv_string
                ]


################################### APP LOOP ####################################
if __name__ == '__main__':
    app.run_server(debug=True)
