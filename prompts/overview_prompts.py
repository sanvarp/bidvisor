ENTITY_TEMPLATE = """
¿Cuál es la entidad que publicó la convocatoria?

{format_instructions}

Responde única y exclusivamente con el JSON que se te solicita. No incluyas información adicional. Tampoco incluyas comentarios en el JSON.
"""

OBJECTIVE_TEMPLATE = """
¿Cuál es el nombre del objeto que se busca desarrollar en la convocatoria?

{format_instructions}

Responde única y exclusivamente con el JSON que se te solicita. No incluyas información adicional. Tampoco incluyas comentarios en el JSON.
"""

BUDGET_TEMPLATE = """
¿Cuánto es el presupuesto total disponible en la convocatoria para la ejecución del proyecto?

Devuelve el monto SIEMPRE formateado así:
- Con separadores de miles (puntos para COP, comas para otras monedas)
- Con la moneda explícita al final usando su código ISO 4217 (COP, USD, EUR, MXN, etc.)
- Si el documento NO especifica la moneda, asume Pesos Colombianos (COP)

Ejemplos del formato esperado:
- "$1.234.567.890 COP"
- "USD 1,234,567"
- "$57.325.000.000 COP (incluye IVA)"

Si el documento expresa el monto en millones o miles (ej. "2.431,67 millones"), conviértelo al valor completo con todos los dígitos.

{format_instructions}

Responde única y exclusivamente con el JSON que se te solicita. No incluyas información adicional. Tampoco incluyas comentarios en el JSON.
"""