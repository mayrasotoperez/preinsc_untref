##################################### IMPORTING ################################
# -*- coding: utf-8 -*-
import pandas as pd ; import assets.consulta as consulta ; import plotly.graph_objs as go
import dash
import dash_core_components as dcc ; import dash_html_components as html
import dash_table ; from dash.dependencies import Output, Input
import urllib ; import urllib.parse
##################################### IMPORTING ################################
#################################### CONSULTA DB ###############################

totales,dic_sigla_nom = consulta.consulta_db()

totales.fecha_insc.fillna(0,inplace=True)

pre = totales.loc[totales.propuesta != 'Sin Propuesta']
pre['cant'] = [i+1 for i in range(len(pre))]
dic_nom_sigla = {pre.propuesta.iloc[i]: pre.sigla.iloc[i] for i in range(len(pre))}
dic_nom_sigla.update({'Total Institución': ''})


#################################### CONSULTA DB ###############################
################################### TABLAS DATOS ###############################
propuestas_lst = list(pre.propuesta.unique())
propuestas_lst.sort()

dic_sigla_nom.update({'Total Institución': ''})
siglas = pd.DataFrame([dic_sigla_nom.keys(),dic_sigla_nom.values()]).T

siglas.columns = ['sigla','propuesta']
siglas = siglas.loc[siglas.sigla.isin(dic_nom_sigla.values())]
siglas['nivel'] = [siglas.propuesta.iloc[i].split(' ')[0] for i in range(len(siglas))]


niveles = ['Total Institución','Curso', 'Doctorado', 'Diplomatura', 'Especialización', 'Maestría']


all_options = {}

for niv in niveles:
    cont = list(siglas.loc[siglas['nivel'] == niv]['propuesta'].unique())
    all_options.update({niv:cont})



################################### RAW PYTHON ###############################

trace_totales = go.Scatter()
trace_estado = go.Bar()

data_estado_dic = dict(totales['estado'].value_counts())

labels = ['Pendiente','Activo','Potencial','Inscripto']
values = []

for i in labels:
    try:         value = data_estado_dic[i]
    except:      value = 0
    values.append(value)

tabla_a = pre.copy()

