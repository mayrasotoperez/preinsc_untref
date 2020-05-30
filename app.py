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

################################### IMPORTING ################################

################################### CONSULTA DB ###############################

# nos conectamos a la base de preinscripcion
conn = psycopg2.connect(database='preinscripcion390posgrado', user='postgres', password='uNTreF2019!!',
                        host='170.210.45.210')
# testing corto, si imprime funciona...
cur = conn.cursor()
cur.execute('''SELECT id_preinscripcion, version_modificacion, version_impresa, usuario, apellido, nombres, nacionalidad, tipo_documento, nro_documento, sexo, 
                       fecha_nacimiento, alu_otestsup_uni, alu_otestsup_carr, celular_numero, estado_civil, e_mail, estado
                FROM public.sga_preinscripcion''')
rows = cur.fetchall()
sga_pre = pd.DataFrame(rows)
# print (rows)
sga_pre.columns = ['id_preinscripcion', 'version_modificacion', 'version_impresa', 'usuario', 'apellido', 'nombres',
                   'nacionalidad', 'tipo_documento', 'nro_documento', 'sexo', 'fecha_nacimiento', 'alu_otestsup_uni',
                   'alu_otestsup_carr', 'celular_numero', 'estado_civil', 'e_mail', 'estado']
# sga_preinscripcion_propuestas
# nos conectamos a la base de preinscripcion
conn = psycopg2.connect(database='preinscripcion390posgrado', user='postgres', password='uNTreF2019!!',
                        host='170.210.45.210')
# testing corto, si imprime funciona...
cur = conn.cursor()
cur.execute('''SELECT preinscripcion_propuesta, id_preinscripcion, propuesta, fecha_preinscripcion
                FROM public.sga_preinscripcion_propuestas''')
rows = cur.fetchall()
sga_prepro = pd.DataFrame(rows)
sga_prepro.columns = ['preinscripcion_propuesta', 'id_preinscripcion', 'propuesta', 'fecha_preinscripcion']
# sga_propuestas
# nos conectamos a la base de preinscripcion
conn = psycopg2.connect(database='guarani3162posgrado', user='postgres', password='uNTreF2019!!', host='170.210.45.210')
# testing corto, si imprime funciona...
cur = conn.cursor()
cur.execute('''SELECT propuesta, nombre, nombre_abreviado, codigo
                FROM negocio.sga_propuestas''')
rows = cur.fetchall()
sga_pro = pd.DataFrame(rows)
sga_pro.columns = ['propuesta', 'nombre', 'nombre_abreviado', 'codigo']

# cerrar siempre la conexion por las dudas...
conn.close()

# ---------------------------------------------------------------------------------
################################### MERGING ######################################

dic_prop_names = {sga_pro.propuesta.iloc[i]: sga_pro.nombre.iloc[i] for i in range(len(sga_pro))}
dic_prop_sigla = {sga_pro.propuesta.iloc[i]: sga_pro.nombre_abreviado.iloc[i] for i in range(len(sga_pro))}
sga_prepro['carrera'] = sga_prepro.propuesta.map(dic_prop_names)

preinscriptos = pd.merge(sga_prepro, sga_pre)[
    ['fecha_preinscripcion', 'carrera', 'apellido', 'nombres', 'nacionalidad', 'tipo_documento',
     'nro_documento', 'sexo', 'fecha_nacimiento', 'celular_numero', 'e_mail']]
# ---------------------------------------------------------------------------------
################################ MANAGING DATA ###################################
preinscriptos.sort_values(['carrera', 'fecha_preinscripcion'], ascending=True, inplace=True)
preinscriptos.reset_index(inplace=True, drop=True)

#### Formato Fechas de preinscripcion
preinscriptos['fecha_preinscripcion'] = [preinscriptos.fecha_preinscripcion.iloc[x].date().__format__('%d-%m-%Y') for x
                                         in range(len(preinscriptos))]
preinscriptos['fecha_preinscripcion'] = [
    datetime.datetime.strptime(preinscriptos.fecha_preinscripcion.iloc[x], '%d-%m-%Y') for x in
    range(len(preinscriptos))]


#### De fecha a edad
def calculate_age(born):
    today = datetime.date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


preinscriptos['edad'] = ''
for i in range(len(preinscriptos)):
    try:
        preinscriptos.loc[i, 'edad'] = calculate_age(preinscriptos.fecha_nacimiento.iloc[i])
    except:
        preinscriptos.loc[i, 'edad'] = 'No informa'

