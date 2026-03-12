from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from math import exp, log
import random
from typing import Any

from .risk_engine import PricingAssumptions, summarize_policy_months


VOLUME_PRESETS = {
    "small_debug": {
        "n_carriers": 36,
        "vehicles_per_carrier": (4, 10),
        "drivers_per_carrier": (6, 14),
        "policy_count": 52,
        "months": 12,
        "trip_count": 25_000,
    },
    "baseline_research": {
        "n_carriers": 420,
        "vehicles_per_carrier": (5, 18),
        "drivers_per_carrier": (8, 28),
        "policy_count": 720,
        "months": 18,
        "trip_count": 300_000,
    },
    "large_stress": {
        "n_carriers": 900,
        "vehicles_per_carrier": (8, 28),
        "drivers_per_carrier": (10, 40),
        "policy_count": 1_800,
        "months": 24,
        "trip_count": 1_000_000,
    },
}


@dataclass(frozen=True)
class ScenarioConfig:
    scenario_id: str
    rain_prob_shift: float = 0.0
    heat_prob_shift: float = 0.0
    winter_prob_shift: float = 0.0
    flood_prob_shift: float = 0.0
    event_intensity_shift: float = 0.0
    heat_severity_shift: float = 0.0
    flood_tail_shift: float = 0.0
    cancellation_shift: float = 0.0
    adas_adoption_shift: float = 0.0
    routing_avoidance_gain: float = 0.0
    deductible_shift: float = 0.0
    coverage_narrowing_shift: float = 0.0
    telematics_missing_shift: float = 0.0
    maintenance_missing_shift: float = 0.0


SCENARIOS = {
    "S0_baseline": ScenarioConfig("S0_baseline"),
    "S1_wet_extreme": ScenarioConfig(
        "S1_wet_extreme",
        rain_prob_shift=0.10,
        flood_prob_shift=0.02,
        event_intensity_shift=0.35,
    ),
    "S2_heat_stress": ScenarioConfig(
        "S2_heat_stress",
        heat_prob_shift=0.12,
        event_intensity_shift=0.30,
        heat_severity_shift=0.30,
    ),
    "S3_winter_disruption": ScenarioConfig(
        "S3_winter_disruption",
        winter_prob_shift=0.16,
        event_intensity_shift=0.28,
        cancellation_shift=0.12,
    ),
    "S4_flood_tail": ScenarioConfig(
        "S4_flood_tail",
        flood_prob_shift=0.05,
        event_intensity_shift=0.45,
        flood_tail_shift=0.80,
    ),
    "S5_adaptation": ScenarioConfig(
        "S5_adaptation",
        adas_adoption_shift=0.25,
        routing_avoidance_gain=0.30,
    ),
    "S6_contract_shift": ScenarioConfig(
        "S6_contract_shift",
        deductible_shift=0.35,
        coverage_narrowing_shift=0.24,
    ),
    "S7_data_quality_degradation": ScenarioConfig(
        "S7_data_quality_degradation",
        telematics_missing_shift=0.12,
        maintenance_missing_shift=0.14,
    ),
}


