##################################### IMPORTING ################################
# -*- coding: utf-8 -*-
# importamos las librerias que implementaremos
import pandas as pd;
import base64;
import io
import plotly.graph_objs as go
import dash;
import dash_table;
from dash.dependencies import Output, Input
import dash_core_components as dcc;
import dash_html_components as html
# ademas importamos la funcion de consulta.py que ejecuta las querys SQL
import assets.consulta as consulta;
# de welcome traemos los textos
import assets.entry_text as welcome
import datetime as dt

##################################### IMPORTING ################################
#################################### CONSULTA DB ###############################

# instanciamos en totales todos los datos de preinscriptos y tambien guardamos un diccionario con nombres y siglas de propuestas
totales, dic_sigla_nom = consulta.consulta_db()
dic_sigla_nom.update({'Total Institución': ''})

#################################### CONSULTA DB ###############################
#################################### RAW PYTHON  ###############################

# completamos valores faltantes con 0
totales.fecha_insc.fillna(0, inplace=True)

# en pre filtraremos de totales la propuesta elegida
pre = totales.loc[totales.propuesta != 'Sin Propuesta'].copy()
# cant guardará la frecuencia
pre['cant'] = [i + 1 for i in range(len(pre))]
# necesitaremos el diccionario de siglas y propuestas pero inverso
dic_nom_sigla = {pre.propuesta.iloc[i]: pre.sigla.iloc[i] for i in range(len(pre))}
# al cual agregamos "total institucion como una key
dic_nom_sigla.update({'Total Institución': ''})

# establecemos y ordenamos una lista de propuestas disponibles para seleccionar
propuestas_lst = list(pre.propuesta.unique())
propuestas_lst.sort()

# armamos un df con siglas y nombres para poder trabajarlos
siglas = pd.DataFrame([dic_sigla_nom.keys(), dic_sigla_nom.values()]).T
siglas.columns = ['sigla', 'propuesta']
siglas = siglas.loc[siglas.sigla.isin(dic_nom_sigla.values())].copy()
# extraemos el nivel del nombre de la propuesta
siglas['nivel'] = [siglas.propuesta.iloc[i].split(' ')[0] for i in range(len(siglas))]

# hardcodeamos la lista de niveles, esto no se modificará nunca
niveles = ['Total Institución', 'Curso', 'Doctorado', 'Diplomatura', 'Especialización', 'Maestría']

# creamos un diccionario de niveles y propuestas por cada nivel
all_options = {}
for niv in niveles:
    cont = list(siglas.loc[siglas['nivel'] == niv]['propuesta'].unique())
    all_options.update({niv: cont})

# generamos los marcos para los graficos de fechas y estados
trace_totales = go.Scatter()
trace_estado = go.Bar()

# generamos un dic con los estados posibles
data_estado_dic = dict(totales['estado'].value_counts())

# los estados nunca cambiarán
labels = ['Pendiente', 'Activo', 'Potencial', 'Inscripto']
values = []
for i in labels:
    try:
        value = data_estado_dic[i]
    except:
        value = 0
    values.append(value)

# para la pantalla inicial
tabla_a = pre.copy()

# trazamos equivalencias entre el nombre de la columna y el nombre que imprimirá, para facilitar la lectura al usuario
dic_columns = {'fecha_preinscripcion': 'Fecha', 'nivel': 'Nivel', 'propuesta': 'Carrera', 'ape': 'Apellido/s',
               'nom': 'Nombre/s', 'nacionalidad': 'Nacionalidad', 'edad': 'Edad', 'nro_doc': 'Nro. Documento',
               'sexo': 'Sexo', 'celular': 'Nro. Celular', 'e_mail': 'e-Mail', 'cant': 'Cantidad', 'estado': 'Estado',
               'Pendiente': 'Pendientes', 'Activo': 'Activos', 'Potencial': 'Potenciales', 'Inscripto': 'Inscriptos',
               'Totales': 'Totales'
               }


# armamos una funcion que nos organice la tabla de resultados
def generate_table(dataframe, max_rows=100):
    return html.Table([
        html.Thead(html.Tr([html.Th(col) for col in dataframe.columns])),
        html.Tbody([
            html.Tr([html.Td(dataframe.iloc[i][col]) for col in dataframe.columns]) for i in
            range(min(len(dataframe), max_rows))
        ])])


