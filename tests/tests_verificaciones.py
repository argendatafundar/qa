from unittest import TestCase
import pandas as pd
from argendata.qa import ControlSubtopico

class TestVerificacionNivelRegistro(TestCase):
    
    def test_distintos(self):
        df = pd.DataFrame({
            'orden_grafico': [1, 2, 3],
            'dataset_archivo': ['a', 'b', 'c'],
            'script_archivo': ['d', 'e', 'f'],
            'variable_nombre': ['g', 'h', 'i'],
            'url_path': ['j', 'k', 'l'],
            'fuente_nombre': ['m', 'n', 'o'],
            'institucion': ['p', 'q', 'r']
        })

        result = ControlSubtopico.verificar_nivel_registro(df)
        self.assertEqual(result, (3, []))

    def test_un_duplicado(self):
        df = pd.DataFrame({
            'orden_grafico': [1, 1, 2],
            'dataset_archivo': ['a', 'a', 'b'],
            'script_archivo': ['d', 'd', 'e'],
            'variable_nombre': ['g', 'g', 'h'],
            'url_path': ['j', 'j', 'k'],
            'fuente_nombre': ['m', 'm', 'n'],
            'institucion': ['p', 'p', 'q']
        })      
        result = ControlSubtopico.verificar_nivel_registro(df)
        self.assertEqual(result, (2, [1]))

    def test_vacio(self):
        df = pd.DataFrame({
            'orden_grafico': [],
            'dataset_archivo': [],
            'script_archivo': [],
            'variable_nombre': [],
            'url_path': [],
            'fuente_nombre': [],
            'institucion': []
        })      
        result = ControlSubtopico.verificar_nivel_registro(df)
        self.assertEqual(result, (0, []))

    def test_todos_duplicados(self):
        df = pd.DataFrame({
            'orden_grafico': [1, 1, 1],
            'dataset_archivo': ['a', 'a', 'a'],
            'script_archivo': ['d', 'd', 'd'],
            'variable_nombre': ['g', 'g', 'g'],
            'url_path': ['j', 'j', 'j'],
            'fuente_nombre': ['m', 'm', 'm'],
            'institucion': ['p', 'p', 'p']
        })      
        result = ControlSubtopico.verificar_nivel_registro(df)
        self.assertEqual(result, (1, [1]))

    def test_multiples_duplicados(self):
        df = pd.DataFrame({
            'orden_grafico': [1, 2, 3, 1, 2, 3],
            'dataset_archivo': ['A', 'B', 'C', 'A', 'B', 'C'],
            'script_archivo': ['script_A', 'script_B', 'script_C', 'script_A', 'script_B', 'script_C'],
            'variable_nombre': ['var1', 'var2', 'var3', 'var1', 'var2', 'var3'],
            'url_path': ['url1', 'url2', 'url3', 'url1', 'url2', 'url3'],
            'fuente_nombre': ['fuente1', 'fuente2', 'fuente3', 'fuente1', 'fuente2', 'fuente3'],
            'institucion': ['inst1', 'inst2', 'inst3', 'inst1', 'inst2', 'inst3']
        })      
        result = ControlSubtopico.verificar_nivel_registro(df)
        self.assertEqual(result, (3, [1,2,3]))


class TestVerificacionCompletitud(TestCase):
    def setUp(self):
        self.plantilla = pd.DataFrame({
            'dataset_archivo': ['file1', 'file2', 'file3', 'file1', 'file2'],
            'seccion_desc': ['desc1', 'desc2', None, 'desc4', 'desc5'],
            'nivel_agregacion': ['aggr1', 'aggr2', 'aggr3', 'aggr4', 'aggr5'],
            'unidad_medida': ['med1', 'med2', 'med3', 'med4', 'med5'],
            'other_column': [None, 'value2', 'value3', None, 'value5']
        })
        self.interseccion = {'file1', 'file2'}

    def test_vacio(self):
        empty_df = pd.DataFrame()
        self.assertRaises(AttributeError, lambda: ControlSubtopico.verificar_completitud(empty_df, self.interseccion))

    def test_plantilla_vacia(self):
        plantilla = pd.DataFrame({
            'dataset_archivo': [],
            'seccion_desc': [],
            'nivel_agregacion': [],
            'unidad_medida': [],
            'other_column': []
        })
        result = ControlSubtopico.verificar_completitud(plantilla, self.interseccion)
        self.assertTrue(result.empty)

    def test_interseccion_vacia(self):
        interseccion = {'file4', 'file5'}
        result = ControlSubtopico.verificar_completitud(self.plantilla, interseccion)
        self.assertTrue(result.empty)

    def test_ok(self):
        plantilla = self.plantilla.copy()
        plantilla.fillna('value', inplace=True)
        result = ControlSubtopico.verificar_completitud(plantilla, self.interseccion)
        self.assertTrue(result.empty)

    def test_filas_incompletas(self):
        expected_output = pd.DataFrame({
            'dataset_archivo': ['file1'],
            'columna_plantilla': ['other_column'],
            'filas_incompletas': [2]
        })
        result = ControlSubtopico.verificar_completitud(self.plantilla, self.interseccion)
        self.assertTrue(result.equals(expected_output))