CORRIDORS = [
    {
        "route_corridor_id": "C01",
        "origin_region": "Pacific",
        "destination_region": "Mountain",
        "baseline_distance_miles": 910,
        "baseline_duration_hours": 17.0,
        "baseline_flood_risk": 0.18,
        "baseline_heat_index": 0.28,
        "baseline_snow_index": 0.10,
        "congestion_class": "medium",
    },
    {
        "route_corridor_id": "C02",
        "origin_region": "Pacific",
        "destination_region": "Southwest",
        "baseline_distance_miles": 1_120,
        "baseline_duration_hours": 19.0,
        "baseline_flood_risk": 0.14,
        "baseline_heat_index": 0.48,
        "baseline_snow_index": 0.05,
        "congestion_class": "medium",
    },
    {
        "route_corridor_id": "C03",
        "origin_region": "Mountain",
        "destination_region": "Midwest",
        "baseline_distance_miles": 940,
        "baseline_duration_hours": 16.5,
        "baseline_flood_risk": 0.20,
        "baseline_heat_index": 0.26,
        "baseline_snow_index": 0.22,
        "congestion_class": "low",
    },
    {
        "route_corridor_id": "C04",
        "origin_region": "Southwest",
        "destination_region": "Midwest",
        "baseline_distance_miles": 1_070,
        "baseline_duration_hours": 18.0,
        "baseline_flood_risk": 0.16,
        "baseline_heat_index": 0.44,
        "baseline_snow_index": 0.06,
        "congestion_class": "medium",
    },
    {
        "route_corridor_id": "C05",
        "origin_region": "South",
        "destination_region": "Midwest",
        "baseline_distance_miles": 840,
        "baseline_duration_hours": 15.0,
        "baseline_flood_risk": 0.34,
        "baseline_heat_index": 0.38,
        "baseline_snow_index": 0.10,
        "congestion_class": "high",
    },
    {
        "route_corridor_id": "C06",
        "origin_region": "South",
        "destination_region": "Northeast",
        "baseline_distance_miles": 1_220,
        "baseline_duration_hours": 21.5,
        "baseline_flood_risk": 0.30,
        "baseline_heat_index": 0.34,
        "baseline_snow_index": 0.14,
        "congestion_class": "high",
    },
    {
        "route_corridor_id": "C07",
        "origin_region": "Midwest",
        "destination_region": "Northeast",
        "baseline_distance_miles": 780,
        "baseline_duration_hours": 14.0,
        "baseline_flood_risk": 0.22,
        "baseline_heat_index": 0.24,
        "baseline_snow_index": 0.22,
        "congestion_class": "high",
    },
    {
        "route_corridor_id": "C08",
        "origin_region": "Midwest",
        "destination_region": "South",
        "baseline_distance_miles": 860,
        "baseline_duration_hours": 15.5,
        "baseline_flood_risk": 0.24,
        "baseline_heat_index": 0.30,
        "baseline_snow_index": 0.12,
        "congestion_class": "medium",
    },
    {
        "route_corridor_id": "C09",
        "origin_region": "Northeast",
        "destination_region": "South",
        "baseline_distance_miles": 1_100,
        "baseline_duration_hours": 20.0,
        "baseline_flood_risk": 0.26,
        "baseline_heat_index": 0.26,
        "baseline_snow_index": 0.18,
        "congestion_class": "high",
    },
    {
        "route_corridor_id": "C10",
        "origin_region": "Northeast",
        "destination_region": "Midwest",
        "baseline_distance_miles": 760,
        "baseline_duration_hours": 13.5,
        "baseline_flood_risk": 0.20,
        "baseline_heat_index": 0.18,
        "baseline_snow_index": 0.24,
        "congestion_class": "high",
    },
]


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _weighted_choice(rng: random.Random, weights: dict[str, float]) -> str:
    items = list(weights.items())
    total = sum(weight for _, weight in items)
    draw = rng.random() * total
    running = 0.0
    for item, weight in items:
        running += weight
        if draw <= running:
            return item
    return items[-1][0]


def _month_ids(months: int) -> list[str]:
    year = 2024
    month = 1
    values: list[str] = []
    for _ in range(months):
        values.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            month = 1
            year += 1
    return values


def _corridor_map() -> dict[str, dict[str, Any]]:
    return {corridor["route_corridor_id"]: corridor for corridor in CORRIDORS}


def _season(month_index: int) -> str:
    month = (month_index % 12) + 1
    if month in (12, 1, 2):
        return "winter"
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    return "fall"


def _poisson_sample(rng: random.Random, lam: float) -> int:
    lam = max(0.0, lam)
    if lam == 0.0:
        return 0
    if lam < 30.0:
        count = 0
        limit = exp(-lam)
        product = 1.0
        while product > limit:
            count += 1
            product *= rng.random()
        return count - 1
    std = lam ** 0.5
    return max(0, int(round(rng.gauss(lam, std))))


def _negative_binomial_sample(rng: random.Random, mean: float, dispersion: float = 1.35) -> int:
    mean = max(0.0, mean)
    if mean == 0.0:
        return 0
    gamma_draw = rng.gammavariate(dispersion, mean / max(dispersion, 1e-9))
    return _poisson_sample(rng, gamma_draw)