################################### RAW PYTHON ###############################
################################## APP SETTING ###############################
# seteamos la url del ccs
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
# instanciamos la app
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
# le definimos un título
app.title = 'Inscripciones de POSGRADOS'
# instanciamos el servidor
server = app.server  # the Flask app

################################## APP SETTING ###############################
################################## APP LAYOUT ################################
# seteamos como valor inicial "Total Institución" para que se pueda comenzar a visualizar sin haber elegido propuesta alguna
input_value = 'Total Institución'

# comenzamos a organizar la app
app.layout = html.Div([
    # creamos un HEADER con el título y logo
    html.Div(className='row',
             children=[
                 html.H2('Preinscripciones de Posgrado', className='eight columns'),
                 html.Img(src='/assets/untref_logo.jpg',
                          className='four columns',
                          style={'margin-top': '22px'}),
             ]
             ),
    # agregamos un Input donde se debe ingresar la contraseña para desbloquear la app
    html.Div(className='row',
             hidden=False,
             children=[
                 html.Label('Ingrese la contraseña:', className='three columns', style={'margin-top': '7px'}),
                 dcc.Input(id='password',
                           type='password',
                           className='two columns',
                           autoFocus=True,
                           style={'margin-left': '-5%'},
                           #value='limon2015',
                           ),
             ]
             ),
    html.Hr(className='linea'),

    # si se ingresa la contraseña correcta, el atributo hidden del siguiente div pasa a False para mostrar toda la app
    html.Div(id='password_valid',
             hidden=True,
             children=[
                 # welcome DIV nos muestra los textos explicativos de intro y estados
                 html.Div(className='row',
                          style={'margin-left': '8%', 'margin-right': '8%', 'background-color': '#eeeeee',
                                 'border-radius': '10px', 'padding': '20px'},
                          children=[
                              html.Div(className='six columns',
                                       children=[
                                           html.Label(children='Introducción:',
                                                      className='row',
                                                      style={'margin-bottom': '10px'}, ),
                                           dcc.Markdown(className='texto_intro',
                                                        children='''En los datos de preinscriptos podemos encontrar diferentes niveles de _"intención"_ de concretar una inscripción.
                                                                    Dado que una persona podría haber generado su usuario, completar sus datos e incluso imprimir el formulario,
                                                                    pero finalmente no concurrir en ningún momento a la institución.'''),
                                           dcc.Markdown(className='texto_intro',
                                                        children='''Valuaremos la intención de efectivamente inscribirse a un posgrado en base a haber validado un usuario 
                                                                    de preinscripción, tener una propuesta formativa seleccionada y tener impreso la última versión de su 
                                                                    formulario de preinscripción.''')
                                       ],
                                       ),
                              html.Div(className='six columns',
                                       children=[
                                           html.Label(children='Definición de estados:',
                                                      className='row',
                                                      style={'margin-bottom': '10px'}, ),
                                           dcc.Markdown(className='texto_intro',
                                                        style={'margin-bottom': '4px'},
                                                        children=[welcome.welcome_tags.split('#')[i] for i in
                                                                  range(len(welcome.welcome_tags.split('#')))]
                                                        )
                                       ]
                                       ),
                          ]
                          ),

                 # mediante RadioButtons realizamos la SELECCION DE NIVEL como primer filtro
                 html.Div(className='row',
                          children=[
                              html.Label(children='Seleccione un nivel:',
                                         className='row',
                                         style={'margin-top': '20px'}, ),
                              dcc.RadioItems(
                                  id='nivel_elegido',
                                  className='niveles',
                                  options=[{'label': k, 'value': k} for k in all_options.keys()],
                                  value='Total Institución',
                                  labelStyle={'display': 'inline-block', 'margin-right': '15px'},
                              ),
                              html.Hr(className='linea'),
                          ]
                          ),

                 # mediante DROPDOWN CARRERAS X NIVEL realizamos el segundo filtro
                 html.Div(className='row',
                          children=[
                              html.Label(className='row',
                                         children='Seleccione una propuesta:'),
                              dcc.Dropdown(id='carrera_elegida',
                                           options=[dict({'label': propuestas_lst[i], 'value': propuestas_lst[i]}) for i
                                                    in range(len(propuestas_lst))],
                                           value='',
                                           clearable=False
                                           ),
                          ]
                          ),

                 # Una vez seleccionada la carrera, dispondremos la info en el "HEADER"
                 html.Div(className='row',
                          children=[
                              # aqui establecemos el título, que será la carreram, y la sigla para empezar a impregnar este dato en el usuario.
                              html.H4(children='',
                                      id='subtitulo',
                                      className='twelve columns, carrera'),
                              html.P(id='subtitulo_sigla',
                                     className='two columns, sigla'),
                          ]
                          ),

                 # Generamos un DIV para los gráficos
                 html.Div(className="row",
                          children=[
                              # SCATTER PLOT
                              html.Div(
                                  className="seven columns",
                                  children=[
                                      dcc.Graph(
                                          id='graph_fechas',
                                          style={
                                                 'height':'400px'}
                                          ),
                                      ],
                                  ),

                              # GRAFICO DE BARRAS
                              html.Div(
                                  className="five columns",
                                  children=[
                                      dcc.Graph(
                                          id='graph_sexo',
                                          style={
                                                 'height':'400px'}
                                          ),
                                      ],
                                  ),
                              ]
                          ),

                 # BOTON DE DESCARGA
                 html.A(
                     children='Descargar tabla',
                     id='download-link',
                     download="tabla-preinscriptos.xlsx",
                     href="",
                     target="_blank",
                 ),
                 html.P('(formato Excel)', className='span'),

                 # generamos un div oculto para vincular los callbacks
                 html.Div([
                     html.Label('Seleccione un nivel:', className='row'),
                     dcc.Dropdown(options=[dict({'label': niveles[i], 'value': niveles[i]})
                                           for i in range(len(niveles))],
                                  id='nivel_elegido_home',
                                  value='',
                                  clearable=False,
                                  disabled=True,
                                  ),
                 ], id='selector_nivel', hidden=True, className='row'),

                 # Finalmente, desplegamos la tabla de datos
                 dash_table.DataTable(
                     id='tabla-datos',
                     sort_action='native',
                     # aplicamos un filtro condicional para resaltar inscriptos
                     style_data_conditional=[
                         {
                             'if': {
                                 'filter_query': '{estado} = Inscripto',
                             },
                             'backgroundColor': '#008a5a',
                             'color': 'white'
                         }, ]
                 ),
             ])
], className='cuerpo')