#### pais DOC
pais_dic = {1: 'Argentino', 2: 'Extranjero', 3: 'Naturalizado', 4: 'Por Opción'}
preinscriptos['nacionalidad'] = preinscriptos.nacionalidad.map(pais_dic)

#### Tipo DOC
names = ['id', 'doc', 'sigla', 'a', 'b', 'c', 'd', 'e', 'f']
docus = pd.read_csv('mdp_tipo_documento.csv', sep='|', index_col=None, names=names)
docu_dic = {docus.id.iloc[i]: docus.sigla.iloc[i] for i in range(len(docus))}
preinscriptos['tipo_documento'] = preinscriptos.tipo_documento.map(docu_dic)
#### Sexo
preinscriptos.sexo.fillna('0', inplace=True)
sex_dic = {'0': 'No informa',
           '1': 'Masculino',
           '2': 'Femenino'}
preinscriptos['sexo'] = preinscriptos.sexo.map(sex_dic)

# ---------------------------------------------------------------------------------
############################## COLUMNAS FINALES ##################################
pre = preinscriptos[['fecha_preinscripcion', 'carrera', 'apellido', 'nombres',
                     'nacionalidad', 'edad', 'tipo_documento', 'nro_documento',
                     'sexo', 'celular_numero', 'e_mail']]

pre.columns = ['Fecha', 'Carrera', 'Apellidos', 'Nombres', 'Nacionalidad', 'Edad', 'Doc. tipo',
               'Doc. número', 'Sexo', 'Celular', 'e_mail']

propuestas = list(pre.Carrera.unique())
#propuestas.sort()


pre.fillna('No informa', inplace=True)
#propuestas.append('')

#pre = pre.loc[pre.Carrera == 'Maestría en Periodismo Documental']
################################### CONSULTA DB ###############################



pre.sort_values(by='Fecha',inplace=True)

pre['cant'] = range(1,len(pre)+1)


################################### RAW PYTHON ###############################

trace_close2 = go.Bar(x=list(pre.Fecha),
                     y=list(pre.index),
                     name='Close',
                     #line=dict(color='#f44242')
                     )
data2 = [trace_close2]


# layout = dict(title='Crecimiento de Preinscripciones',
#               showlegend=False
#               )
# fig = dict(data=data, layout=layout)


################################### RAW PYTHON ###############################
################################## APP SETTING ###############################


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.title = 'Dash Testing'

server = app.server # the Flask app

################################## APP SETTING ###############################
################################## APP LAYOUT ################################


app.layout = html.Div([

    # titulo
    html.Div([
        html.H2('Preinscripciones de Posgrados',className='eight columns'),
        html.Img(src='/assets/untref.jpg',className='four columns'),
    ], className='row'),


    html.Div([
        html.Label('Seleccione una propuesta',className='row'),
        dcc.Dropdown(options=[dict({'label': propuestas[i],
                                    'value': propuestas[i]})
                              for i in range(len(propuestas))],
                     id = 'carrera_elegida',
                     value='',
                     ),

    ], className='row'),

    # html.Div(
    #     dcc.Graph(id='Stock Chart',
    #               figure=fig)
    # ),

    html.Div([
        html.Div([
            dcc.Graph(
                id='graph_close',
            ),
        ],className="ten columns"),

        # segundo grafico
        # html.Div([
        #     dcc.Graph(
        #         id='graph_close-1',
        #         figure={
        #             'data': data2,
        #             'layout': {
        #                 'title': 'Close Graph'
        #             }
        #         }
        #     ),
        # ],className="six columns"),
    ],className="row"),

    # html.Div(
    #     dcc.Input(
    #         id='stock-input',
    #         placeholder='Enter a Stock to be charted',
    #         type='text',
    #         value='',
    #     ),
    # ),


])
################################## APP LAYOUT ###################################
################################## CALL BACKS ###################################

@app.callback(dash.dependencies.Output("graph_close",'figure'),
             [dash.dependencies.Input("carrera_elegida",'value')]
             )


def update_fig(input_value):

    if input_value == '':

        vista = pre.copy()
    else:
        vista = pre.loc[pre.Carrera == input_value]
        vista['cant'] = range(1,len(vista)+1)

    data = []
    trace_close = go.Scatter(x=list(vista.Fecha),
                             y=list(vista.cant),
                             name='Close',
                             line=dict(color='#f44242'),

                             )
    data.append(trace_close)

    layout = {'title':input_value}

    return {
        'data':data,
        'layout':layout
    }



################################### APP LOOP ####################################
if __name__ == '__main__':
    app.run_server(debug=True)