dic_columns = {'fecha_preinscripcion': 'Fecha',
               'nivel': 'Nivel',
               'propuesta': 'Carrera',
               'ape': 'Apellido/s',
               'nom': 'Nombre/s',
               'nacionalidad': 'Nacionalidad',
               'edad': 'Edad',
               'nro_doc': 'Nro. Documento',
               'sexo': 'Sexo',
               'celular': 'Nro. Celular',
               'e_mail': 'e-Mail',
               'cant': 'Cantidad',
               'estado':'Estado',
               'Pendiente':'Pendientes',
               'Activo':'Activos',
               'Potencial':'Potenciales',
               'Inscripto':'Inscriptos',
               'Totales':'Totales'
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
import assets.entry_text as welcome

app.layout = html.Div([
    # HEADER
    html.Div(className='row',
             children=[
                 html.H2('Preinscripciones de Posgrado', className='eight columns'),
                 html.Img(src='/assets/untref_logo.jpg', className='four columns'),
                 ]
             ),

    html.Div(className='row',
             hidden=False,
             children=[
                 html.Label('Ingrese la contraseña:', className='three columns',style={'margin-top': '7px',
                                                                                       }),
                 dcc.Input(id='password',
                           type='password',
                           className='two columns',
                           autoFocus=True,
                           style = {#'margin-top': '100px',
                                    'margin-left': '-5%'}
                           ),
                 ]
             ),

    html.Hr(className='linea'),

    html.Div(id='password_valid',
             hidden=True,
             children=[
                # welcome DIV
                html.Div([
                    html.Div([\
                        html.P(welcome.welcome.split('#')[i], className='texto_intro') for i in range(len(welcome.welcome.split('#')))\
                    ], className='twelve columns'),
                    html.Div([ \
                        html.P(welcome.welcome_tags.split('#')[i], className='texto_intro') for i in
                        range(len(welcome.welcome_tags.split('#'))) \
                        ], className='eight columns'),
                ], className='row'),

                html.Hr(className='linea'),
                # SELECCION DE NIVEL
                html.Div([
                    html.Label('Seleccione un nivel:', className='row'),
                    dcc.RadioItems(
                        id='nivel_elegido',
                        options=[{'label': k, 'value': k} for k in all_options.keys()],
                        value='Total Institución',
                        labelStyle={'display': 'inline-block', 'margin-right':'15px'},
                        className='niveles'),
                    html.Hr(className='linea'),
                ], className='row'),

                # DROPDOWN CARRERAS X NIVEL
                html.Div([
                    html.Label('Seleccione una propuesta:', className='row'),
                    dcc.Dropdown(options=[dict({'label': propuestas_lst[i],
                                                'value': propuestas_lst[i]})
                                          for i in range(len(propuestas_lst))],
                                 id = 'carrera_elegida',
                                 value='',
                                 clearable=False),
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

                # graphs DIV
                html.Div([
                    # SCATTER PLOT
                    html.Div([
                        dcc.Graph(
                            id='graph_fechas',
                            style={'height':400},
                            responsive=True),
                    ],className="seven columns"),
                    # GRAFICO DE BARRAS
                    html.Div([
                        dcc.Graph(
                            id='graph_sexo',
                            style={'height':400}),
                    ],className="five columns"),
                ],className="row"),

                # BOTON DE DESCARGA
                html.A(
                    'Descargar tabla',
                    id='download-link',
                    download="tabla-preinscriptos.csv",
                    href="",
                    target="_blank",
                ),html.P('(formato CSV)',className='span'),

                # DROPDOWN CARRERAS X NIVEL
                html.Div([
                    html.Label('Seleccione un nivel:', className='row'),
                    dcc.Dropdown(options=[dict({'label': niveles[i], 'value': niveles[i]})
                                          for i in range(len(niveles))],
                                 id='nivel_elegido_home',
                                 value='',
                                 clearable=False,
                                 disabled=True,
                                 ),
                ],id='selector_nivel',hidden=True, className='row'),

                # TABLA DE DATOS
                dash_table.DataTable(
                    id='tabla-datos',
                    sort_action='native',
                    style_data_conditional=[
                            {
                                'if': {
                                    'filter_query': '{estado} = Inscripto',
                                },
                                'backgroundColor': '#008a5a',
                                'color': 'white'
                            },]
                ),
    ])
],className='cuerpo')

################################## APP LAYOUT ###################################
################################## CALL BACKS ###################################

@app.callback(
    Output('password_valid','hidden'),
    [Input('password','value')])
def password(password):
    password_key = 'Un7r3f_2020'

    if password == password_key:
        return False
    else:
        return True

@app.callback(
    Output('carrera_elegida', 'options'),
    [Input('nivel_elegido', 'value')])
def set_nivel(selected_carrera):
    level_set = all_options[selected_carrera]
    level_set.sort()

    niveles_lst = [{'label': i, 'value': i} for i in level_set]
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
        layout_a = {'title': 'Preinscripciones Totales'}

        # TABLA
        tabla = totales[['nivel','propuesta','estado']].copy()

        tabla = pd.concat([tabla.drop('estado', axis=1), pd.get_dummies(tabla.estado)], axis=1)
        tabla = tabla.groupby(['nivel', 'propuesta']).sum()
        tabla.reset_index(inplace=True)

        tabla['Totales'] = tabla.sum(axis=1)
        tabla = tabla.loc[tabla.nivel != 'Sin Propuesta']
        tabla = tabla.sort_values(by='Totales', ascending=False)
        tabla = tabla[['nivel', 'propuesta', 'Activo', 'Potencial', 'Inscripto', 'Totales']]

        vista_b = pre.copy()
        data_estado_dic = dict(totales['estado'].value_counts())
        layout_b = {'title': 'Inscripciones Totales por estado'}

        estado_labels = ['Pendiente', 'Activo', 'Potencial', 'Inscripto']

    # PARA PANTALLA de CADA CARRERA
    else:
        vista = pre.loc[pre.propuesta == input_value][['fecha_preinscripcion','estado','cant','fecha_insc']].copy()
        vista['cant'] = range(1,len(vista)+1)
        tabla = pre.loc[pre.propuesta == input_value][['fecha_preinscripcion','ape','nom','nacionalidad','edad',
                                                       'nro_doc','sexo','e_mail','estado']].copy() # agregar 'celular' en produccion

        layout_a = {'title': 'Preinscriptos por fecha'}

        vista_b = pre.loc[pre.propuesta == input_value][['estado']].copy()
        data_estado_dic = dict(vista_b['estado'].value_counts())
        layout_b = {'title': 'Preinscriptos por estado'}

        estado_labels = ['Activo', 'Potencial', 'Inscripto']

    # GRAFICO DE FECHAS
    colors = {'tot_pos' : '#bbbbbb',
              'poten' : '#000e75',
              'insc' : '#008a5a',
              'pend' : '#8f2806',
              'act' : '#06848f'}


    data_fechas_lst = []
    trace_fechas = go.Scatter(x=list(vista.loc[vista.estado.isin(['Potencial','Inscripto'])].fecha_preinscripcion),
                              y=list(vista.cant), name='Totales Posibles', line=dict(color=colors['tot_pos']),
                              )
    trace_fechas_3 = go.Scatter(x=list(vista.loc[vista.estado == 'Potencial'].fecha_preinscripcion),
                              y=list(vista.cant), name='Potenciales', line=dict(color=colors['poten']),
                              )
    trace_fechas_2 = go.Scatter(x=list(vista.loc[vista.estado == 'Inscripto'].fecha_insc.sort_values()),
                              y=list(vista.cant), name='Inscriptos Actuales', line=dict(color=colors['insc']),
                              )

    data_fechas_lst.append(trace_fechas)
    data_fechas_lst.append(trace_fechas_3)
    data_fechas_lst.append(trace_fechas_2)

    # GRAFICO DE ESTADOS

    estado_values = []
    for i in estado_labels:
        try:
            value = data_estado_dic[i]
        except:
            value = 0
        estado_values.append(value)

    data_estado_lst = []


    if input_value == 'Total Institución':
        trace_estado = go.Bar(x=estado_labels, y=estado_values, name='sexos',
                              text=estado_values, textposition='auto',
                              marker_color = [colors['pend'],colors['act'],colors['poten'],colors['insc']] )
    else:
        trace_estado = go.Bar(x=estado_labels, y=estado_values, name='sexos',
                              text=estado_values, textposition='auto',
                              marker_color = [colors['act'],colors['poten'],colors['insc']] )

    data_estado_lst.append(trace_estado)

    try:
        tabla.fecha_preinscripcion = pd.DatetimeIndex(tabla.fecha_preinscripcion).strftime("%d/%m/%Y")
    except:
        pass

    # FILE EXPORTING
    csv_string = tabla.to_csv(index=False, encoding='Latin-1')
    csv_string = "data:text/csv;charset=Latin-1," + urllib.parse.quote(csv_string)

    if input_value == 'Total Institución':
        return [input_value,
                dic_nom_sigla[input_value],
                {
                'data':data_fechas_lst,
                'layout':layout_a,
                },
                {
                'data': data_estado_lst,
                'layout': layout_b,
                },
                tabla.to_dict('records'),
                [{"name": dic_columns[i], "id": i} for i in tabla.columns],
                csv_string
                ]
    else:
        return [input_value,
                'Sigla: ' + dic_nom_sigla[input_value],
                {
                    'data': data_fechas_lst,
                    'layout': layout_a,
                },
                {
                    'data': data_estado_lst,
                    'layout': layout_b,
                },
                tabla.to_dict('records'),
                [{"name": dic_columns[i], "id": i} for i in tabla.columns],
                csv_string
                ]




################################### APP LOOP ####################################
if __name__ == '__main__':
    app.run_server(debug=True)