################################## APP LAYOUT ###################################
################################## CALL BACKS ###################################
# el primer callback refresca el hidden de la app, para visualizarla con la contraseña
@app.callback(
    Output('password_valid', 'hidden'),
    [Input('password', 'value')])
def password(password):
    password_key = 'Un7r3f_2020'
    my_pass = 'limon2015'
    if password == password_key:
        return False
    elif password == my_pass:
        return False
    else:
        return True


# luego de seleccionar el nivel, este callback devuelve un listado de propuestas dentro de dicho nivel
@app.callback(
    Output('carrera_elegida', 'options'),
    [Input('nivel_elegido', 'value')])
def set_nivel(selected_carrera):
    level_set = all_options[selected_carrera]
    level_set.sort()
    niveles_lst = [{'label': i, 'value': i} for i in level_set]
    niveles_lst.append({'label': 'Total Institución', 'value': 'Total Institución'})
    return niveles_lst


# con el nivel elegido, seleccionamos una carrera que será el input_value de toda la info
@app.callback(
    Output('carrera_elegida', 'value'),
    [Input('carrera_elegida', 'options')])
def set_carreras(available_options):
    return available_options[0]['value']


@app.callback(
    [dash.dependencies.Output('graph_fechas', 'figure'),
     dash.dependencies.Output('graph_sexo', 'figure')],
    [dash.dependencies.Input('carrera_elegida', 'value')])
