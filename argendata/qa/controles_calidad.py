from argendata.utils import MethodMapping
from pandas import DataFrame, isnull, Series
from numpy import nan
from functools import reduce
import re

# TODO: No es un Verificador per se porque tiene que tener las siguientes capacidades:
#   - Poder ser creado con un diccionario que contiene los chequeos que van a realizarse,
#     junto con los parámetros de cada uno.
# 
#   - Poder ser creado dinámicamente en función de los parámetros previamente descritos, y ser aplicado
#     de manera dinámica.
# 
# Sin embargo, *podría* ser un Verificador, si o bien ampliamos el verificador, o bien lo restringimos
# a que tenga otro comportamiento.
# 
# La diferencia más grande que tenía antes era la llamada a las funciones con parámetros dinámicos, pero
# los verificadores, al ser subclases de DynamicExecutor, ya tienen esa capacidad.
#
# En principio esto NO es una clase para aprovechar la extensibilidad del MethodMapping con los decoradores
# y mantener el código lightweight. Pero quizá usar un Verificador sea beneficioso. (?)

controles = MethodMapping()

@controles.register('tidy_data')
def is_tidy(data: DataFrame, keys: list[str], threshold: float = 0.5):
    ncols = len(data.columns)
    nkeys = len(keys)
    ratio = (nkeys / ncols)
    result = 1 - ratio
    return result <= threshold

@controles.register
def number_of_nulls(data: DataFrame):
    ...
    return True

# @controles.register('cardinality')
# def check_cardinality(data: DataFrame, keys: list[str]):
#     # all(data[keys].apply(lambda x: x.nunique() == len(data))) (?)
#     real = len(data)
#     expected = 1
#     for k in keys: 
#         x : int = data[k].nunique()
#         expected = expected * x
#     return real <= expected

PATRON_WRONG_COLNAME = re.compile(r'[^a-z0-9_]+')
def check_wrong_colname(cadena): 
    # Definir una expresión regular que acepte solo letras y números
    # Buscar si hay coincidencias en la cadena
    coincidencias = PATRON_WRONG_COLNAME.search(cadena)
    # Devolver True si hay coincidencias, lo que significa que hay caracteres raros
    return coincidencias is not None

@controles.register('header')
def wrong_colnames(col_list: list[str]):
    # all(map(check_wrong_colname, col_list)) (?)
    return [col for col in col_list if check_wrong_colname(col)]

def tiene_caracteres_raros(cadena):
    # Definir una expresión regular que acepte solo letras y números
    patron = re.compile(r"[^a-zA-Z0-9\s,.áéíóúüñôçÁÉÍÓÚÜÑÇ_' \-\(\)]+")
    # Buscar si hay coincidencias en la cadena
    try:
        if isnull(cadena)==False:
            coincidencias = patron.search(cadena)
            return coincidencias is not None
        else:
            return False
    except Exception as exc:
        print(f"{type(exc)}: Error with string in row")

def _check_special_characters(serie:Series, count_header_row=True):
    n = 2 if count_header_row else 0
        
    row_status = serie.apply(tiene_caracteres_raros)

    if row_status.sum() <= 0:
        return nan
    
    idx = row_status[row_status == True].index.tolist()

    return ", ".join([str(x+n) for x in idx])

@controles.register('special_characters')
def special_characters(data: DataFrame):
    special_chars = data.select_dtypes(include='object').apply(_check_special_characters, axis=0).dropna()
    return len(special_chars) == 0

def make_controls(d: dict[str, object|tuple]):
    """Factory method para crear controles de calidad"""
    def curry_object(data: DataFrame):
        result = dict()
        for k,v in d.items():
            params = (data, *v) if isinstance(v, tuple) and len(v) > 0 else (data, ) if not v else (data, v)
            result[k] = controles[k](*params)
        return result
    return curry_object

# Uso:
# 
# Para NO realizar un chequeo, no tiene que ser clave. Para realizarlo, tiene que ser clave y tener un valor.
# Los valores son los argumentos adicionales de cada función. Si el valor es falsy, entonces se llama sólo con el
# dataframe a verificar, sin parámetros adicionales. 
#
# ensure_quality = make_controls({
#     'tidy_data': ['a'],
#     'number_of_nulls': None,
#     'cardinality': ['a'],
#     'header': None,
#     'special_characters': None
# })
# 
# ensure_quality(DataFrame())

# > {'tidy_data': True,
# >  'number_of_nulls': True,
# >  'cardinality': True,
# >  'header': True,
# >  'special_characters': <object at 0x7f6ab053b7d0>}