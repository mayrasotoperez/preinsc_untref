import numpy as np;
import pandas as pd

import time;
import datetime
from datetime import date

import psycopg2, psycopg2.extras

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
# pais DOC
pais_dic = {1: 'Argentino', 2: 'Extranjero', 3: 'Naturalizado', 4: 'Por Opción'}
preinscriptos['nacionalidad'] = preinscriptos.nacionalidad.map(pais_dic)
# Tipo DOC
names = ['id', 'doc', 'sigla', 'a', 'b', 'c', 'd', 'e', 'f']
docus = pd.read_csv('assets/mdp_tipo_documento.csv', sep='|', index_col=None, names=names)
docu_dic = {docus.id.iloc[i]: docus.sigla.iloc[i] for i in range(len(docus))}
preinscriptos['tipo_documento'] = preinscriptos.tipo_documento.map(docu_dic)
# Sexo
preinscriptos.sexo.fillna('0', inplace=True)
sex_dic = {'0': 'No informa', '1': 'Masculino', '2': 'Femenino'}
preinscriptos['sexo'] = preinscriptos.sexo.map(sex_dic)
# ---------------------------------------------------------------------------------
############################## COLUMNAS FINALES ##################################
pre = preinscriptos[['fecha_preinscripcion', 'carrera', 'apellido', 'nombres',
                     'nacionalidad', 'edad', 'tipo_documento', 'nro_documento',
                     'sexo', 'celular_numero', 'e_mail']].copy()

pre.columns = ['Fecha', 'Carrera', 'Apellidos', 'Nombres', 'Nacionalidad', 'Edad', 'Doc. tipo',
               'Doc. número', 'Sexo', 'Celular', 'e_mail']

pre.to_csv('consulta.csv', index=None, sep='|')



import sqlite3

conn = sqlite3.connect('preinscriptos_db.db')
c = conn.cursor()

def create_table():
    c.execute("CREATE TABLE IF NOT EXISTS peinscriptos(unix REAL, pre TEXT)")
    conn.commit()

create_table()