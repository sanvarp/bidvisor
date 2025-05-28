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
        description="El presupuesto total asignado a la ejecución del proyecto, incluyendo impuestos y otros costos asociados. Este monto puede ser expresado en la moneda local o en una moneda extranjera.",
    )
]