def update_graficos(input_value):
    if input_value == 'Total Institución':
        vista = pre.copy()
        layout_a = {'title': 'Preinscripciones totales por fecha'}

        # # TABLA
        # tabla = totales[['nivel','propuesta','estado']].copy()
        # tabla = pd.concat([tabla.drop('estado', axis=1), pd.get_dummies(tabla.estado)], axis=1)
        # tabla = tabla.groupby(['nivel', 'propuesta']).sum()
        # tabla.reset_index(inplace=True)
        # tabla['Totales'] = tabla.sum(axis=1)
        # tabla = tabla.loc[tabla.nivel != 'Sin Propuesta']
        # tabla = tabla.sort_values(by='Totales', ascending=False)
        # tabla = tabla[['nivel', 'propuesta', 'Activo', 'Potencial', 'Inscripto', 'Totales']]

        vista_b = pre.copy()
        data_estado_dic = dict(totales['estado'].value_counts())
        layout_b = {'title': 'Preinscripciones totales por estado'}
        estado_labels = ['Pendiente', 'Activo', 'Potencial', 'Inscripto']

    # PARA PANTALLA de CADA CARRERA
    else:
        vista = pre.loc[pre.propuesta == input_value][['fecha_preinscripcion', 'estado', 'cant', 'fecha_insc']].copy()
        vista['cant'] = range(1, len(vista) + 1)
        # tabla = pre.loc[pre.propuesta == input_value][['fecha_preinscripcion','ape','nom','nacionalidad','edad',
        #                                                'nro_doc','sexo','e_mail','estado']].copy() # agregar 'celular' en produccion
        layout_a = {'title': 'Preinscriptos por fecha'}
        vista_b = pre.loc[pre.propuesta == input_value][['estado']].copy()
        data_estado_dic = dict(vista_b['estado'].value_counts())
        layout_b = {'title': 'Preinscriptos por estado'}
        estado_labels = ['Activo', 'Potencial', 'Inscripto']

    # GRAFICO DE FECHAS
    colors = {'tot_pos': '#bbbbbb', 'poten': '#000e75', 'insc': '#008a5a', 'pend': '#8f2806', 'act': '#06848f'}


    trace_fechas = go.Scatter(x=list(vista.loc[vista.estado.isin(['Potencial', 'Inscripto'])].fecha_preinscripcion),
                              y=list(vista.cant), name='Totales Posibles', line=dict(color=colors['tot_pos']),
                              )
    trace_fechas_3 = go.Scatter(x=list(vista.loc[vista.estado == 'Potencial'].fecha_preinscripcion),
                                y=list(vista.cant), name='Potenciales', line=dict(color=colors['poten']),
                                )
    trace_fechas_2 = go.Scatter(x=list(vista.loc[vista.estado == 'Inscripto'].fecha_insc.sort_values()),
                                y=list(vista.cant), name='Inscriptos Actuales', line=dict(color=colors['insc']),
                                )

    # defino una lista para agrupar los 3 scatter plot
    data_fechas_lst = [trace_fechas,trace_fechas_3,trace_fechas_2]


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
                              marker_color=[colors['pend'], colors['act'], colors['poten'], colors['insc']])
    else:
        trace_estado = go.Bar(x=estado_labels, y=estado_values, name='sexos',
                              text=estado_values, textposition='auto',
                              marker_color=[colors['act'], colors['poten'], colors['insc']])

    data_estado_lst.append(trace_estado)

    return [
        {
            'data': data_fechas_lst,
            'layout': layout_a,
        },
        {
            'data': data_estado_lst,
            'layout': layout_b,
        },
    ]


# con la carrera elegida, obtenemos todos los outputs para las diferentes funciones
@app.callback(
    [dash.dependencies.Output('subtitulo', 'children'),
     dash.dependencies.Output('subtitulo_sigla', 'children'),
     # dash.dependencies.Output('graph_fechas', 'figure'),
     # dash.dependencies.Output('graph_sexo', 'figure'),
     dash.dependencies.Output('tabla-datos', 'data'),
     dash.dependencies.Output('tabla-datos', 'columns'),
     dash.dependencies.Output('download-link', 'href'),
     ],
    [dash.dependencies.Input('carrera_elegida', 'value')])
