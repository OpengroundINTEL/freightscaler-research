# Climate Variability, Long-Haul Trucking, and Insurance Pricing in the United States

## Abstract

This dissertation investigates how climate-linked weather variability reshapes operational risk, insurance loss structure, and premium adequacy in U.S. long-haul trucking. Existing work on freight vulnerability, climate exposure, and insurance design remains fragmented, leaving unresolved how route-level hazard exposure, driver behavior, cargo sensitivity, and contract structure jointly translate into claim frequency, claim severity, loss ratio instability, and actuarial mispricing. This study addresses that gap by developing a dynamic climate-linked rating framework that treats trucking risk as a corridor-conditioned freight system problem and an insurance portfolio problem at the same time.

The dissertation advances three research questions. First, how do heavy rain, cold waves, heat waves, snowstorms, and floods alter frequency, severity, and loss-ratio structure in U.S. long-haul trucking? Second, how should insurers incorporate route-time exposure, operating behavior, and contract design into dynamic rating so that weather-linked tail risk is not systematically underpriced? Third, what insurer, carrier, and regulatory responses become defensible once climate-related trucking risk is quantified in an integrated empirical framework? The project uses a synthetic but research-grade panel linking trip-level freight exposure, policy-period contract variables, climate shock indicators, and claim outcomes, with a real-data mapping blueprint for future empirical migration.

The central argument is that climate-linked trucking risk is not adequately described by generic weather indicators or by static underwriting averages. Instead, risk emerges when hazard regimes interact with corridor dependence, schedule pressure, behavior, equipment condition, cargo type, and insurance terms. The dissertation therefore proposes a baseline two-part actuarial model separating claim frequency from severity, compares it against hierarchical and nonlinear alternatives, and evaluates how climate-sensitive pricing recommendations change under multiple scenario and robustness regimes. The contribution is theoretical, empirical, and institutional: it integrates freight-systems logic with insurance rate-making and translates results into insurer, carrier, and government-facing governance implications.

## Chapter 1. Introduction

The U.S. long-haul trucking industry moves the majority of freight value across a geographically concentrated interstate system that is increasingly exposed to heavy rain, flood, heat, snow, and cold-related disruption. The practical problem is not only more adverse weather. The deeper issue is that weather shocks interact with route concentration, hours-of-service constraints, cargo vulnerability, and insurance contract structure in ways that can distort both realized loss experience and prospective pricing.

This dissertation asks whether traditional static rating factors can remain adequate under climate variability, or whether trucking insurers must move toward dynamic climate-linked pricing. It argues that climate shocks should be modeled as corridor-level and policy-period exposure states rather than as background annual averages. [P2/P1 lens] The research contributes to transport, logistics, and insurance studies by linking operational disruption to actuarial loss structure and policy design.

## Chapter 2. Literature Review

The literature review integrates four streams: climate variability in transport systems, logistics vulnerability in long-haul trucking, insurance loss modeling and pricing, and catastrophe-risk governance. Prior studies show that freight systems are vulnerable to corridor disruption, schedule compression, and node failure, but they rarely connect those mechanisms to premium adequacy or claims decomposition. Insurance studies often model loss at the contract level while under-specifying route-time exposure construction. This dissertation’s gap lies in unifying hazard measurement, freight exposure, and pricing adequacy inside one coherent framework.

## Chapter 3. Conceptual Framework And Hypotheses

The conceptual framework moves in a structured chain: climate hazard -> route-time exposure -> operational and behavioral mediation -> claim frequency and severity -> loss ratio -> pricing indication -> institutional response. Six hypotheses anchor the framework.

1. Extreme precipitation increases claim frequency more than matched non-extreme wet conditions.
2. Heat-wave exposure increases severity through cargo and mechanical stress channels.
3. Snow and cold effects are mediated by route choice, winterization, and HOS pressure.
4. Static rating variables materially underprice climate-linked tail risk.
5. Deductibles, coverage breadth, and safety technology moderate weather-loss transmission.
6. Some apparent climate effects attenuate after controlling for selection, route structure, and underwriting composition.

Each hypothesis includes an explicit counterexample path, preserving the possibility that adaptation, route avoidance, or contract selection weakens naive weather-loss claims. [P5/P6 lens]

