import numpy as np;
import pandas as pd
import datetime;
import assets.data as data
import psycopg2, psycopg2.extras
import warnings;

#warnings.filterwarnings('ignore')

# Esta celda permite obtener toda la tabla que sea seleccionada (el orden de las columnas varía desde la db hacia aqui)
# elegimos el origen

user_db = data.user_db
pass_db = data.pass_db
host = data.host
data_db = data.data_db


def get_table(esquema, tabla_objetivo, columns):
    ''' esta funcion toma 3 parametros, esquema, tabla_objetivo y columns
    esquema y tabla_objetivo son variables definidas, y columns es una lista de columnas filtrada de tablas[0]
    siempre se trabajará con la base de datos declarada en data_db al inicio de esta notebook.
    '''
    conn = psycopg2.connect(database=data_db, user=user_db, password=pass_db, host=host);
    cur = conn.cursor()
    cur.execute('SELECT {} FROM {}.{}'.format(', '.join(columns), esquema, tabla_objetivo))

    global output_df
    output_df = pd.DataFrame(cur.fetchall(), columns=columns)
    # cerrar siempre la conexion por las dudas...
    conn.close()


# DataBase: Preinscripcion

def consulta_db(user_db=user_db, pass_db=pass_db, host=host):
    global data_db
    # nos conectamos a la base
    conn = psycopg2.connect(database=data_db, user=user_db, password=pass_db, host=host);
    cur = conn.cursor()
    # comprueba todas las tablas y obtiene las columnas de la tabla objetivo...
    cur.execute('''SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS''')
    tablas = pd.DataFrame(cur.fetchall());
    conn.close()
    tablas.columns = ['tabla_name', 'campo']

    # public.sga_preinscripcion

    # seleccionamos el esquema y la tabla
    esquema = 'public'
    tabla_objetivo = 'sga_preinscripcion'
    columns = list(tablas.loc[tablas['tabla_name'] == tabla_objetivo]['campo'].unique())
    get_table(esquema, tabla_objetivo, columns)

    # P : Pendiente de activacion
    # A : Activado. La persona respondió el mail enviado
    # C : Preparado para proceso masivo de inscripción.
    # I : Inscripto al Guarani

    users = output_df[['id_preinscripcion',
                       'tipo_documento', 'nro_documento', 'apellido', 'nombres',
                       'fecha_nacimiento', 'sexo', 'nacionalidad',
                       #                   'alu_otestsup_uni', 'alu_otestsup_carr',
                       'celular_numero', 'e_mail',
                       'version_modificacion', 'version_impresa']].copy()

    users.columns = ['id_preinscripcion', 'tipo_doc', 'nro_doc', 'ape', 'nom', 'fecha_nac', 'sexo', 'nacion',
                     #                 'uni_previa', 'carr_previa',
                     'celular', 'e_mail', 'ver_act', 'ver_imp']

    # public.sga_preinscripcion_propuestas

    # seleccionamos el esquema y la tabla
    tabla_objetivo = 'sga_preinscripcion_propuestas'
    columns = list(tablas.loc[tablas['tabla_name'] == tabla_objetivo]['campo'].unique())

    get_table(esquema, tabla_objetivo, columns)

    users_prop = output_df[['id_preinscripcion', 'propuesta', 'fecha_preinscripcion', 'estado']].copy()

    estados_dic = {'P': 'Pendiente', 'A': 'Activo', 'C': 'Potencial', 'I': 'Inscripto'}
    users_prop['estado'] = users_prop.estado.map(estados_dic)

    # DataBase: Gestion
    data_db = 'guarani3162posgrado'
    # Esta celda permite obtener toda la tabla que sea seleccionada (el orden de las columnas varía desde la db hacia aqui)
    conn = psycopg2.connect(database=data_db, user=user_db, password=pass_db, host=host);
    cur = conn.cursor()
    # comprueba todas las tablas y obtiene las columnas de la tabla objetivo...
    cur.execute('''SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS''')
    tablas = pd.DataFrame(cur.fetchall());
    conn.close()
    tablas.columns = ['tabla_name', 'campo']

    # negocio.sga_propuestas

    # seleccionamos el esquema y la tabla
    esquema = 'negocio'
    tabla_objetivo = 'sga_propuestas'
    columns = list(tablas.loc[tablas['tabla_name'] == tabla_objetivo]['campo'].unique())

    get_table(esquema, tabla_objetivo, columns)
    sga_propuestas = output_df[['propuesta', 'nombre', 'nombre_abreviado', 'codigo']].copy()

    dic_id_sigla = {sga_propuestas.propuesta.iloc[i]: sga_propuestas.nombre_abreviado.iloc[i] for i in
                    range(len(sga_propuestas))}
    dic_sigla_nom = {sga_propuestas.nombre_abreviado.iloc[i]: sga_propuestas.nombre.iloc[i] for i in
                     range(len(sga_propuestas))}

    users_prop['propuesta_id'] = users_prop.propuesta.copy()
    users_prop['propuesta'] = users_prop.propuesta.map(dic_id_sigla)

    # negocio.sga_propuestas_aspira

    # seleccionamos el esquema y la tabla
    esquema = 'negocio'
    tabla_objetivo = 'sga_propuestas_aspira'
    columns = list(tablas.loc[tablas['tabla_name'] == tabla_objetivo]['campo'].unique())

    get_table(esquema, tabla_objetivo, columns)

    aspira = output_df[['persona', 'periodo_insc', 'anio_academico', 'propuesta', 'fecha_inscripcion', 'situacion_asp',
                        'fecha_alta']].copy()

    # negocio.mdp_personas

    # seleccionamos el esquema y la tabla
    esquema = 'negocio'
    tabla_objetivo = 'mdp_personas'
    columns = list(tablas.loc[tablas['tabla_name'] == tabla_objetivo]['campo'].unique())

    get_table(esquema, tabla_objetivo, columns)

    personas = output_df[['persona', 'usuario', 'apellido']].copy()
    personas.dropna(inplace=True)
    personas.reset_index(inplace=True, drop=True)

    dic_personas = {personas.persona.iloc[i]: personas.usuario.iloc[i] for i in range(len(personas))}

    # se preinscribió alguien que ya era persona, al procesar esa preinscripcion se rompio por lo que la agrego a mano y sigue...
    dic_personas.update({11247: '22655029'})
    dic_personas.update({13125: '10846093'})

    aspira['DNI'] = aspira.persona.map(dic_personas)

    dic_fechas_insc = {str(aspira.DNI.iloc[i]) + '_' + str(aspira.propuesta.iloc[i]): aspira.fecha_alta.iloc[i] for i in
                       range(len(aspira))}

    # MERGE
    totales = pd.merge(users, users_prop, on='id_preinscripcion', how='outer')
    totales['unique'] = [str(totales.id_preinscripcion.iloc[i]) + '_' + str(totales.propuesta.iloc[i]) for i in
                         range(len(totales))]
    totales.drop_duplicates(subset='unique', inplace=True)
    totales.reset_index(drop=True, inplace=True)

    totales.loc[totales.estado.isna(), 'estado'] = 'Activo'

    # MAPPING DATA
    # DOCUMENTO TIPO
    doc_tipo = {0: 'DNI', 1: 'DNT', 2: 'CI', 3: 'CUIL', 18: 'LE', 19: 'LC', 20: 'CM', 21: 'CD', 22: 'CC', 23: 'CDI',
                90: 'PAS'}
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
    totales.sexo.fillna('0', inplace=True)
    totales['sexo'] = totales.sexo.map(sex_dic)

    # NACIONALIDAD
    pais_dic = {1: 'Argentino', 2: 'Extranjero', 3: 'Naturalizado', 4: 'Por Opción'}
    totales['nacionalidad'] = totales.nacion.map(pais_dic)

    # PROPUESTAS Y NIVELES
    totales['sigla'] = totales.propuesta.copy()
    totales['propuesta'] = totales.propuesta.map(dic_sigla_nom)
    totales['nivel'] = [
        totales.propuesta.iloc[i].split(' ')[0] if type(totales.propuesta.iloc[i]) == str else 'Sin Propuesta' for i in
        range(len(totales))]

    totales['propuesta'] = totales.propuesta.fillna('Sin Propuesta')
    totales['sigla'] = totales.sigla.fillna('Sin Propuesta')
    totales['version'] = [
        'Vacia' if totales.ver_imp.iloc[i] == 0 else 'Correcta' if totales.ver_imp.iloc[i] == totales.ver_act.iloc[
            i] else 'Anterior' for i in range(len(totales))]
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
    totales = totales[['id_preinscripcion', 'estado', 'nivel', 'sigla', 'propuesta', 'version',
                       'fecha_preinscripcion', 'unique',
                       'tipo_doc', 'nro_doc', 'ape', 'nom', 'fecha_nac', 'edad', 'nacionalidad',
                       'sexo', 'celular', 'e_mail', 'fecha_insc']]

    return totales, dic_sigla_nom