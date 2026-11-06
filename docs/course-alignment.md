> Integration update: the operational simulator and dashboard are now implemented. See [TEAM_HANDOFF](../TEAM_HANDOFF.md) and [logistics implementation](logistics.md). Phase-1 scope statements below describe the original demand component.

# Feasibility and ISE450 alignment

Reviewed source: Project Guideline_4b.docx attached to the referenced Build GenAI Model Repo conversation. The supplied guideline describes a group project worth 30%: presentation 15%, PPT and simulation file 15%. It requires a 10-minute presentation, an off-campus case, objectives, technology/method, model building, data sources, model summary, testing where applicable, findings, conclusions, future plan and member responsibilities. It explicitly lists AI/Generative AI among suggested Logistics 4.0 technologies. No dates were present in the extracted schedule fields.

The proposed Hong Kong e-commerce delivery operation is a feasible off-campus case. Its stated 5,000 parcels/day and 15% delay rate must be labeled hypothetical until sourced. Choose minimizing delay rate as the shared project objective. Demand forecasting and scenario generation support the simulation rather than completing that objective by themselves.

| Guideline element | Phase 1 contribution | Remaining team work |
|---|---|---|
| Industrial case and objectives | Defined synthetic delivery-demand case | Agree operational assumptions and objective |
| Technology and method | Conditional statistical generator plus baseline | Optional neural CVAE implemented; compare against statistical baseline |
| Data collection | Seeded synthetic history; explicit provenance | Company data collection plan and calibration |
| Model building and diagrams | History → chronological split → fit/evaluate → refit → scenario CSV → simulation interface | System layout and entity flow diagram |
| Entities, arrivals, distributions | District-day counts and context schema | Confirm assumed hourly profile; implement parcels, queues, vehicles, routing/service distributions |
| Testing | Determinism, leakage, scenario controls, held-out diagnostics | Hypothetical 15% target calibration, fleet sensitivity and surge+disruption simulation tests |
| Findings | Forecast error and scenario demand totals | Delay-risk ranking, policy comparison, confidence intervals |
| Conclusions/business achievement | Phase 1 feasibility and limitations | Evidence of simulated delay reduction; avoid claiming real operational gains |
| Submission | Reproducible code and demand exports | PPT, executable simulation file, 10-minute presentation and Q&A |
| Responsibilities | Demand/model contributor owns this phase | Assign simulation, experiments, presentation and integration owners |

A bootstrap generator is practical, fast, explainable and reproducible, but acceptance as the intended modern GenAI technology is uncertain. Obtain lecturer clarification before committing the presentation title to a neural or LLM claim. Phase 1 alone is not a complete course submission. Avoid reporting synthetic validation as a comparison against actual company behavior.

See [named teammate handoff](handoff.md). The 15% delay target is hypothetical, not historical observed data. Sample operational results are illustrative only. The optional CVAE is neural; the default statistical model remains available.
