# Trucking Climate-Risk Program

This package exposes a standard-library-only CLI for generating synthetic trucking data and running the climate-risk engine. The CLI writes both CSV and JSON artifacts into a user-provided output directory.

## Usage

Run the CLI as a module from the package parent directory:

```bash
python -m program.cli generate-data --output-dir ./outputs/synthetic --rows 250 --seed 42
python -m program.cli run-risk --output-dir ./outputs/risk --input-csv ./outputs/synthetic/synthetic_data.csv --scenario baseline
```

You can also inspect the built-in help:

```bash
python -m program.cli --help
python -m program.cli generate-data --help
python -m program.cli run-risk --help
```

## Outputs

`generate-data` writes:

- `synthetic_data.csv`
- `synthetic_data.json`

`run-risk` writes:

- `risk_results.csv`
- `risk_results.json`

Both commands create the output directory if needed.
