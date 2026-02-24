import sqlite3
import json
import logging
from decimal import Decimal
from typing import List, Dict

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "Almacenamiento/divisas.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Inicializa la base de datos y crea la tabla si no existe."""
        query = '''
        CREATE TABLE IF NOT EXISTS divisas (
            codigo TEXT PRIMARY KEY,
            valor_actual TEXT NOT NULL,
            valor_comparacion TEXT,
            total_calculado TEXT,
            fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        '''
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                conn.commit()
            logger.info("Base de datos inicializada correctamente.")
        except Exception as e:
            logger.error(f"Error inicializando la base de datos: {e}")
            raise

    def limpiar_tabla(self):
        """Borra todos los registros de la tabla divisas antes de una nueva actualización.
        Esto garantiza que datos.json solo contenga las divisas actualmente disponibles,
        sin acumular entradas obsoletas de corridas anteriores."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM divisas')
                conn.commit()
            logger.info("Tabla divisas limpia. Lista para nueva actualización.")
        except Exception as e:
            logger.error(f"Error limpiando la tabla divisas: {e}")
            raise

    def upsert_divisa(self, codigo: str, valor_actual: Decimal, valor_comparacion: str = "", total_calculado: Decimal = None):
        """Inserta o actualiza una divisa en la base de datos conservando precisión decimal como TEXT."""
        query = '''
        INSERT INTO divisas (codigo, valor_actual, valor_comparacion, total_calculado, fecha_actualizacion)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(codigo) DO UPDATE SET
            valor_actual = excluded.valor_actual,
            valor_comparacion = excluded.valor_comparacion,
            total_calculado = excluded.total_calculado,
            fecha_actualizacion = CURRENT_TIMESTAMP
        '''
        
        # Guardar como cadena (TEXT) para mantener la precisión decimal intacta
        val_act_str = f"{valor_actual:.16f}".rstrip('0').rstrip('.') if valor_actual is not None else None
        
        # Si total_calculado es null, usamos el valor_actual (para mantener consistencia)
        if total_calculado is not None:
             total_calc_str = f"{total_calculado:.16f}".rstrip('0').rstrip('.')
        else:
             total_calc_str = val_act_str

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, (codigo, val_act_str, valor_comparacion, total_calc_str))
                conn.commit()
            logger.debug(f"Divisa {codigo} guardada exitosamente.")
        except Exception as e:
            logger.error(f"Error guardando la divisa {codigo}: {e}")
            raise

    def export_to_json(self, output_path: str = "datos.json"):
        """Exporta la tabla completa a un archivo JSON para ser leída por GitHub Pages."""
        query = 'SELECT codigo, valor_actual, valor_comparacion, total_calculado, fecha_actualizacion FROM divisas'
        data = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()

                for row in rows:
                    data.append({
                        "codigo": row["codigo"],
                        "valor_actual": row["valor_actual"],
                        "valor_comparacion": row["valor_comparacion"],
                        "total_calculado": row["total_calculado"],
                        "fecha_actualizacion": row["fecha_actualizacion"]
                    })

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logger.info(f"Datos exportados a {output_path} exitosamente. Total registros: {len(data)}")
        except Exception as e:
            logger.error(f"Error exportando a JSON: {e}")
            raise