## Chapter 4. Data Architecture

The empirical design uses a synthetic dataset structured around `trip_policy_panel`, `claim`, and `policy_month_summary` layers. The main fields cover route corridor, exposure duration, weather regime, weather intensity, driver behavior, vehicle age, cargo type, deductibles, coverage terms, and claim outcomes. Synthetic scenarios vary rainfall intensity, heat stress, winter disruption, flood tails, adaptation, contract shift, and data-quality degradation. Every synthetic variable has a future mapping path to NOAA weather, telematics, ELD, insurer policy files, and claims systems.

The design keeps missingness and outliers visible through quality flags rather than collapsing them. This matters because trucking climate-risk research is especially vulnerable to route mismatch, reporting bias, and tail-loss distortion if the dataset is over-cleaned before analysis.

## Chapter 5. Empirical Strategy

The baseline empirical strategy is a two-part actuarial model. Claim frequency is estimated with a negative binomial model using exposure offsets, route effects, time controls, weather variables, behavior variables, contract terms, and underwriting covariates. Claim severity is estimated with a Gamma log-link specification conditional on positive claims. Expected loss is the product of expected frequency and expected severity. Premium indication then adds trend, development, fixed expense, variable expense, capital load, and reinsurance load.

Two comparison models test whether the baseline is leaving material signal on the table: a zero-inflated mixed model for structural zeros and a gradient-boosted aggregate loss benchmark for nonlinear interaction discovery. An event-study difference-in-differences design serves as a timing-focused stress test around discrete hazard episodes. [P8/P9 lens]

## Chapter 6. Results Framework

The first-pass results structure proceeds from descriptive to causal to actuarial findings. Descriptive analysis compares peril exposure by corridor family, claim incidence by peril class, severity by cargo class, and loss-ratio variation by deductible tier. The main hypothesis section then estimates frequency, severity, and pricing effects. The most important expected result is not a universal upward weather coefficient, but a differentiated structure in which precipitation loads most strongly on frequency, heat loads most strongly on severity, flood dominates the tail, and contract or mitigation variables reshape the translation from exposure to insured loss.

The dissertation expects at least one attenuation result. In particular, some hazard coefficients should weaken after route, cargo, and contract controls are introduced. That attenuation is a substantive result rather than a failure because it identifies where operational selection and adaptation matter most.

## Chapter 7. Robustness, Validation, And Alternative Explanations

Validation operates on four levels: data integrity, design credibility, model stability, and insurance-usefulness. Placebo timing tests, placebo geography tests, randomized pseudo-events, cargo-mix splits, and underwriting-selection checks all serve as falsification routes. The dissertation also reports threshold sensitivity, exposure-unit sensitivity, sample restrictions, and decision sensitivity. The key standard is whether conclusions remain directionally and economically meaningful when route-time matching, hazard thresholds, and capital-load assumptions change.

## Chapter 8. Policy And Regulatory Implications

For insurers, the main implication is that dynamic climate-linked rating should distinguish among peril classes, corridor accumulation, contract design, and mitigation quality rather than applying a blunt catastrophe load. For carriers, the findings justify adaptation investment in routing flexibility, trailer slack, maintenance quality, and safety technology if those measures reduce weather-loss transmission. For regulators, the dissertation argues that climate-sensitive trucking insurance should be evaluated as an insurability and disclosure problem rather than only a premium-level problem. [P10/P7 lens]

## Chapter 9. Project Management, Reproducibility, And Ethics

The project management architecture uses 3/6/12-month milestones, a deliverable tracking matrix, and a disagreement log. Reproducibility requirements include deterministic seeds, build-order control, versioned data dictionaries, stored model configurations, and regenerable table inputs. The research ethics section notes that synthetic data avoids immediate confidentiality issues but should not be used to overstate empirical certainty about actual carrier or insurer behavior.

## Conclusion

This dissertation frames climate-linked trucking risk as both a freight-system problem and an insurance-design problem. Its main contribution is to show that weather exposure becomes institutionally meaningful only when translated through route dependence, behavior, contract structure, and pricing governance. The monograph’s core value lies not in claiming a universal climate penalty, but in identifying when and why trucking risk becomes mispriced, how that mispricing can be measured, and which responses remain defensible under uncertainty.

