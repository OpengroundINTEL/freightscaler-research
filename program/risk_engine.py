from __future__ import annotations

from collections import defaultdict
import csv
from dataclasses import asdict, dataclass
import json
from math import exp, log
from pathlib import Path
from typing import Any, Iterable


WEATHER_FACTORS = {
    "normal": {"freq": 0.0, "sev": 0.0, "tail": 0.0},
    "heavy_rain": {"freq": 0.36, "sev": 0.12, "tail": 0.05},
    "cold_wave": {"freq": 0.18, "sev": 0.08, "tail": 0.04},
    "heat_wave": {"freq": 0.14, "sev": 0.28, "tail": 0.08},
    "snowstorm": {"freq": 0.42, "sev": 0.22, "tail": 0.10},
    "flood": {"freq": 0.55, "sev": 0.58, "tail": 0.40},
}

COVERAGE_FACTORS = {
    "liability_only": -0.08,
    "physical_damage": 0.02,
    "broad_form": 0.08,
}

CARGO_FACTORS = {
    "dry_van": 0.00,
    "refrigerated": 0.18,
    "flatbed": 0.06,
    "hazmat": 0.28,
    "mixed": 0.10,
}


@dataclass(frozen=True)
class PricingAssumptions:
    trend_factor: float = 1.06
    development_factor: float = 1.03
    fixed_expense_usd: float = 35.0
    variable_expense_rate: float = 0.11
    capital_load_rate: float = 0.09
    reinsurance_load_rate: float = 0.07
    attachment_threshold: float = 1.25
    tail_quantile: float = 0.95


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _safe_float(record: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = record.get(key, default)
    if value is None:
        return default
    return float(value)


def weather_tail_index(record: dict[str, Any]) -> float:
    regime = record.get("weather_regime", "normal")
    weather = WEATHER_FACTORS.get(regime, WEATHER_FACTORS["normal"])
    intensity = max(0.0, _safe_float(record, "weather_intensity_z"))
    exposure_hours = max(0.0, _safe_float(record, "exposure_hours_in_event"))
    flood_risk = max(0.0, _safe_float(record, "road_flood_risk"))
    return (
        weather["tail"]
        + 0.14 * intensity
        + 0.03 * exposure_hours
        + 0.18 * flood_risk
    )


def predict_claim_frequency(record: dict[str, Any]) -> float:
    """Estimate expected claim count from the baseline log-link structure."""

    exposure = max(
        0.25,
        _safe_float(record, "distance_miles", 500.0) / 1_000.0
        + _safe_float(record, "duration_hours", 10.0) / 24.0,
    )
    weather = WEATHER_FACTORS.get(record.get("weather_regime", "normal"), WEATHER_FACTORS["normal"])
    contract = COVERAGE_FACTORS.get(record.get("coverage_breadth", "physical_damage"), 0.0)
    cargo = CARGO_FACTORS.get(record.get("cargo_type", "dry_van"), 0.0)
    deductible = max(500.0, _safe_float(record, "deductible_usd", 2_500.0))
    log_mu = (
        log(exposure)
        - 4.15
        + weather["freq"]
        + 0.12 * max(0.0, _safe_float(record, "weather_intensity_z"))
        + 0.018 * max(0.0, _safe_float(record, "exposure_hours_in_event"))
        + 0.55 * _safe_float(record, "hard_brake_rate")
        + 0.45 * _safe_float(record, "overspeed_share")
        + 0.20 * _safe_float(record, "night_share")
        + 0.35 * _safe_float(record, "hos_pressure_index")
        + 0.10 * _safe_float(record, "vehicle_age_years") / 10.0
        + 0.28 * _safe_float(record, "maintenance_risk_score")
        - 0.22 * _safe_float(record, "adas_flag")
        + contract
        + 0.20 * max(0.0, cargo)
        - 0.06 * log(deductible / 1_000.0)
        - 0.04 * _safe_float(record, "safety_culture_score")
    )
    return exp(log_mu)


def predict_claim_severity(record: dict[str, Any]) -> float:
    """Estimate conditional claim severity from the baseline Gamma-style log link."""

    weather = WEATHER_FACTORS.get(record.get("weather_regime", "normal"), WEATHER_FACTORS["normal"])
    cargo = CARGO_FACTORS.get(record.get("cargo_type", "dry_van"), 0.0)
    coverage = COVERAGE_FACTORS.get(record.get("coverage_breadth", "physical_damage"), 0.0)
    deductible = max(500.0, _safe_float(record, "deductible_usd", 2_500.0))
    limit = max(50_000.0, _safe_float(record, "coverage_limit_usd", 500_000.0))
    log_mean = (
        8.95
        + weather["sev"]
        + 0.10 * max(0.0, _safe_float(record, "weather_intensity_z"))
        + 0.06 * _safe_float(record, "heat_stress_index")
        + 0.05 * _safe_float(record, "snow_ice_index")
        + 0.18 * _safe_float(record, "road_flood_risk")
        + 0.14 * _safe_float(record, "hos_pressure_index")
        + 0.09 * _safe_float(record, "maintenance_risk_score")
        + 0.05 * _safe_float(record, "vehicle_age_years") / 10.0
        + 0.04 * _safe_float(record, "payload_tons") / 20.0
        + cargo
        + 0.30 * coverage
        + 0.08 * log(limit / 100_000.0)
        - 0.05 * log(deductible / 1_000.0)
        - 0.04 * _safe_float(record, "adas_flag")
    )
    return exp(log_mean)


def predict_pure_premium(record: dict[str, Any]) -> float:
    return predict_claim_frequency(record) * predict_claim_severity(record)


def _loss_distribution(record: dict[str, Any]) -> list[float]:
    pure_premium = predict_pure_premium(record)
    tail = weather_tail_index(record)
    return [
        pure_premium * 0.55,
        pure_premium,
        pure_premium * (1.20 + 0.60 * tail),
        pure_premium * (1.55 + 1.25 * tail),
        pure_premium * (2.20 + 2.40 * tail),
    ]


def _tvar(distribution: Iterable[float], quantile: float) -> float:
    values = sorted(float(v) for v in distribution)
    if not values:
        return 0.0
    quantile = _clamp(quantile, 0.50, 0.995)
    start = int(len(values) * quantile)
    tail = values[start:] or values[-1:]
    return sum(tail) / len(tail)


def indicate_premium(
    record: dict[str, Any],
    assumptions: PricingAssumptions | None = None,
) -> dict[str, float]:
    assumptions = assumptions or PricingAssumptions()
    pure_premium = predict_pure_premium(record)
    tail_index = weather_tail_index(record)
    capital_load = assumptions.capital_load_rate * _tvar(
        _loss_distribution(record),
        assumptions.tail_quantile,
    )
    reinsurance_load = assumptions.reinsurance_load_rate * max(
        0.0,
        tail_index - assumptions.attachment_threshold,
    ) * pure_premium
    premium = (
        pure_premium * assumptions.trend_factor * assumptions.development_factor
        + assumptions.fixed_expense_usd
        + assumptions.variable_expense_rate * pure_premium
        + capital_load
        + reinsurance_load
    )
    expected_miles = max(1.0, _safe_float(record, "distance_miles", 500.0))
    return {
        "expected_claim_count": predict_claim_frequency(record),
        "expected_claim_severity_usd": predict_claim_severity(record),
        "pure_premium_usd": pure_premium,
        "capital_load_usd": capital_load,
        "reinsurance_load_usd": reinsurance_load,
        "tail_index": tail_index,
        "indicated_premium_usd": premium,
        "final_rate_per_mile_usd": premium / expected_miles,
    }


def score_trip_records(
    trips: Iterable[dict[str, Any]],
    assumptions: PricingAssumptions | None = None,
) -> list[dict[str, Any]]:
    assumptions = assumptions or PricingAssumptions()
    scored: list[dict[str, Any]] = []
    for trip in trips:
        merged = dict(trip)
        merged.update(indicate_premium(trip, assumptions))
        scored.append(merged)
    return scored


def summarize_policy_months(
    trips: Iterable[dict[str, Any]],
    claims: Iterable[dict[str, Any]],
    assumptions: PricingAssumptions | None = None,
) -> list[dict[str, Any]]:
    assumptions = assumptions or PricingAssumptions()
    claim_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for claim in claims:
        claim_map[str(claim["trip_id"])].append(claim)

    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for trip in trips:
        key = (str(trip["policy_id"]), str(trip["month_id"]))
        summary = grouped.setdefault(
            key,
            {
                "policy_id": trip["policy_id"],
                "carrier_id": trip["carrier_id"],
                "month_id": trip["month_id"],
                "scenario_id": trip.get("scenario_id"),
                "trip_count": 0,
                "distance_miles": 0.0,
                "actual_claim_count": 0,
                "actual_incurred_loss_usd": 0.0,
                "actual_paid_loss_usd": 0.0,
                "actual_case_reserve_usd": 0.0,
                "booked_premium_usd": 0.0,
                "allocated_premium_usd": 0.0,
                "expected_claim_count": 0.0,
                "expected_loss_usd": 0.0,
                "indicated_premium_usd": 0.0,
                "capital_load_usd": 0.0,
                "reinsurance_load_usd": 0.0,
                "mean_tail_index": 0.0,
                "claims_open_count": 0,
            },
        )
        pricing = indicate_premium(trip, assumptions)
        trip_claims = claim_map.get(str(trip["trip_id"]), [])
        summary["trip_count"] += 1
        summary["distance_miles"] += _safe_float(trip, "distance_miles")
        summary["allocated_premium_usd"] += _safe_float(trip, "premium_month_usd_alloc")
        summary["booked_premium_usd"] += _safe_float(trip, "premium_month_usd")
        summary["expected_claim_count"] += pricing["expected_claim_count"]
        summary["expected_loss_usd"] += pricing["pure_premium_usd"]
        summary["indicated_premium_usd"] += pricing["indicated_premium_usd"]
        summary["capital_load_usd"] += pricing["capital_load_usd"]
        summary["reinsurance_load_usd"] += pricing["reinsurance_load_usd"]
        summary["mean_tail_index"] += pricing["tail_index"]
        summary["actual_claim_count"] += len(trip_claims)
        for claim in trip_claims:
            summary["actual_incurred_loss_usd"] += _safe_float(claim, "incurred_loss_usd")
            summary["actual_paid_loss_usd"] += _safe_float(claim, "paid_loss_usd")
            summary["actual_case_reserve_usd"] += _safe_float(claim, "case_reserve_usd")
            summary["claims_open_count"] += int(bool(claim.get("open_claim_flag")))

    results: list[dict[str, Any]] = []
    for summary in grouped.values():
        trips_count = max(1, int(summary["trip_count"]))
        allocated_premium = max(1.0, float(summary["allocated_premium_usd"]))
        indicated_premium = max(1.0, float(summary["indicated_premium_usd"]))
        summary["mean_tail_index"] /= trips_count
        summary["expected_severity_usd"] = summary["expected_loss_usd"] / max(
            summary["expected_claim_count"],
            1e-9,
        )
        summary["actual_loss_ratio"] = summary["actual_incurred_loss_usd"] / allocated_premium
        summary["expected_loss_ratio"] = summary["expected_loss_usd"] / indicated_premium
        summary["final_rate_per_mile_usd"] = indicated_premium / max(
            1.0,
            float(summary["distance_miles"]),
        )
        summary["pricing_assumptions"] = asdict(assumptions)
        results.append(summary)

    results.sort(key=lambda item: (str(item["month_id"]), str(item["policy_id"])))
    return results


def _coerce_scalar(value: str) -> Any:
    if value == "":
        return ""
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _load_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [{key: _coerce_scalar(value) for key, value in row.items()} for row in reader]


def _load_json(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        records = payload.get("records", [])
        if isinstance(records, list):
            return records
    if isinstance(payload, list):
        return payload
    return []


def run_engine(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Alias used by the CLI."""
    return score_trip_records(records)


def run_risk_engine(
    input_csv: str | Path | None = None,
    input_json: str | Path | None = None,
    scenario: str | None = None,
    **_: Any,
) -> dict[str, Any]:
    """CLI-friendly wrapper that loads inputs or creates defaults."""
    if input_csv:
        trips = _load_csv(Path(input_csv))
    elif input_json:
        trips = _load_json(Path(input_json))
    else:
        from .synthetic_data import generate_data

        trips = generate_data(rows=250, scenario=scenario or "S0_baseline")["records"]

    if scenario:
        for trip in trips:
            trip["scenario_id"] = scenario

    scored = score_trip_records(trips)
    summaries = summarize_policy_months(trips, [], None)
    return {
        "risk_results": scored,
        "portfolio_summary": summaries,
        "metrics": {
            "trip_count": len(scored),
            "mean_indicated_premium_usd": round(
                sum(row["indicated_premium_usd"] for row in scored) / max(len(scored), 1),
                2,
            ),
            "mean_tail_index": round(
                sum(row["tail_index"] for row in scored) / max(len(scored), 1),
                4,
            ),
        },
    }