def _weather_probs(corridor: dict[str, Any], month_index: int, scenario: ScenarioConfig) -> dict[str, float]:
    season = _season(month_index)
    base = {
        "normal": 0.70,
        "heavy_rain": 0.10,
        "cold_wave": 0.05,
        "heat_wave": 0.06,
        "snowstorm": 0.06,
        "flood": 0.03,
    }
    if season == "summer":
        base["heat_wave"] += 0.08 + scenario.heat_prob_shift
        base["heavy_rain"] += 0.04 + scenario.rain_prob_shift / 2.0
        base["snowstorm"] = 0.01
        base["cold_wave"] = 0.01
    elif season == "winter":
        base["snowstorm"] += 0.10 + scenario.winter_prob_shift
        base["cold_wave"] += 0.08 + scenario.winter_prob_shift / 2.0
        base["heat_wave"] = 0.01
    elif season == "spring":
        base["heavy_rain"] += 0.05 + scenario.rain_prob_shift
        base["flood"] += 0.02 + scenario.flood_prob_shift
    else:
        base["heavy_rain"] += 0.03 + scenario.rain_prob_shift / 2.0
        base["flood"] += 0.01 + scenario.flood_prob_shift

    base["flood"] += corridor["baseline_flood_risk"] * 0.05
    base["heat_wave"] += corridor["baseline_heat_index"] * 0.04
    base["snowstorm"] += corridor["baseline_snow_index"] * 0.05
    total = sum(base.values())
    return {key: value / total for key, value in base.items()}


def _weather_intensity(
    rng: random.Random,
    corridor: dict[str, Any],
    regime: str,
    scenario: ScenarioConfig,
) -> tuple[float, float, float, float]:
    base_intensity = {
        "normal": -0.25,
        "heavy_rain": 1.10,
        "cold_wave": 0.95,
        "heat_wave": 1.00,
        "snowstorm": 1.20,
        "flood": 1.55,
    }[regime]
    intensity = max(-0.5, rng.gauss(base_intensity + scenario.event_intensity_shift, 0.35))
    heat = _clamp(
        corridor["baseline_heat_index"]
        + (0.60 if regime == "heat_wave" else 0.06 * intensity)
        + scenario.heat_severity_shift,
        0.0,
        2.5,
    )
    snow = _clamp(
        corridor["baseline_snow_index"] + (0.75 if regime == "snowstorm" else 0.06 * intensity),
        0.0,
        2.5,
    )
    flood = _clamp(
        corridor["baseline_flood_risk"] + (0.85 if regime == "flood" else 0.08 * intensity),
        0.0,
        2.5,
    )
    exposure_hours = _clamp(
        rng.uniform(0.0, 8.0)
        + max(0.0, intensity) * 2.4
        - scenario.routing_avoidance_gain * 2.0,
        0.0,
        20.0,
    )
    return intensity, heat, snow, flood, exposure_hours


def _claim_type_weights(trip: dict[str, Any], scenario: ScenarioConfig) -> dict[str, float]:
    regime = trip["weather_regime"]
    cargo_type = trip["cargo_type"]
    weights = {
        "collision": 0.46,
        "cargo_damage": 0.16,
        "weather_damage": 0.14,
        "breakdown": 0.14,
        "liability": 0.10,
    }
    if regime == "heavy_rain":
        weights["collision"] += 0.18
        weights["weather_damage"] += 0.08
    elif regime == "heat_wave":
        weights["cargo_damage"] += 0.16
        weights["breakdown"] += 0.12
    elif regime in {"cold_wave", "snowstorm"}:
        weights["collision"] += 0.10
        weights["breakdown"] += 0.10
    elif regime == "flood":
        weights["weather_damage"] += 0.28
        weights["liability"] += 0.08
    if cargo_type == "refrigerated":
        weights["cargo_damage"] += 0.16
    if cargo_type == "hazmat":
        weights["liability"] += 0.12
    if scenario.scenario_id == "S4_flood_tail" and regime == "flood":
        weights["weather_damage"] += 0.12
    return weights


