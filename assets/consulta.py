import numpy as np;
import pandas as pd;
import datetime;
import assets.data as data
import psycopg2, psycopg2.extras;
import warnings;

warnings.filterwarnings('ignore')

# Esta celda permite obtener toda la tabla que sea seleccionada (el orden de las columnas varía desde la db hacia aqui)
user_db = data.user_db;
pass_db = data.pass_db
host_db = data.host;
data_db = data.data_db


def get_table(esquema, tabla_objetivo, columns, where):
    ''' toma como parametros: esquema, tabla_objetivo, columns, where
    esquema y tabla_objetivo son variables definidas, y columns es una lista de columnas filtrada de tablas[0]
    siempre se trabajará con la base de datos declarada en data_db al inicio de esta notebook.
    '''
    global out
    conn = psycopg2.connect(database=data_db, user=user_db, password=pass_db, host=host_db)
    cur = conn.cursor()
    if where == '':
        cur.execute('SELECT {} FROM {}.{}'.format(', '.join(columns), esquema, tabla_objetivo))
        out = pd.DataFrame(cur.fetchall(), columns=columns)
    else:
        cur.execute('SELECT {} FROM {}.{} WHERE {}'.format(', '.join(columns), esquema, tabla_objetivo, where))
        out = pd.DataFrame(cur.fetchall(), columns=columns)
    conn.close()


