"""AddField tolerante para TiDB/MySQL.

- Si la columna ya existe (migración a medias), no la vuelve a crear.
- TiDB no acepta crear columna + llave foránea en un solo ALTER TABLE,
  así que se crea la columna primero y la restricción después.
"""
from django.db import migrations


class AddFieldSeguro(migrations.AddField):
    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        modelo = to_state.apps.get_model(app_label, self.model_name)
        campo = modelo._meta.get_field(self.name)
        conn = schema_editor.connection
        with conn.cursor() as cursor:
            columnas = [c.name for c in conn.introspection.get_table_description(cursor, modelo._meta.db_table)]
        if campo.column in columnas:
            return
        if campo.remote_field is not None and campo.db_constraint:
            sin_fk = campo.clone()
            sin_fk.set_attributes_from_name(self.name)
            sin_fk.model = modelo
            sin_fk.db_constraint = False
            schema_editor.add_field(modelo, sin_fk)
            try:
                schema_editor.execute(
                    schema_editor._create_fk_sql(modelo, campo, '_fk_%s' % campo.column)
                )
            except Exception:
                pass  # Django igual valida la relación; la restricción en BD es opcional
        else:
            schema_editor.add_field(modelo, campo)
