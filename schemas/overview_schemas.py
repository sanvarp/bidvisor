from langchain.output_parsers import ResponseSchema

ENTITY_SCHEMA = [
    ResponseSchema(
        name="contracting_entity",
        type="string",
        description="El nombre de la entidad que publicó la convocatoria. Esta es la organización, institución o gobierno responsable de gestionar el proceso de contratación.",
    )
]

OBJECTIVE_SCHEMA = [
    ResponseSchema(
        name="objective",
        type="string",
        description="El nombre del objeto de la convocatoria, que detalla el propósito y el alcance del proceso de contratación. Generalmente describe los bienes, servicios u obras a contratar.",
    )
]

BUDGET_SCHEMA = [
    ResponseSchema(
        name="budget",
        type="string",
        description=(
            "Presupuesto total formateado con separadores de miles y código ISO de la moneda al final. "
            "Si el documento no menciona la moneda, asume COP (Pesos Colombianos). "
            "Formato: '$1.234.567.890 COP' o 'USD 1,234,567'. "
            "Convierte montos expresados en millones/miles al valor completo con todos los dígitos."
        ),
    )
]