def consulta_db(user_db=user_db, pass_db=pass_db, host=host_db):
    global data_db
    esquema = 'public'

    ### public.sga_preinscripcion
    tabla_objetivo = 'sga_preinscripcion'
    columns = ['id_preinscripcion', 'tipo_documento', 'nro_documento', 'apellido', 'nombres', 'fecha_nacimiento',
               'sexo',
               'nacionalidad', 'celular_numero', 'e_mail', 'version_modificacion', 'version_impresa']
    get_table(esquema, tabla_objetivo, columns, '')
    usuarios = out.copy()
    usuarios.columns = ['id_preinscripcion', 'tipo_doc', 'nro_doc', 'ape', 'nom', 'fecha_nac', 'sexo', 'nacion',
                        'celular',
                        'e_mail', 'ver_act', 'ver_imp']

    # public.sga_preinscripcion_propuestas
    tabla_objetivo = 'sga_preinscripcion_propuestas'
    get_table(esquema, tabla_objetivo, ['id_preinscripcion', 'propuesta', 'fecha_preinscripcion', 'estado'], '')
    preinscripciones = out.copy()
    estados_dic = {'P': 'Pendiente', 'A': 'Activo', 'C': 'Potencial', 'I': 'Inscripto'}
    preinscripciones['estado'] = preinscripciones.estado.map(estados_dic)
    preinscripciones['id_prop'] = [
        str(preinscripciones.id_preinscripcion.iloc[i]) + '_' + str(preinscripciones.propuesta.iloc[i])
        for i in range(len(preinscripciones))]
    preinscripciones.drop_duplicates(subset='id_prop', keep='last', inplace=True)

    # cambiamos de base de datos DataBase: Gestion
    data_db = 'guarani3162posgrado'
    esquema = 'negocio'

    ### negocio.sga_propuestas
    tabla_objetivo = 'sga_propuestas'
    sql_propuestas = ', '.join(preinscripciones.propuesta.astype(str).drop_duplicates().unique())
    get_table(esquema, tabla_objetivo, ['propuesta', 'nombre', 'nombre_abreviado', 'codigo'],
              'propuesta in ({})'.format(sql_propuestas))
    sga_propuestas = out.copy()
    dic_id_sigla = {sga_propuestas.propuesta.iloc[i]: sga_propuestas.nombre_abreviado.iloc[i] for i in
                    range(len(sga_propuestas))}
    dic_sigla_nom = {sga_propuestas.nombre_abreviado.iloc[i]: sga_propuestas.nombre.iloc[i] for i in
                     range(len(sga_propuestas))}
    preinscripciones['propuesta_id'] = preinscripciones.propuesta.copy()
    preinscripciones['propuesta'] = preinscripciones.propuesta.map(dic_id_sigla)

    # negocio.sga_propuestas_aspira
    tabla_objetivo = 'sga_propuestas_aspira'
    get_table(esquema, tabla_objetivo, ['persona', 'periodo_insc', 'anio_academico', 'propuesta', 'fecha_inscripcion',
                                        'situacion_asp', 'fecha_alta'], 'anio_academico > 2019')
    aspira = out.copy()

    # negocio.mdp_personas
    sql_personas = ', '.join(aspira.persona.astype(str).drop_duplicates().unique())
    tabla_objetivo = 'mdp_personas'
    get_table(esquema, tabla_objetivo, ['persona', 'usuario', 'apellido'], 'persona in ({})'.format(sql_personas))
    personas = out.copy()
    personas.dropna(inplace=True)
    personas.reset_index(inplace=True, drop=True)
    dic_personas = {personas.persona.iloc[i]: personas.usuario.iloc[i] for i in range(len(personas))}
    aspira['DNI'] = aspira.persona.map(dic_personas)
    dic_fechas_insc = {str(aspira.DNI.iloc[i]) + '_' + str(aspira.propuesta.iloc[i]): aspira.fecha_alta.iloc[i] for i in
                       range(len(aspira))}

    # MERGE
    totales = pd.merge(usuarios, preinscripciones, on='id_preinscripcion', how='outer')
    totales['unique'] = [str(totales.id_preinscripcion.iloc[i]) + '_' + str(totales.propuesta.iloc[i]) for i in
                         range(len(totales))]
    totales.drop_duplicates(subset='unique', inplace=True)
    totales.reset_index(drop=True, inplace=True)
    totales.loc[totales.estado.isna(), 'estado'] = 'Activo'

    # MAPPING DATA
    # DOCUMENTO TIPO
    tabla_objetivo = 'mdp_tipo_documento'
    get_table(esquema, tabla_objetivo, ['tipo_documento', 'desc_abreviada'], '')
    doc_tipo = {out.tipo_documento.iloc[i]: out.desc_abreviada.iloc[i] for i in range(len(out))}
    totales['tipo_doc'] = totales.tipo_doc.map(doc_tipo)

    # FECHA DE NACIMIENTO -> EDAD
    def calculate_age(b):
        try:
            return datetime.date.today().year - b.year - (
                        (datetime.date.today().month, datetime.date.today().day) < (b.month, b.day))
        except:
            return 'No Informa'

    totales['edad'] = totales.fecha_nac.map(calculate_age)

    # SEXO
    sex_dic = {'0': 'No informa', '1': 'Masculino', '2': 'Femenino'}
    totales.sexo.fillna('0', inplace=True);
    totales['sexo'] = totales.sexo.map(sex_dic)

    # NACIONALIDAD
    pais_dic = {1: 'Argentino', 2: 'Extranjero', 3: 'Naturalizado', 4: 'Por Opción'}
    totales['nacionalidad'] = totales.nacion.map(pais_dic)

    # PROPUESTAS Y NIVELES
    totales['sigla'] = totales.propuesta.copy()
    totales['propuesta'] = totales.propuesta.map(dic_sigla_nom)
    totales['nivel'] = [totales.propuesta.iloc[i].split(' ')[0]
                        if type(totales.propuesta.iloc[i]) == str
                        else 'Sin Propuesta' for i in range(len(totales))]
    totales['propuesta'] = totales.propuesta.fillna('Sin Propuesta')
    totales['sigla'] = totales.sigla.fillna('Sin Propuesta')
    totales['version'] = ['Vacia' if totales.ver_imp.iloc[i] == 0
                          else 'Correcta' if totales.ver_imp.iloc[i] == totales.ver_act.iloc[i]
    else 'Anterior' for i in range(len(totales))]
    totales = totales.sort_values(by='fecha_preinscripcion')

    # FECHA DE INSCRIPCION (solo para inscriptos)
    totales.propuesta_id.fillna(0, inplace=True)
    totales.propuesta_id = totales.propuesta_id.astype(int)
    totales['dni_prop'] = [str(totales.nro_doc.iloc[i]) + '_' + str(totales.propuesta_id.iloc[i]) for i in
                           range(len(totales))]
    totales['fecha_insc'] = np.nan
    totales.reset_index(inplace=True, drop=True)

    errores = []
    for i in range(len(totales)):
        if totales.estado.iloc[i] == 'Inscripto':
            try:
                totales.fecha_insc.iloc[i] = dic_fechas_insc[totales.dni_prop.iloc[i]]
            except:
                errores.append(i)
        else:
            pass

    totales = totales.drop(errores)
    totales.reset_index(inplace=True, drop=True)
    totales.fecha_insc.fillna(0, inplace=True)
    totales.loc[totales.propuesta == 'Sin Propuesta', 'estado'] = 'Pendiente'
    totales.loc[(totales.propuesta != 'Sin Propuesta') & (totales.version != 'Correcta'), 'estado'] = 'Activo'
    totales.loc[(totales.propuesta != 'Sin Propuesta') & (totales.version == 'Correcta'), 'estado'] = 'Potencial'
    totales.loc[(totales.propuesta != 'Sin Propuesta') & (totales.version == 'Correcta') & (
            totales.fecha_insc != 0), 'estado'] = 'Inscripto'

    # ACOMODAMOS LAS FEATURES
    totales = totales[['id_preinscripcion', 'estado', 'nivel', 'sigla', 'propuesta', 'version', 'fecha_preinscripcion',
                       'unique', 'tipo_doc', 'nro_doc', 'ape', 'nom', 'fecha_nac', 'edad', 'nacionalidad',
                       'sexo', 'celular', 'e_mail', 'fecha_insc']]

    return totales, dic_sigla_nom