def _severity_amount(
    rng: random.Random,
    trip: dict[str, Any],
    claim_type: str,
    scenario: ScenarioConfig,
) -> tuple[float, bool]:
    base = {
        "collision": 12_500.0,
        "cargo_damage": 9_800.0,
        "weather_damage": 16_500.0,
        "breakdown": 7_200.0,
        "liability": 18_500.0,
    }[claim_type]
    regime = trip["weather_regime"]
    multiplier = (
        1.0
        + 0.10 * max(0.0, trip["weather_intensity_z"])
        + 0.16 * trip["maintenance_risk_score_imputed"]
        + 0.08 * trip["hos_pressure_index"]
        + 0.06 * trip["payload_tons_imputed"] / 20.0
    )
    if regime == "heat_wave":
        multiplier += 0.18 + scenario.heat_severity_shift
    if regime == "snowstorm":
        multiplier += 0.10
    if regime == "flood":
        multiplier += 0.44 + scenario.flood_tail_shift
    if trip["cargo_type"] == "refrigerated":
        multiplier += 0.12
    if trip["cargo_type"] == "hazmat":
        multiplier += 0.16
    if trip["coverage_breadth"] == "liability_only":
        multiplier -= 0.10
    sigma = 0.50 if regime != "flood" else 0.72
    gross = rng.lognormvariate(log(base * max(0.35, multiplier)), sigma)
    cat_tail_flag = False
    if regime == "flood" and rng.random() < (0.08 + scenario.flood_tail_shift * 0.08):
        gross *= rng.uniform(2.2, 4.8)
        cat_tail_flag = True
    limit = trip["coverage_limit_usd"]
    deductible = trip["deductible_usd"]
    net = min(limit, max(0.0, gross - deductible))
    return round(net, 2), cat_tail_flag


