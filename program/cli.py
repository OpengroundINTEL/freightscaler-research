from __future__ import annotations

import argparse
import csv
import importlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trucking-climate-risk",
        description="Generate synthetic trucking data and run the climate-risk engine.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser(
        "generate-data",
        help="Generate synthetic trucking data and write CSV and JSON outputs.",
    )
    generate.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Directory where generated CSV and JSON files will be written.",
    )
    generate.add_argument(
        "--rows",
        type=int,
        default=100,
        help="Requested record count passed through to the synthetic data module.",
    )
    generate.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed passed through to the synthetic data module.",
    )
    generate.set_defaults(handler=handle_generate_data)

    run = subparsers.add_parser(
        "run-risk",
        help="Run the climate-risk engine and write CSV and JSON outputs.",
    )
    run.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Directory where risk CSV and JSON files will be written.",
    )
    run.add_argument(
        "--input-csv",
        type=Path,
        default=None,
        help="Optional synthetic-data CSV input for the risk engine.",
    )
    run.add_argument(
        "--input-json",
        type=Path,
        default=None,
        help="Optional synthetic-data JSON input for the risk engine.",
    )
    run.add_argument(
        "--scenario",
        default=None,
        help="Optional scenario name passed through to the risk engine.",
    )
    run.set_defaults(handler=handle_run_risk)

    return parser


def handle_generate_data(args: argparse.Namespace) -> int:
    output_dir = ensure_output_dir(args.output_dir)
    synthetic_module = importlib.import_module(".synthetic_data", package=__package__)
    generator = resolve_callable(
        synthetic_module,
        (
            "generate_synthetic_data",
            "generate_data",
            "create_synthetic_data",
            "main",
        ),
    )

    result = invoke_flexibly(
        generator,
        rows=args.rows,
        num_rows=args.rows,
        n_rows=args.rows,
        seed=args.seed,
        random_seed=args.seed,
        output_dir=output_dir,
    )

    payload = normalize_output(result, default_records_key="records")
    write_outputs(output_dir, "synthetic_data", payload)
    return 0


def handle_run_risk(args: argparse.Namespace) -> int:
    output_dir = ensure_output_dir(args.output_dir)
    risk_module = importlib.import_module(".risk_engine", package=__package__)
    runner = resolve_callable(
        risk_module,
        (
            "run_risk_engine",
            "run_engine",
            "evaluate_risk",
            "main",
        ),
    )

    result = invoke_flexibly(
        runner,
        input_csv=args.input_csv,
        csv_path=args.input_csv,
        input_json=args.input_json,
        json_path=args.input_json,
        scenario=args.scenario,
        output_dir=output_dir,
    )

    payload = normalize_output(result, default_records_key="risk_results")
    write_outputs(output_dir, "risk_results", payload)
    return 0


def ensure_output_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_callable(module: Any, candidate_names: Sequence[str]) -> Any:
    for name in candidate_names:
        value = getattr(module, name, None)
        if callable(value):
            return value
    raise AttributeError(
        f"Expected one of {', '.join(candidate_names)} in module {module.__name__}."
    )


def invoke_flexibly(func: Any, **kwargs: Any) -> Any:
    call_kwargs = dict(kwargs)
    while True:
        try:
            return func(**call_kwargs)
        except TypeError as exc:
            unknown = extract_unexpected_keyword(exc)
            if unknown is None or unknown not in call_kwargs:
                raise
            call_kwargs.pop(unknown)


def extract_unexpected_keyword(exc: TypeError) -> str | None:
    message = str(exc)
    marker = "unexpected keyword argument "
    if marker not in message:
        return None
    tail = message.split(marker, 1)[1].strip()
    if not tail or tail[0] not in {"'", '"'}:
        return None
    quote = tail[0]
    end = tail.find(quote, 1)
    if end == -1:
        return None
    return tail[1:end]


def normalize_output(result: Any, *, default_records_key: str) -> dict[str, Any]:
    if result is None:
        records: list[dict[str, Any]] = []
        metadata: dict[str, Any] = {}
    elif isinstance(result, Mapping):
        records = to_records(result.get(default_records_key, result.get("records", result)))
        metadata = {k: v for k, v in result.items() if k not in {default_records_key, "records"}}
    else:
        records = to_records(result)
        metadata = {}

    return {
        "records": records,
        "metadata": metadata,
        "record_count": len(records),
    }


def to_records(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [dict(value)]
    if isinstance(value, (str, bytes)):
        return [{"value": value.decode() if isinstance(value, bytes) else value}]
    if isinstance(value, Iterable):
        records: list[dict[str, Any]] = []
        for item in value:
            if isinstance(item, Mapping):
                records.append(dict(item))
            else:
                records.append({"value": item})
        return records
    return [{"value": value}]


def write_outputs(output_dir: Path, stem: str, payload: Mapping[str, Any]) -> None:
    json_path = output_dir / f"{stem}.json"
    csv_path = output_dir / f"{stem}.csv"

    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(csv_path, payload["records"])


def write_csv(path: Path, records: Sequence[Mapping[str, Any]]) -> None:
    fieldnames: list[str] = []
    for record in records:
        for key in record.keys():
            if key not in fieldnames:
                fieldnames.append(str(key))

    with path.open("w", newline="", encoding="utf-8") as handle:
        if not fieldnames:
            handle.write("")
            return

        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow({name: stringify(record.get(name)) for name in fieldnames})


def stringify(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
