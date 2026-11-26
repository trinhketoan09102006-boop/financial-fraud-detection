"""Contract-driven Pandas to Arrow conversion helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyarrow as pa
import yaml

from .audit import ROOT


_ARROW_TYPES = {
    "string": pa.string(),
    "datetime64[ns]": pa.timestamp("ns"),
    "float64": pa.float64(),
    "float32": pa.float32(),
    "int64": pa.int64(),
    "int8": pa.int8(),
}


def load_contract_arrow_schema(schema_path: Path | None = None) -> pa.Schema:
    """Load Arrow field types and nullability from the canonical YAML contract."""
    path = schema_path or ROOT / "configs" / "data_schema.yaml"
    contract = yaml.safe_load(path.read_text(encoding="utf-8"))
    fields = []
    for name, spec in contract["fields"].items():
        try:
            arrow_type = _ARROW_TYPES[spec["type"]]
        except KeyError as exc:
            raise ValueError(f"Unsupported contract type for {name}: {spec.get('type')}") from exc
        fields.append(pa.field(name, arrow_type, nullable=spec.get("nullable", True)))
    return pa.schema(fields)


def dataframe_to_arrow_table(
    frame: pd.DataFrame,
    *,
    strict: bool = True,
    schema_path: Path | None = None,
) -> pa.Table:
    """Convert a frame using contract types, independent of pandas/Arrow inference.

    Strict mode requires exactly the normalized contract fields. Non-strict mode
    supports split outputs: known fields use contract types and additional
    Arrow ``large_string`` fields (such as the split label) are narrowed to
    Arrow ``string`` as well.
    """
    contract_schema = load_contract_arrow_schema(schema_path)
    contract_fields = {field.name: field for field in contract_schema}
    frame_columns = list(frame.columns)
    if strict:
        missing = set(contract_fields) - set(frame_columns)
        extra = set(frame_columns) - set(contract_fields)
        if missing or extra:
            raise ValueError(f"Frame does not match contract fields; missing={sorted(missing)}, extra={sorted(extra)}")
        column_order = contract_schema.names
    else:
        column_order = frame_columns

    inferred = pa.Table.from_pandas(frame, preserve_index=False)
    arrays = []
    fields = []
    for name in column_order:
        source = inferred.column(name)
        source_field = inferred.schema.field(name)
        target = contract_fields.get(name)
        if target is not None:
            target_type = target.type
            nullable = target.nullable
        elif pa.types.is_large_string(source_field.type):
            target_type = pa.string()
            nullable = source_field.nullable
        else:
            target_type = source_field.type
            nullable = source_field.nullable

        if not nullable and source.null_count:
            raise ValueError(f"Non-nullable contract field {name} contains {source.null_count} null values.")
        if source.type != target_type:
            source = source.cast(target_type, safe=True)
        arrays.append(source)
        fields.append(pa.field(name, target_type, nullable=nullable, metadata=source_field.metadata))
    return pa.Table.from_arrays(arrays, schema=pa.schema(fields))