def update_datos(input_value):
    # PARA LA PANTALLA INICIAL
    if input_value == 'Total Institución':
        vista = pre.copy()
        layout_a = {'title': 'Preinscripciones totales por fecha'}

        # TABLA
        tabla = totales[['nivel', 'propuesta', 'estado']].copy()
        tabla = pd.concat([tabla.drop('estado', axis=1), pd.get_dummies(tabla.estado)], axis=1)
        tabla = tabla.groupby(['nivel', 'propuesta']).sum()
        tabla.reset_index(inplace=True)
        tabla['Totales'] = tabla.sum(axis=1)
        tabla = tabla.loc[tabla.nivel != 'Sin Propuesta']
        tabla = tabla.sort_values(by='Totales', ascending=False)
        tabla = tabla[['nivel', 'propuesta', 'Activo', 'Potencial', 'Inscripto', 'Totales']]

        vista_b = pre.copy()
        data_estado_dic = dict(totales['estado'].value_counts())
        layout_b = {'title': 'Preinscripciones totales por estado'}
        estado_labels = ['Pendiente', 'Activo', 'Potencial', 'Inscripto']

    # PARA PANTALLA de CADA CARRERA
    else:
        # vista = pre.loc[pre.propuesta == input_value][['fecha_preinscripcion','estado','cant','fecha_insc']].copy()
        # vista['cant'] = range(1,len(vista)+1)
        tabla = pre.loc[pre.propuesta == input_value][['fecha_preinscripcion', 'ape', 'nom', 'nacionalidad', 'edad',
                                                       'nro_doc', 'sexo', 'e_mail',
                                                       'estado']].copy()  # agregar 'celular' en produccion
        # layout_a = {'title': 'Preinscriptos por fecha'}
        # vista_b = pre.loc[pre.propuesta == input_value][['estado']].copy()
        # data_estado_dic = dict(vista_b['estado'].value_counts())
        # layout_b = {'title': 'Preinscriptos por estado'}
        # estado_labels = ['Activo', 'Potencial', 'Inscripto']

    # # GRAFICO DE FECHAS
    # colors = {'tot_pos' : '#bbbbbb',
    #           'poten' : '#000e75',
    #           'insc' : '#008a5a',
    #           'pend' : '#8f2806',
    #           'act' : '#06848f'}
    #
    # data_fechas_lst = []
    # trace_fechas = go.Scatter(x=list(vista.loc[vista.estado.isin(['Potencial','Inscripto'])].fecha_preinscripcion),
    #                           y=list(vista.cant), name='Totales Posibles', line=dict(color=colors['tot_pos']),
    #                           )
    # trace_fechas_3 = go.Scatter(x=list(vista.loc[vista.estado == 'Potencial'].fecha_preinscripcion),
    #                           y=list(vista.cant), name='Potenciales', line=dict(color=colors['poten']),
    #                           )
    # trace_fechas_2 = go.Scatter(x=list(vista.loc[vista.estado == 'Inscripto'].fecha_insc.sort_values()),
    #                           y=list(vista.cant), name='Inscriptos Actuales', line=dict(color=colors['insc']),
    #                           )
    # data_fechas_lst.append(trace_fechas)
    # data_fechas_lst.append(trace_fechas_3)
    # data_fechas_lst.append(trace_fechas_2)
    #
    # # GRAFICO DE ESTADOS
    # estado_values = []
    # for i in estado_labels:
    #     try:            value = data_estado_dic[i]
    #     except:         value = 0
    #     estado_values.append(value)
    #
    # data_estado_lst = []
    #
    #
    # if input_value == 'Total Institución':
    #     trace_estado = go.Bar(x=estado_labels, y=estado_values, name='sexos',
    #                           text=estado_values, textposition='auto',
    #                           marker_color = [colors['pend'],colors['act'],colors['poten'],colors['insc']] )
    # else:
    #     trace_estado = go.Bar(x=estado_labels, y=estado_values, name='sexos',
    #                           text=estado_values, textposition='auto',
    #                           marker_color = [colors['act'],colors['poten'],colors['insc']] )
    #
    # data_estado_lst.append(trace_estado)

    try:
        tabla.fecha_preinscripcion = pd.DatetimeIndex(tabla.fecha_preinscripcion).strftime("%d/%m/%Y")
    except:
        pass

    # FILE EXPORTING
    xlsx_io = io.BytesIO()
    writer = pd.ExcelWriter(xlsx_io, engine='xlsxwriter')
    tabla.reset_index(drop=True, inplace=True)
    tabla.to_excel(writer, sheet_name=dic_nom_sigla[input_value])
    writer.save()
    xlsx_io.seek(0)
    media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    data = base64.b64encode(xlsx_io.read()).decode("utf-8")
    xls_string = f'data:{media_type};base64,{data}'

    if input_value == 'Total Institución':
        return [input_value,
                dic_nom_sigla[input_value],
                # {
                # 'data':data_fechas_lst,
                # 'layout':layout_a,
                # },
                # {
                # 'data': data_estado_lst,
                # 'layout': layout_b,
                # },
                tabla.to_dict('records'),
                [{"name": dic_columns[i], "id": i} for i in tabla.columns],
                xls_string,
                ]
    else:
        return [input_value,
                'Sigla: ' + dic_nom_sigla[input_value],
                # {
                #     'data': data_fechas_lst,
                #     'layout': layout_a,
                # },
                # {
                #     'data': data_estado_lst,
                #     'layout': layout_b,
                # },
                tabla.to_dict('records'),
                [{"name": dic_columns[i], "id": i} for i in tabla.columns],
                xls_string,
                ]


################################### APP LOOP ####################################
if __name__ == '__main__':
    app.run_server(debug=True)
