import argendata.qa as qa
from subprocess import CalledProcessError
from .utils.gwrappers import GAuth, GDrive
from .utils.files import file
from .utils import timeformat
from datetime import datetime
import pandas as pd
import json
import pytz
from .utils.logger import LoggerFactory
from pandas import DataFrame
import pandas as pd
from argendata.reporter import Reporter
from argendata.reporter.pdfexport import pandoc_export
from argendata.freeze import generate_ids, autoajustar_columnas
from argendata.freeze import exportar_definitivo
import csv
import numpy as np

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

def wrap_string(string: str, max_length: int) -> str:
    if len(string) <= max_length:
        return string
    
    prefix_suffix_length = max_length - 3
    half_length = prefix_suffix_length // 2
    return string[:half_length+1] + '...' + string[-half_length:]

def main(subtopico: str, entrega: int, generate_indices: bool, es_definitivo: bool):
    log = LoggerFactory.getLogger('main')
    auth = GAuth.authenticate()
    drive = GDrive(auth)

    verificaciones, subtopico_obj = qa.analyze(subtopico, entrega=entrega)
    now_timestamp = datetime.now(tz=pytz.timezone('America/Argentina/Buenos_Aires'))
    today_str = now_timestamp.strftime("%d/%m/%Y")

    verificaciones['fecha'] = today_str
    verificaciones['subtopico'] = subtopico

    outfile = subtopico+str(entrega)+"-"+timeformat(now_timestamp)
    outfile_path = f'./output/{subtopico+str(entrega)}/result-'+outfile+'.json'

    with open(file(outfile_path), 'w') as fp:
        json.dump(obj=verificaciones, indent=4, fp=fp, cls=NpEncoder)

    log.info(f'Reporte para {subtopico+str(entrega)} generado en {outfile_path}')

    report_generator = Reporter(subtopico, today_str, verificaciones)
    archivos = report_generator.generar_reporte(output_folder=f'./output/{subtopico+str(entrega)}/',
                                                merge_to=f"{outfile}.md")

    log.info("Generando reporte PDF...")
    export_result = pandoc_export(archivos[-1])
    if isinstance(export_result, Exception):
        log.error(f'Error al convertir a pdf')
        if isinstance(export_result, CalledProcessError):
            log.error(f"Error en el comando {' '.join(export_result.cmd)}")
            if getattr(export_result, 'stderr', None):
                stderr = export_result.stderr.decode().strip()
                for line in stderr.split('\n'):
                    log.error(line)
    else:
        log.info(f'PDF generado: {export_result}')
    
    if generate_indices or es_definitivo:
        ids, csv_map, internal_mapping = generate_ids(subtopico, subtopico_obj.plantilla)

        DataFrame(internal_mapping).to_csv(file(f'./output/{subtopico+str(entrega)}/internal_mapping.csv'),
          index=False,
          encoding='utf-8',
          sep=',',
          lineterminator='\n',
          quoting=csv.QUOTE_ALL,
          quotechar='"',
          doublequote=True,
          escapechar=None,
          header=True
         )

        with open(file(f'./output/{subtopico+str(entrega)}/mappings.json'), 'w') as fp:
            json.dump(csv_map, indent=4, fp=fp)

        pd.DataFrame(ids).to_excel(file(f'./output/{subtopico+str(entrega)}/{subtopico}.xlsx'), index=False)
        autoajustar_columnas(f'./output/{subtopico+str(entrega)}/{subtopico}.xlsx')
        exportar_definitivo(subtopico_obj, subtopico, entrega, verificaciones['verificacion_datasets'][0], csv_map, ids)


def update(subtopico: str, entrega: int, generate_indices: bool, es_definitivo: bool):
    ...

if __name__ == "__main__":
    main()