def generate_dataset(
    seed: int = 7,
    scenario: str = "S0_baseline",
    volume: str = "small_debug",
    pricing: PricingAssumptions | None = None,
) -> dict[str, Any]:
    """Generate research-grade synthetic trucking climate-risk tables."""

    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario}")
    if volume not in VOLUME_PRESETS:
        raise ValueError(f"Unknown volume preset: {volume}")

    rng = random.Random(seed)
    scenario_cfg = SCENARIOS[scenario]
    preset = VOLUME_PRESETS[volume]
    months = _month_ids(preset["months"])
    corridor_lookup = _corridor_map()
    pricing = pricing or PricingAssumptions()

    carriers: list[dict[str, Any]] = []
    for idx in range(preset["n_carriers"]):
        fleet_size = rng.randint(*preset["vehicles_per_carrier"])
        carriers.append(
            {
                "carrier_id": f"CAR{idx + 1:04d}",
                "fleet_size": fleet_size,
                "fleet_size_band": (
                    "small" if fleet_size < 8 else "medium" if fleet_size < 14 else "large"
                ),
                "safety_culture_score": round(_clamp(rng.gauss(0.0, 0.85), -2.0, 2.0), 3),
                "telematics_adoption_score": round(_clamp(rng.gauss(0.45, 0.20), 0.05, 1.0), 3),
                "maintenance_program_score": round(_clamp(rng.gauss(0.50, 0.22), 0.05, 1.0), 3),
                "base_region": rng.choice(["Pacific", "Mountain", "Midwest", "South", "Northeast"]),
            }
        )
    carrier_map = {carrier["carrier_id"]: carrier for carrier in carriers}

    policies: list[dict[str, Any]] = []
    for idx in range(preset["policy_count"]):
        carrier = carriers[idx % len(carriers)]
        coverage = _weighted_choice(
            rng,
            {
                "liability_only": 0.18 + scenario_cfg.coverage_narrowing_shift,
                "physical_damage": 0.46,
                "broad_form": max(0.10, 0.36 - scenario_cfg.coverage_narrowing_shift),
            },
        )
        deductible_base = _weighted_choice(
            rng,
            {
                "1000": 0.22,
                "2500": 0.38,
                "5000": 0.28 + scenario_cfg.deductible_shift,
                "10000": 0.12 + scenario_cfg.deductible_shift / 2.0,
            },
        )
        deductible_usd = int(deductible_base) * (2 if carrier["fleet_size_band"] == "small" and rng.random() < 0.15 else 1)
        adas_share = _clamp(
            carrier["telematics_adoption_score"] * 0.7 + scenario_cfg.adas_adoption_shift,
            0.05,
            1.0,
        )
        policies.append(
            {
                "policy_id": f"POL{idx + 1:05d}",
                "carrier_id": carrier["carrier_id"],
                "effective_start": months[0],
                "effective_end": months[-1],
                "deductible_usd": deductible_usd,
                "coverage_limit_usd": rng.choice([250_000, 500_000, 1_000_000]),
                "coverage_breadth": coverage,
                "adas_share": round(adas_share, 3),
                "renewal_flag": int(rng.random() < 0.78),
                "base_rate_per_mile_usd": round(0.72 + rng.random() * 0.42, 3),
            }
        )
    policy_map = {policy["policy_id"]: policy for policy in policies}

    vehicles: list[dict[str, Any]] = []
    drivers: list[dict[str, Any]] = []
    for carrier in carriers:
        for vehicle_number in range(rng.randint(*preset["vehicles_per_carrier"])):
            vehicles.append(
                {
                    "vehicle_id": f"VEH{len(vehicles) + 1:06d}",
                    "carrier_id": carrier["carrier_id"],
                    "vehicle_age_years": round(_clamp(rng.gauss(6.0, 3.0), 0.0, 18.0), 1),
                    "maintenance_risk_score": round(
                        _clamp(
                            rng.gauss(0.55 - 0.25 * carrier["maintenance_program_score"], 0.22),
                            0.02,
                            1.60,
                        ),
                        3,
                    ),
                    "adas_flag": int(rng.random() < (0.30 + scenario_cfg.adas_adoption_shift)),
                }
            )
        for driver_number in range(rng.randint(*preset["drivers_per_carrier"])):
            drivers.append(
                {
                    "driver_id": f"DRV{len(drivers) + 1:06d}",
                    "carrier_id": carrier["carrier_id"],
                    "driver_quality_score": round(_clamp(rng.gauss(0.0, 0.9), -2.0, 2.0), 3),
                    "years_experience": round(_clamp(rng.gauss(8.0, 5.0), 0.0, 35.0), 1),
                }
            )
    vehicles_by_carrier: dict[str, list[dict[str, Any]]] = {}
    drivers_by_carrier: dict[str, list[dict[str, Any]]] = {}
    for vehicle in vehicles:
        vehicles_by_carrier.setdefault(vehicle["carrier_id"], []).append(vehicle)
    for driver in drivers:
        drivers_by_carrier.setdefault(driver["carrier_id"], []).append(driver)

    weather_calendar: list[dict[str, Any]] = []
    for month_index, month_id in enumerate(months):
        for corridor in CORRIDORS:
            regime = _weighted_choice(rng, _weather_probs(corridor, month_index, scenario_cfg))
            intensity, heat, snow, flood, exposure_hours = _weather_intensity(
                rng,
                corridor,
                regime,
                scenario_cfg,
            )
            weather_calendar.append(
                {
                    "month_id": month_id,
                    "route_corridor_id": corridor["route_corridor_id"],
                    "weather_regime": regime,
                    "weather_intensity_z": round(intensity, 3),
                    "heat_stress_index": round(heat, 3),
                    "snow_ice_index": round(snow, 3),
                    "road_flood_risk": round(flood, 3),
                    "event_duration_hours": round(exposure_hours, 3),
                    "scenario_id": scenario,
                }
            )
    weather_lookup = {
        (row["route_corridor_id"], row["month_id"]): row for row in weather_calendar
    }

    trips: list[dict[str, Any]] = []
    claims: list[dict[str, Any]] = []

    cargo_weights = {
        "dry_van": 0.38,
        "refrigerated": 0.20,
        "flatbed": 0.18,
        "hazmat": 0.08,
        "mixed": 0.16,
    }

    for trip_index in range(preset["trip_count"]):
        policy = policies[trip_index % len(policies)]
        carrier = carrier_map[policy["carrier_id"]]
        vehicle = rng.choice(vehicles_by_carrier[carrier["carrier_id"]])
        driver = rng.choice(drivers_by_carrier[carrier["carrier_id"]])
        corridor = rng.choice(CORRIDORS)
        month_id = months[trip_index % len(months)]
        weather = weather_lookup[(corridor["route_corridor_id"], month_id)]

        distance_miles = max(120.0, rng.gauss(corridor["baseline_distance_miles"], 95.0))
        duration_hours = max(3.0, rng.gauss(corridor["baseline_duration_hours"], 2.4))
        cargo_type = _weighted_choice(rng, cargo_weights)
        payload_tons = _clamp(rng.gauss(17.0, 6.0), 2.0, 45.0)
        night_share = _clamp(rng.gauss(0.26, 0.10), 0.0, 0.75)
        avg_speed_mph = _clamp(rng.gauss(61.0, 5.5), 35.0, 82.0)
        hard_brake_rate = _clamp(
            rng.gauss(0.08 + weather["weather_intensity_z"] * 0.03, 0.04),
            0.0,
            0.45,
        )
        overspeed_share = _clamp(
            rng.gauss(0.10 - driver["driver_quality_score"] * 0.02, 0.05),
            0.0,
            0.55,
        )
        hos_pressure = _clamp(
            rng.gauss(0.32 + night_share * 0.20, 0.12),
            0.0,
            1.0,
        )

        cancellation_probability = _clamp(
            0.01
            + scenario_cfg.cancellation_shift
            + (0.08 if weather["weather_regime"] == "snowstorm" else 0.0)
            + (0.04 if weather["weather_regime"] == "flood" else 0.0)
            - scenario_cfg.routing_avoidance_gain * 0.03,
            0.0,
            0.35,
        )
        trip_cancelled_flag = int(rng.random() < cancellation_probability)
        exposure_hours = (
            0.0 if trip_cancelled_flag else max(0.0, weather["event_duration_hours"] - rng.uniform(0.0, 2.0))
        )

        telematics_missing = rng.random() < (
            0.05
            + 0.10 * max(0.0, -carrier["telematics_adoption_score"] + 0.5)
            + scenario_cfg.telematics_missing_shift
        )
        maintenance_missing = rng.random() < (
            0.08
            + 0.12 * max(0.0, vehicle["vehicle_age_years"] / 20.0)
            + scenario_cfg.maintenance_missing_shift
        )
        payload_missing = rng.random() < 0.03

        trip = {
            "trip_id": f"TRP{trip_index + 1:07d}",
            "policy_id": policy["policy_id"],
            "carrier_id": carrier["carrier_id"],
            "vehicle_id": vehicle["vehicle_id"],
            "driver_id": driver["driver_id"],
            "month_id": month_id,
            "route_corridor_id": corridor["route_corridor_id"],
            "origin_region": corridor["origin_region"],
            "destination_region": corridor["destination_region"],
            "distance_miles": round(distance_miles, 2),
            "duration_hours": round(duration_hours, 2),
            "night_share": None if telematics_missing else round(night_share, 3),
            "avg_speed_mph": None if telematics_missing else round(avg_speed_mph, 2),
            "hard_brake_rate": None if telematics_missing else round(hard_brake_rate, 3),
            "overspeed_share": None if telematics_missing else round(overspeed_share, 3),
            "hos_pressure_index": round(hos_pressure, 3),
            "cargo_type": cargo_type,
            "payload_tons": None if payload_missing else round(payload_tons, 2),
            "vehicle_age_years": vehicle["vehicle_age_years"],
            "maintenance_risk_score": None if maintenance_missing else vehicle["maintenance_risk_score"],
            "adas_flag": int(
                vehicle["adas_flag"]
                or rng.random() < policy["adas_share"]
            ),
            "deductible_usd": policy["deductible_usd"],
            "coverage_limit_usd": policy["coverage_limit_usd"],
            "coverage_breadth": policy["coverage_breadth"],
            "premium_month_usd": round(
                policy["base_rate_per_mile_usd"] * distance_miles * rng.uniform(0.90, 1.18),
                2,
            ),
            "premium_month_usd_alloc": round(
                policy["base_rate_per_mile_usd"] * distance_miles / 4.0,
                2,
            ),
            "weather_regime": weather["weather_regime"],
            "weather_intensity_z": weather["weather_intensity_z"],
            "exposure_hours_in_event": round(exposure_hours, 2),
            "road_flood_risk": weather["road_flood_risk"],
            "heat_stress_index": weather["heat_stress_index"],
            "snow_ice_index": weather["snow_ice_index"],
            "claim_occurred": 0,
            "claim_count": 0,
            "incurred_loss_usd": 0.0,
            "paid_loss_usd": 0.0,
            "case_reserve_usd": 0.0,
            "loss_ratio_trip_equiv": 0.0,
            "trip_cancelled_flag": trip_cancelled_flag,
            "scenario_id": scenario,
            "night_share_missing_flag": int(telematics_missing),
            "avg_speed_mph_missing_flag": int(telematics_missing),
            "hard_brake_rate_missing_flag": int(telematics_missing),
            "overspeed_share_missing_flag": int(telematics_missing),
            "maintenance_risk_score_missing_flag": int(maintenance_missing),
            "payload_tons_missing_flag": int(payload_missing),
            "sensor_implausible_flag": 0,
            "winsor_candidate_flag": 0,
            "cat_tail_flag": 0,
            "safety_culture_score": carrier["safety_culture_score"],
        }
        trip["maintenance_risk_score_imputed"] = (
            vehicle["maintenance_risk_score"]
            if trip["maintenance_risk_score"] is None
            else trip["maintenance_risk_score"]
        )
        trip["payload_tons_imputed"] = payload_tons if trip["payload_tons"] is None else trip["payload_tons"]
        trip["hard_brake_rate_imputed"] = hard_brake_rate if trip["hard_brake_rate"] is None else trip["hard_brake_rate"]
        trip["overspeed_share_imputed"] = overspeed_share if trip["overspeed_share"] is None else trip["overspeed_share"]
        trip["night_share_imputed"] = night_share if trip["night_share"] is None else trip["night_share"]

        if trip_cancelled_flag:
            mean_claims = 0.0
        else:
            exposure = max(0.25, distance_miles / 1_000.0 + duration_hours / 24.0)
            weather_log = {
                "normal": 0.0,
                "heavy_rain": 0.34,
                "cold_wave": 0.16,
                "heat_wave": 0.12,
                "snowstorm": 0.42,
                "flood": 0.58,
            }[trip["weather_regime"]]
            log_mu = (
                log(exposure)
                - 4.10
                + weather_log
                + 0.11 * max(0.0, trip["weather_intensity_z"])
                + 0.017 * trip["exposure_hours_in_event"]
                + 0.52 * trip["hard_brake_rate_imputed"]
                + 0.42 * trip["overspeed_share_imputed"]
                + 0.22 * trip["night_share_imputed"]
                + 0.34 * trip["hos_pressure_index"]
                + 0.09 * trip["vehicle_age_years"] / 10.0
                + 0.25 * trip["maintenance_risk_score_imputed"]
                - 0.20 * trip["adas_flag"]
                - 0.05 * log(max(1_000.0, trip["deductible_usd"]) / 1_000.0)
                - 0.04 * trip["safety_culture_score"]
            )
            mean_claims = exp(log_mu)
            low_severity_reporting_drag = _clamp(
                1.0 - 0.05 * log(max(1_000.0, trip["deductible_usd"]) / 1_000.0),
                0.70,
                1.0,
            )
            mean_claims *= low_severity_reporting_drag
        claim_count = _negative_binomial_sample(rng, mean_claims)
        trip["claim_count"] = claim_count
        trip["claim_occurred"] = int(claim_count > 0)

        total_incurred = 0.0
        total_paid = 0.0
        total_reserve = 0.0
        for claim_number in range(claim_count):
            claim_type = _weighted_choice(rng, _claim_type_weights(trip, scenario_cfg))
            incurred_loss, cat_tail_flag = _severity_amount(rng, trip, claim_type, scenario_cfg)
            closure_lag = int(round(max(3.0, rng.lognormvariate(log(28.0 + incurred_loss / 3_500.0), 0.45))))
            open_flag = int(closure_lag > 90 and rng.random() < 0.35)
            if open_flag:
                paid_share = rng.uniform(0.45, 0.78)
            else:
                paid_share = rng.uniform(0.82, 1.0)
            paid = round(incurred_loss * paid_share, 2)
            reserve = round(max(0.0, incurred_loss - paid), 2)
            claim = {
                "claim_id": f"CLM{len(claims) + 1:08d}",
                "trip_id": trip["trip_id"],
                "policy_id": trip["policy_id"],
                "carrier_id": trip["carrier_id"],
                "month_id": trip["month_id"],
                "route_corridor_id": trip["route_corridor_id"],
                "claim_type": claim_type,
                "incurred_loss_usd": incurred_loss,
                "paid_loss_usd": paid,
                "case_reserve_usd": reserve,
                "closure_lag_days": None if open_flag else closure_lag,
                "closure_lag_days_right_censored_flag": open_flag,
                "open_claim_flag": open_flag,
                "cat_tail_flag": int(cat_tail_flag),
                "weather_regime": trip["weather_regime"],
                "scenario_id": scenario,
            }
            claims.append(claim)
            total_incurred += incurred_loss
            total_paid += paid
            total_reserve += reserve
            trip["cat_tail_flag"] = max(trip["cat_tail_flag"], int(cat_tail_flag))
            if incurred_loss > 75_000:
                trip["winsor_candidate_flag"] = 1

        trip["incurred_loss_usd"] = round(total_incurred, 2)
        trip["paid_loss_usd"] = round(total_paid, 2)
        trip["case_reserve_usd"] = round(total_reserve, 2)
        allocated = max(1.0, trip["premium_month_usd_alloc"])
        trip["loss_ratio_trip_equiv"] = round(total_incurred / allocated, 4)
        trip["sensor_implausible_flag"] = int(
            (trip["avg_speed_mph"] is not None and trip["avg_speed_mph"] > 78.0)
            or (trip["hard_brake_rate"] is not None and trip["hard_brake_rate"] > 0.35)
        )
        trips.append(trip)

    policy_month_summary = summarize_policy_months(trips, claims, pricing)
    metadata = {
        "generated_at": date.today().isoformat(),
        "seed": seed,
        "scenario_id": scenario,
        "volume": volume,
        "scenario_parameter_log": asdict(scenario_cfg),
        "volume_parameters": dict(preset),
        "pricing_assumptions": asdict(pricing),
        "table_row_counts": {
            "carriers": len(carriers),
            "policies": len(policies),
            "vehicles": len(vehicles),
            "drivers": len(drivers),
            "corridors": len(CORRIDORS),
            "weather_calendar": len(weather_calendar),
            "trips": len(trips),
            "claims": len(claims),
            "policy_month_summary": len(policy_month_summary),
        },
    }
    return {
        "metadata": metadata,
        "carriers": carriers,
        "policies": policies,
        "vehicles": vehicles,
        "drivers": drivers,
        "corridors": [dict(corridor) for corridor in CORRIDORS],
        "weather_calendar": weather_calendar,
        "trips": trips,
        "claims": claims,
        "policy_month_summary": policy_month_summary,
    }


def generate_data(
    rows: int = 100,
    seed: int | None = None,
    scenario: str = "S0_baseline",
    volume: str = "small_debug",
    **_: Any,
) -> dict[str, Any]:
    """CLI-friendly wrapper exposing trip records as the primary output."""
    dataset = generate_dataset(
        seed=42 if seed is None else seed,
        scenario=scenario,
        volume=volume,
    )
    records = dataset["trips"]
    if rows > 0:
        records = records[:rows]
    return {
        "records": records,
        "metadata": dataset["metadata"],
        "policy_month_summary": dataset["policy_month_summary"],
    }


generate_synthetic_data = generate_data
