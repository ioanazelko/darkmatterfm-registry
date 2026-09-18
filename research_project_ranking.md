# Research-project ranking from the capability-gap registry

Each project is one capability theme from the gap roadmap, phrased as a concrete deliverable that would close its tool, likelihood and derivation gaps together. Scores:

- **impact** — summed `adjusted_priority_score` of the distinct models the project unblocks, each weighted by how badly it is blocked (blocks_all_observables 1.0, blocks_key 0.8, degrades_precision 0.4, minor 0.1, unknown 0.3).
- **SF impact** — the same sum counting only gap entries that block structure-formation observables.
- **cost** — mean effort of the member gap entries (small=1, medium=3, large=10, major_program=30; rough person-months of the typical closing work in the theme).
- **value ratio** — impact / cost: science unblocked per unit effort.

Machine-readable version with full member lists: `registry/models/research_projects_ranked.jsonl`; underlying groups: `registry/models/capability_gap_roadmap.jsonl`.

## Ranking by impact

| # | project | impact | SF impact | models | cost | value ratio |
|---|---------|-------:|----------:|-------:|-----:|------------:|
| 1 | A maintained general non-CDM Boltzmann-code framework | 10,048 | 5,214 | 556 | 3.7 | 2,716 |
| 2 | A community model-implementation library for relic-abundance solvers | 9,952 | 1,788 | 660 | 3 | 3,318 |
| 3 | A unified indirect-detection likelihood suite | 8,886 | 1,824 | 578 | 3.5 | 2,539 |
| 4 | A reusable Lyman-α forest likelihood for non-CDM cosmologies | 6,694 | 5,716 | 416 | 4.1 | 1,633 |
| 5 | A public wave-dark-matter solver suite | 4,791 | 2,027 | 272 | 5.3 | 904 |
| 6 | An end-to-end primordial-black-hole pipeline | 3,124 | 932 | 176 | 5.1 | 612 |
| 7 | A collider and beam-dump recast library for DM benchmarks | 2,972 | 231 | 233 | 3.2 | 929 |
| 8 | A CMB energy-injection and ΔN_eff constraint toolkit | 2,653 | 684 | 196 | 3.3 | 804 |
| 9 | A direct-detection recast framework beyond the standard WIMP | 2,561 | 167 | 216 | 2.4 | 1,067 |
| 10 | A dwarf-galaxy structure likelihood | 1,979 | 1,592 | 136 | 5.3 | 373 |
| 11 | An extended sterile-neutrino production code | 1,673 | 1,176 | 78 | 4.8 | 349 |
| 12 | A velocity-dependent SIDM halo-modeling kit | 1,419 | 1,098 | 91 | 5.2 | 273 |
| 13 | Interferometer forecasts and likelihoods for DM-sector signals | 1,156 | 217 | 85 | 6.4 | 180 |
| 14 | A subhalo-abundance-to-satellite-counts pipeline | 1,055 | 997 | 68 | 8.7 | 121 |
| 15 | A BBN code extension for dark-sector energy injection | 917 | 338 | 75 | 3 | 306 |
| 16 | A modern PTA stochastic-background likelihood for dark sectors | 881 | 132 | 73 | 4.1 | 215 |
| 17 | A dark-sector phase-transition and defect computation toolkit | 759 | 86 | 47 | 5 | 152 |
| 18 | A targeted non-CDM simulation campaign with public halo products | 676 | 474 | 40 | 13 | 52 |
| 19 | A 21-cm signal modeling and likelihood package for non-CDM | 534 | 120 | 28 | 5.1 | 105 |
| 20 | A light-mediator constraint compilation with proper likelihoods | 191 | 62 | 13 | 4.8 | 40 |
| 21 | An isocurvature constraint pipeline | 185 | 40 | 16 | 2.8 | 66 |
| 22 | A compact-object capture and heating calculator | 175 | 16 | 14 | 4 | 44 |
| 23 | A stellar-stream perturbation likelihood | 125 | 65 | 7 | 9.6 | 13 |
| 24 | Nonlinear-structure emulators for non-CDM cosmologies | 98 | 62 | 7 | 11.9 | 8 |
| 25 | A strong-lensing substructure likelihood | 78 | 78 | 4 | 8.6 | 9 |

## Ranking by value ratio (impact per unit effort)

| # | project | impact | SF impact | models | cost | value ratio |
|---|---------|-------:|----------:|-------:|-----:|------------:|
| 1 | A community model-implementation library for relic-abundance solvers | 9,952 | 1,788 | 660 | 3 | 3,318 |
| 2 | A maintained general non-CDM Boltzmann-code framework | 10,048 | 5,214 | 556 | 3.7 | 2,716 |
| 3 | A unified indirect-detection likelihood suite | 8,886 | 1,824 | 578 | 3.5 | 2,539 |
| 4 | A reusable Lyman-α forest likelihood for non-CDM cosmologies | 6,694 | 5,716 | 416 | 4.1 | 1,633 |
| 5 | A direct-detection recast framework beyond the standard WIMP | 2,561 | 167 | 216 | 2.4 | 1,067 |
| 6 | A collider and beam-dump recast library for DM benchmarks | 2,972 | 231 | 233 | 3.2 | 929 |
| 7 | A public wave-dark-matter solver suite | 4,791 | 2,027 | 272 | 5.3 | 904 |
| 8 | A CMB energy-injection and ΔN_eff constraint toolkit | 2,653 | 684 | 196 | 3.3 | 804 |
| 9 | An end-to-end primordial-black-hole pipeline | 3,124 | 932 | 176 | 5.1 | 612 |
| 10 | A dwarf-galaxy structure likelihood | 1,979 | 1,592 | 136 | 5.3 | 373 |
| 11 | An extended sterile-neutrino production code | 1,673 | 1,176 | 78 | 4.8 | 349 |
| 12 | A BBN code extension for dark-sector energy injection | 917 | 338 | 75 | 3 | 306 |
| 13 | A velocity-dependent SIDM halo-modeling kit | 1,419 | 1,098 | 91 | 5.2 | 273 |
| 14 | A modern PTA stochastic-background likelihood for dark sectors | 881 | 132 | 73 | 4.1 | 215 |
| 15 | Interferometer forecasts and likelihoods for DM-sector signals | 1,156 | 217 | 85 | 6.4 | 180 |
| 16 | A dark-sector phase-transition and defect computation toolkit | 759 | 86 | 47 | 5 | 152 |
| 17 | A subhalo-abundance-to-satellite-counts pipeline | 1,055 | 997 | 68 | 8.7 | 121 |
| 18 | A 21-cm signal modeling and likelihood package for non-CDM | 534 | 120 | 28 | 5.1 | 105 |
| 19 | An isocurvature constraint pipeline | 185 | 40 | 16 | 2.8 | 66 |
| 20 | A targeted non-CDM simulation campaign with public halo products | 676 | 474 | 40 | 13 | 52 |
| 21 | A compact-object capture and heating calculator | 175 | 16 | 14 | 4 | 44 |
| 22 | A light-mediator constraint compilation with proper likelihoods | 191 | 62 | 13 | 4.8 | 40 |
| 23 | A stellar-stream perturbation likelihood | 125 | 65 | 7 | 9.6 | 13 |
| 24 | A strong-lensing substructure likelihood | 78 | 78 | 4 | 8.6 | 9 |
| 25 | Nonlinear-structure emulators for non-CDM cosmologies | 98 | 62 | 7 | 11.9 | 8 |

## Ranking by structure-formation impact

| # | project | impact | SF impact | models | cost | value ratio |
|---|---------|-------:|----------:|-------:|-----:|------------:|
| 1 | A reusable Lyman-α forest likelihood for non-CDM cosmologies | 6,694 | 5,716 | 416 | 4.1 | 1,633 |
| 2 | A maintained general non-CDM Boltzmann-code framework | 10,048 | 5,214 | 556 | 3.7 | 2,716 |
| 3 | A public wave-dark-matter solver suite | 4,791 | 2,027 | 272 | 5.3 | 904 |
| 4 | A unified indirect-detection likelihood suite | 8,886 | 1,824 | 578 | 3.5 | 2,539 |
| 5 | A community model-implementation library for relic-abundance solvers | 9,952 | 1,788 | 660 | 3 | 3,318 |
| 6 | A dwarf-galaxy structure likelihood | 1,979 | 1,592 | 136 | 5.3 | 373 |
| 7 | An extended sterile-neutrino production code | 1,673 | 1,176 | 78 | 4.8 | 349 |
| 8 | A velocity-dependent SIDM halo-modeling kit | 1,419 | 1,098 | 91 | 5.2 | 273 |
| 9 | A subhalo-abundance-to-satellite-counts pipeline | 1,055 | 997 | 68 | 8.7 | 121 |
| 10 | An end-to-end primordial-black-hole pipeline | 3,124 | 932 | 176 | 5.1 | 612 |
| 11 | A CMB energy-injection and ΔN_eff constraint toolkit | 2,653 | 684 | 196 | 3.3 | 804 |
| 12 | A targeted non-CDM simulation campaign with public halo products | 676 | 474 | 40 | 13 | 52 |
| 13 | A BBN code extension for dark-sector energy injection | 917 | 338 | 75 | 3 | 306 |
| 14 | A collider and beam-dump recast library for DM benchmarks | 2,972 | 231 | 233 | 3.2 | 929 |
| 15 | Interferometer forecasts and likelihoods for DM-sector signals | 1,156 | 217 | 85 | 6.4 | 180 |
| 16 | A direct-detection recast framework beyond the standard WIMP | 2,561 | 167 | 216 | 2.4 | 1,067 |
| 17 | A modern PTA stochastic-background likelihood for dark sectors | 881 | 132 | 73 | 4.1 | 215 |
| 18 | A 21-cm signal modeling and likelihood package for non-CDM | 534 | 120 | 28 | 5.1 | 105 |
| 19 | A dark-sector phase-transition and defect computation toolkit | 759 | 86 | 47 | 5 | 152 |
| 20 | A strong-lensing substructure likelihood | 78 | 78 | 4 | 8.6 | 9 |
| 21 | A stellar-stream perturbation likelihood | 125 | 65 | 7 | 9.6 | 13 |
| 22 | A light-mediator constraint compilation with proper likelihoods | 191 | 62 | 13 | 4.8 | 40 |
| 23 | Nonlinear-structure emulators for non-CDM cosmologies | 98 | 62 | 7 | 11.9 | 8 |
| 24 | An isocurvature constraint pipeline | 185 | 40 | 16 | 2.8 | 66 |
| 25 | A compact-object capture and heating calculator | 175 | 16 | 14 | 4 | 44 |

## Project descriptions (impact order)

### 1. A maintained general non-CDM Boltzmann-code framework

**Deliverable.** A supported CLASS/ETHOS-style branch implementing interacting, decaying, warm, mixed and self-interacting species behind one interface, with standardized transfer-function output that downstream structure-formation pipelines can consume.

Impact 10,048 (structure formation 5,214) · unblocks 556 models (262 via structure-formation observables) · 639 gap entries (calibration, data, derivation, emulator, likelihood, other, simulation, theory, tool) · typical effort medium.

Highest-priority blocked models:

- **Decaying warm majoron dark matter** ([arXiv:1803.05650](https://arxiv.org/abs/1803.05650), score 52, blocks_key_observables): No public Boltzmann-solver setup treats a keV-scale warm majoron with its thermal free-streaming distribution that also decays to relativistic neutrinos with tau_J of order 50 Gyr; the CLASS decaying-CDM module assumes cold parents, so the combined warm-plus-decaying linear evolution (T(k) and CMB spectra) cannot currently be computed.
- **Nonthermal sub-keV light dark matter fraction from radiative decays** ([arXiv:1912.05563](https://arxiv.org/abs/1912.05563), score 52, blocks_key_observables): The momentum distribution of the boosted decay-produced sub-keV component (born relativistic, redshifting through radiation domination) has not been derived in a form usable by a Boltzmann solver, so the mixed cold+hot transfer function for this scenario cannot be computed.
- **Gauged B-L Dirac-neutrino two-component fermion dark matter** ([arXiv:1911.04703](https://arxiv.org/abs/1911.04703), score 48, degrades_precision): The Delta N_eff constraint is applied only as the quoted static bound Delta N_eff <= 0.285 with an analytic decoupling estimate; no pipeline folds the g_BL- and M_ZBL-dependent right-handed-neutrino decoupling into a current CMB+BBN likelihood, which the card flags as a leading constraint that was not updated.

### 2. A community model-implementation library for relic-abundance solvers

**Deliverable.** A curated, validated library of FeynRules/CalcHEP model files plus solver extensions (freeze-in, co-annihilation, resonances, non-standard histories) so registry models get relic densities from micrOMEGAs/MadDM instead of bespoke by-hand estimates.

Impact 9,952 (structure formation 1,788) · unblocks 660 models (101 via structure-formation observables) · 762 gap entries (calibration, data, derivation, likelihood, other, simulation, theory, tool) · typical effort medium.

Highest-priority blocked models:

- **Cosmic-ray boosted sub-GeV gravitationally interacting dark matter with a spin-2 mediator** ([arXiv:1912.09904](https://arxiv.org/abs/1912.09904), score 48, blocks_key_observables): The momentum-dependent spin-2 (KK graviton) CR-DM scattering cross section and boosted-flux calculation exist only as a private modification of DarkSUSY; no public code computes dPhi_chi/dT_chi and its Earth attenuation for the G^{mu nu}T_{mu nu} coupling with its strong q^2 dependence.
- **Two-state inelastic self-interacting dark matter** ([arXiv:1805.03203](https://arxiv.org/abs/1805.03203), score 46, degrades_precision): The cosmological excited-state abundance f_excited is assumed (near 1) rather than computed: the card flags excited-state survival under early-universe down-scattering as an unsolved model-building requirement, leaving the simulations' key initial condition uncalculated.
- **Inelastic dark matter with a dark photon mediator** ([arXiv:1911.03176](https://arxiv.org/abs/1911.03176), score 46, blocks_key_observables): The FeynRules/CalcHEP model file for the two-state Majorana inelastic dark matter with kinetically mixed dark photon is not confirmed public, blocking off-the-shelf reproduction of the micrOMEGAs coannihilation thermal targets over (m_chi1, Delta, m_A', epsilon, alpha_D).

### 3. A unified indirect-detection likelihood suite

**Deliverable.** One package wrapping Fermi dwarf-spheroidal, Galactic-center, AMS-02 antiproton/positron and neutrino-telescope likelihoods with user-supplied annihilation/decay spectra, replacing per-paper digitized limits.

Impact 8,886 (structure formation 1,824) · unblocks 578 models (104 via structure-formation observables) · 709 gap entries (calibration, data, derivation, likelihood, simulation, theory, tool) · typical effort medium.

Highest-priority blocked models:

- **Gauged B-L Dirac-neutrino two-component fermion dark matter** ([arXiv:1911.04703](https://arxiv.org/abs/1911.04703), score 48, blocks_key_observables): No public model implementation exists for this anomaly-free B-L variant: the fractional-charge chiral fermion sector, extended scalar potential, and two-component (psi_1, psi_2) coupled freeze-out with conversion annihilation must be re-encoded before micrOMEGAs can reproduce the paper's relic and direct-detection numbers.
- **Dark-fermion-production relaxion warm dark matter** ([arXiv:1909.07706](https://arxiv.org/abs/1909.07706), score 48, degrades_precision): The dark fermion's post-dilution phase-space distribution f(p) is not derived: the card records only an approximate thermal form, so the transfer-function cutoff rests on a thermal-equivalent m_WDM mapping the paper itself flags as approximate, and no model-specific transfer function exists.
- **Baryon-triality DFSZ axion and light-axino dark matter model** ([arXiv:1807.02530](https://arxiv.org/abs/1807.02530), score 45, blocks_key_observables): No public likelihood exists for X-ray/gamma-ray line limits on a decaying keV axino that is only a fraction of the dark matter; the card notes limits must be rescaled by the axino fraction and records likelihood_available: no for con_axino_xray_gamma.

### 4. A reusable Lyman-α forest likelihood for non-CDM cosmologies

**Deliverable.** A public likelihood package that takes an arbitrary suppressed or oscillatory linear power spectrum (WDM-like, interacting, mixed, fuzzy) and returns constraints from eBOSS/DESI and high-resolution flux-power data, with an emulator-based nonlinear mapping so users never rerun hydrodynamical simulations.

Impact 6,694 (structure formation 5,716) · unblocks 416 models (338 via structure-formation observables) · 437 gap entries (calibration, derivation, emulator, likelihood, simulation, tool) · typical effort medium.

Highest-priority blocked models:

- **Nonthermal sub-keV light dark matter fraction from radiative decays** ([arXiv:1912.05563](https://arxiv.org/abs/1912.05563), score 52, degrades_precision): The structure-formation bound f < 0.01 is inferred from generic mixed cold/hot arguments rather than from a dedicated likelihood: no Lyman-alpha, CMB, or sigma8 likelihood has been run against this model's boosted-subcomponent transfer function, so the actual upper limit on f versus m_DM and tau is uncalibrated.
- **Dark-fermion-production relaxion warm dark matter** ([arXiv:1909.07706](https://arxiv.org/abs/1909.07706), score 48, degrades_precision): No public Lyman-alpha likelihood applies to this model's mixed case: the constraint is imposed only as the thermal-relic 5-5.3 keV m_WDM bound, which does not cover a partial warm fraction f_WDM < 1 or a diluted non-standard spectrum.
- **Fuzzy dark matter with repulsive quartic self-interaction** ([arXiv:1805.08112](https://arxiv.org/abs/1805.08112), score 46, degrades_precision): No nonlinear structure-formation calibration exists for repulsive quartic self-interacting fuzzy dark matter: the paper's bound uses linear observables only, and the card records unknown halo/subhalo mass-function effects with simulation_calibrated no, so nonlinear probes (Lyman-alpha, subhalo counts, solitonic cores with repulsive pressure) cannot be exploited.

### 5. A public wave-dark-matter solver suite

**Deliverable.** Maintained Schrödinger–Poisson / axion-field solvers with soliton, minicluster and oscillon modules, calibrated scaling relations, and hooks to structure-formation observables.

Impact 4,791 (structure formation 2,027) · unblocks 272 models (97 via structure-formation observables) · 409 gap entries (calibration, data, derivation, emulator, likelihood, simulation, theory, tool) · typical effort medium.

Highest-priority blocked models:

- **Decaying warm majoron dark matter** ([arXiv:1803.05650](https://arxiv.org/abs/1803.05650), score 52, degrades_precision): The nonthermal majoron phase-space distribution (from misalignment-like production or entropy-diluted scenarios mentioned in the paper) has not been derived, so all structure-formation predictions rest on the thermal-distribution assumption that the card marks as high extrapolation risk.
- **Dark-fermion-production relaxion warm dark matter** ([arXiv:1909.07706](https://arxiv.org/abs/1909.07706), score 48, degrades_precision): The entropy dilution factor S that rescues the factor-of-10^3 overabundance is a free multiplicative parameter with no specified entropy-injection sector, so the relic abundance prediction is not closed and BBN consistency of the dilution epoch cannot be checked.
- **Fuzzy dark matter with repulsive quartic self-interaction** ([arXiv:1805.08112](https://arxiv.org/abs/1805.08112), score 46, blocks_key_observables): The modified CLASS module implementing the quartic-FDM effective-fluid sound speed c_s^2(a,k) and the quartic-dominated (radiation-like) background phase is not publicly released; without it neither the matter-power cutoff nor the equality-shift observable can be recomputed or the lambda(m) bound updated with current data.

### 6. An end-to-end primordial-black-hole pipeline

**Deliverable.** One pipeline from a primordial P(k) (or collapse mechanism) to an extended PBH mass function and current constraints (microlensing, CMB accretion, GW rates), replacing monochromatic by-hand estimates.

Impact 3,124 (structure formation 932) · unblocks 176 models (48 via structure-formation observables) · 316 gap entries (calibration, data, derivation, likelihood, simulation, theory, tool) · typical effort medium.

Highest-priority blocked models:

- **N MACHOs** ([arXiv:1911.13281](https://arxiv.org/abs/1911.13281), score 47, blocks_key_observables): Microlensing and femtolensing constraints on N-MACHOs are proxied by monochromatic point-lens PBH limits; no likelihood exists that folds in the OGLE and Subaru/HSC survey detection efficiencies, finite-source and finite-lens-size effects, and an extended N-MACHO mass function in the 10^-16 to 10^-8 solar-mass window.
- **Hidden-sector phase-transition axion minicluster dark matter** ([arXiv:1609.00208](https://arxiv.org/abs/1609.00208), score 36, blocks_key_observables): No microlensing likelihood exists for extended AU-scale lenses in this scenario; point-MACHO limits are not directly applicable and survey efficiencies were never assembled.
- **Light scalar dark matter clumps with angular momentum** ([arXiv:1804.07255](https://arxiv.org/abs/1804.07255), score 36, blocks_key_observables): No microlensing event-rate calculator or likelihood handling extended (finite-size) clump lenses is available; published Subaru HSC limits assume pointlike lenses, and the card's compactness constraint says extended clumps weaken direct application of those limits.

### 7. A collider and beam-dump recast library for DM benchmarks

**Deliverable.** Recast implementations (LHC, Belle II, fixed-target/beam-dump) of the registry's recurring signatures, with acceptances and likelihoods, in a CheckMATE/Contur-style framework.

Impact 2,972 (structure formation 231) · unblocks 233 models (17 via structure-formation observables) · 240 gap entries (calibration, data, derivation, likelihood, simulation, tool) · typical effort medium.

Highest-priority blocked models:

- **Inelastic dark matter with a dark photon mediator** ([arXiv:1911.03176](https://arxiv.org/abs/1911.03176), score 46, blocks_key_observables): No public detector-level likelihood or recast module exists for the BaBar monophoton acceptance or the Belle II displaced photon-plus-dilepton/hadron vertex search applied to long-lived chi_2 decays; exclusions depend on unpublished escape-probability, veto, and trigger assumptions.
- **Type-I non-degenerate 2HDM+a dark matter benchmark model** ([arXiv:2404.05704](https://arxiv.org/abs/2404.05704), score 42, blocks_key_observables): No validated LHC recast exists for the non-degenerate type-I 2HDM+a cascade and missing-energy benchmark topologies (h+MET, Z+MET, top-associated MET, visible heavy-Higgs cascades); existing degenerate type-II limits cannot be reused directly.
- **Singlet-doublet freeze-in dark matter in fast-expansion cosmology** ([arXiv:2301.02514](https://arxiv.org/abs/2301.02514), score 41, blocks_key_observables): No public collider recast or likelihood exists for the boosted W/Z/h plus missing-momentum jet-substructure MVA search; the FeynRules/MadGraph model files used by the authors are not public, so the quoted LHC mass reach cannot be reused or reinterpreted.

### 8. A CMB energy-injection and ΔN_eff constraint toolkit

**Deliverable.** Standardized Planck(+ACT/SPT) likelihood wrappers for energy injection, annihilation/decay, and ΔN_eff from dark radiation, consumable without a full cosmology-pipeline setup.

Impact 2,653 (structure formation 684) · unblocks 196 models (45 via structure-formation observables) · 201 gap entries (calibration, data, derivation, likelihood, simulation, theory, tool) · typical effort medium.

Highest-priority blocked models:

- **Dodelson-Widrow sterile neutrino dark matter with active-neutrino self-interactions** ([arXiv:1910.04901](https://arxiv.org/abs/1910.04901), score 43, degrades_precision): No implemented likelihood exists for the constraint overlay: X-ray line searches, BBN mediator bounds, and kaon-decay/DUNE laboratory limits are only compiled as figure regions from the paper, with likelihood_available set to no for both constraint entries.
- **Unified superfluid dark sector** ([arXiv:1810.09474](https://arxiv.org/abs/1810.09474), score 41, degrades_precision): The nonlinear equations for the two-phase (superfluid core plus normal envelope) structure are derived but not solved, and simulation_calibrated = no, so halo and subhalo mass-function effects and cluster-scale predictions are uncalibrated.
- **Flavor-blind Z-prime mediated complex scalar MeV dark matter** ([arXiv:2205.05714](https://arxiv.org/abs/2205.05714), score 40, degrades_precision): No BBN light-element likelihood is implemented for this specific benchmark: the card's BBN/CMB constraint applies to broader light-WIMP classes and explicitly requires branch-by-branch recasting to the flavor-blind Z-prime scalar, which has not been done.

### 9. A direct-detection recast framework beyond the standard WIMP

**Deliverable.** Recast machinery for XENONnT/LZ/CRESST-class results covering sub-GeV kinematics, non-standard form factors, inelastic and boosted scenarios, exposing proper likelihoods rather than published 90% curves.

Impact 2,561 (structure formation 167) · unblocks 216 models (13 via structure-formation observables) · 230 gap entries (calibration, data, derivation, likelihood, other, simulation, theory, tool) · typical effort medium.

Highest-priority blocked models:

- **Cosmic-ray boosted sub-GeV gravitationally interacting dark matter with a spin-2 mediator** ([arXiv:1912.09904](https://arxiv.org/abs/1912.09904), score 48, degrades_precision): No proper experimental likelihood is implemented for the boosted-DM recoil spectrum: the XENON1T constraint is an approximate bin-by-bin recast without official detector response/efficiency tables, and no electron-recoil (S2-only) likelihood recast exists for the spin-2 model at all.
- **Asymmetric dark matter with Chern-Simons photon-current coupling** ([arXiv:2302.11140](https://arxiv.org/abs/2302.11140), score 39, degrades_precision): The loop-induced ADM-quark interaction from the dimension-six current-photon Chern-Simons operator has only an order-of-magnitude heavy-mediator estimate with simplified quark-charge/log factors; no dedicated loop-level matching and RG running to nuclear-recoil operators exists, so the claimed LZ exclusion of the 5 GeV benchmark is low-robustness.
- **Composite asymmetric dark matter with a dark photon portal** ([arXiv:1805.06876](https://arxiv.org/abs/1805.06876), score 38, degrades_precision): The composite dark-baryon form factor for dark-photon-mediated nuclear scattering is not available: direct-detection recasts currently assume pointlike dark matter, while the card flags that compositeness and the light-mediator recoil spectrum can alter the predicted spectra.

### 10. A dwarf-galaxy structure likelihood

**Deliverable.** A likelihood connecting model predictions for inner density profiles, dynamical heating and star-cluster survival in dwarfs to stellar-kinematics datasets, with marginalization over baryonic feedback.

Impact 1,979 (structure formation 1,592) · unblocks 136 models (107 via structure-formation observables) · 155 gap entries (calibration, derivation, emulator, likelihood, simulation, theory, tool) · typical effort medium.

Highest-priority blocked models:

- **Dodelson-Widrow sterile-neutrino warm dark matter** ([arXiv:1011.2217](https://arxiv.org/abs/1011.2217), score 40, degrades_precision): The dwarf-galaxy phase-space-density constraint on the DW sterile neutrino has no likelihood (likelihood_available: unknown), and the halo-history dependence of the coarse-grained Q_cg evolution is uncalibrated, leaving the Tremaine-Gunn-style bound qualitative.
- **Late Sommerfeld-enhanced dark-matter conversion to dark radiation** ([arXiv:1803.03644](https://arxiv.org/abs/1803.03644), score 40, degrades_precision): No dwarf-galaxy self-interaction likelihood exists for the velocity-dependent sigma_T/m_chi(v) prediction; the route only supports an approximate threshold comparison at a single 30 km/s benchmark rather than a proper halo-population recast.
- **Six-flavor quark matter nugget dark matter** ([arXiv:1804.10249](https://arxiv.org/abs/1804.10249), score 40, minor): No quantitative rate and signature model exists for the proposed transient probes: photon emission from nugget collisions with compact stars and with other nuggets is described only qualitatively, with no derived energy-deposition spectrum, event rate, or detectability estimate for the 6FQM benchmark.

### 11. An extended sterile-neutrino production code

**Deliverable.** A quantum-kinetic production solver going beyond Dodelson–Widrow/Shi–Fuller: new mediators, self-interactions, and non-standard expansion histories, emitting phase-space distributions ready for Boltzmann codes.

Impact 1,673 (structure formation 1,176) · unblocks 78 models (57 via structure-formation observables) · 82 gap entries (calibration, derivation, likelihood, tool) · typical effort medium.

Highest-priority blocked models:

- **Dodelson-Widrow sterile neutrino dark matter with active-neutrino self-interactions** ([arXiv:1910.04901](https://arxiv.org/abs/1910.04901), score 43, blocks_all_observables): No public quantum kinetic solver evolves sterile-neutrino production with a light-scalar-mediated active-neutrino self-interaction, i.e. the modified in-medium mixing potential and phi-mediated scattering/on-shell decay collision terms of the paper's master equation; only standard-DW codes (sterile-dm, LASAGNA) are public.
- **Resonantly produced sterile neutrino dark matter in non-standard pre-BBN cosmology** ([arXiv:1911.03398](https://arxiv.org/abs/1911.03398), score 41, blocks_key_observables): No public resonant sterile-neutrino production solver supports a non-standard pre-BBN expansion history: existing quantum-kinetic/Boltzmann codes (e.g. sterile-dm for Shi-Fuller production) hard-code the standard H(T), so the model's central parameterization of a modified Hubble rate above T_tr cannot be scanned with existing tools.
- **Twin sterile neutrino dark matter** ([arXiv:2305.06364](https://arxiv.org/abs/2305.06364), score 41, blocks_key_observables): No public solver evolves the coupled SM and twin-sector baths with twin-sector Dodelson-Widrow sterile-neutrino production (including twin matter potentials), N_A freeze-out and out-of-equilibrium decay, and the resulting entropy injection and T_B/T_A history; the paper's calculation is in-house and unreleased.

### 12. A velocity-dependent SIDM halo-modeling kit

**Deliverable.** Calibrated halo-level models (gravothermal evolution, core formation/collapse) for velocity-dependent cross sections, plus the likelihood connecting sigma(v)/m to rotation curves, clusters and dwarfs.

Impact 1,419 (structure formation 1,098) · unblocks 91 models (69 via structure-formation observables) · 103 gap entries (calibration, derivation, likelihood, simulation, theory, tool) · typical effort medium.

Highest-priority blocked models:

- **Two-state inelastic self-interacting dark matter** ([arXiv:1805.03203](https://arxiv.org/abs/1805.03203), score 46, blocks_key_observables): The Arepo module implementing two-state inelastic (endothermic/exothermic) self-scattering is author code with no extracted public repository, so the simulation step of the only route cannot be reproduced or extended to new (sigma/m, Delta/m_chi, f_excited) points by others.
- **Conformal freeze-in quark-portal dark matter** ([arXiv:1910.10160](https://arxiv.org/abs/1910.10160), score 40, degrades_precision): No curated likelihood or structured bound compilation exists for cluster-scale self-interaction (sigma_self/m_DM) to test the PGB self-scattering estimate; the card records only externally cited merger bounds requiring compilation.
- **Bose-Einstein-condensed scalar field dark matter** ([arXiv:1310.6061](https://arxiv.org/abs/1310.6061), score 39, blocks_key_observables): No public background solver implements the complex SFDM with conserved U(1) charge and quartic self-interaction: the stiff, radiationlike, and CDM-like phase transitions that set N_eff and z_eq must be reproduced from the primary-paper equations, since standard CLASS/CAMB scalar-field modules do not cover this charge-conserving, self-interacting condensate.

### 13. Interferometer forecasts and likelihoods for DM-sector signals

**Deliverable.** Shared LIGO/LISA/ET sensitivity and event-rate machinery for dark-sector mergers, backgrounds and continuous waves.

Impact 1,156 (structure formation 217) · unblocks 85 models (13 via structure-formation observables) · 89 gap entries (calibration, data, derivation, likelihood, simulation, theory, tool) · typical effort medium.

Highest-priority blocked models:

- **Singlet-SUSY singlino self-interacting dark matter** ([arXiv:2204.01928](https://arxiv.org/abs/2204.01928), score 39, blocks_key_observables): No released pipeline implements this model's singlet-sector finite-temperature effective potential in CosmoTransitions or converts the resulting phase-transition parameters into a GW spectrum and LISA/TianQin/Taiji SNR; the paper's scan scripts are private, so the FOPT and GW forecasts cannot currently be reproduced.
- **Stable particle dark matter from hot-big-bang black-hole evaporation** ([arXiv:2303.07372](https://arxiv.org/abs/2303.07372), score 36, minor): The high-reheat CMB target (high-frequency gravitational-wave background from the near-Planckian thermal plasma contributing to N_eff) has no step in the forward-model chain and no calculational pipeline or likelihood: the card marks the likelihood as unknown and recasting as needed, so the observable cannot currently be evaluated.
- **First-order phase-transition vector dark matter** ([arXiv:2403.03252](https://arxiv.org/abs/2403.03252), score 35, degrades_precision): No public joint likelihood exists that confronts the model's correlated predictions (Planck relic abundance plus the FOPT stochastic GW spectrum against LISA/pulsar-timing-class detector sensitivities) in one statistical framework; the card notes no unified likelihood is provided.

### 14. A subhalo-abundance-to-satellite-counts pipeline

**Deliverable.** A pipeline from a suppressed subhalo mass function to the observed Milky Way satellite luminosity function (DES/Rubin selection functions included), packaged as a likelihood any transfer function can be pushed through.

Impact 1,055 (structure formation 997) · unblocks 68 models (64 via structure-formation observables) · 77 gap entries (derivation, likelihood, simulation, tool) · typical effort large.

Highest-priority blocked models:

- **Heavy-scalar-decay non-thermal warm dark matter** ([arXiv:2305.15736](https://arxiv.org/abs/2305.15736), score 50, degrades_precision): Nonlinear predictions (subhalo mass function, satellite counts) rely on thermal-WDM-calibrated simulations through an approximate half-mode-scale matching; no N-body simulations exist for the broader, higher-momentum-peaked decay-produced spectra, so the mapping's validity outside the studied f(q) grid is uncontrolled.
- **Two-state inelastic self-interacting dark matter** ([arXiv:1805.03203](https://arxiv.org/abs/1805.03203), score 46, blocks_key_observables): No public likelihood exists connecting the model's predictions (density profiles, subhalo Vmax functions, local speed distribution) to data; the card lists only 'profile and subhalo summary-statistic likelihoods; no public full likelihood identified' and the elastic-SIDM constraint set explicitly requires recasting for inelastic scattering.
- **Non-resonantly produced sterile-neutrino mixed dark matter** ([arXiv:1412.1592](https://arxiv.org/abs/1412.1592), score 42, degrades_precision): No public spectral likelihood exists for the XMM-Newton/Chandra 3.5 keV line searches; mixing-angle constraints on the sterile subcomponent must be reconstructed from published flux limits and rescaled by r_warm.

### 15. A BBN code extension for dark-sector energy injection

**Deliverable.** PRIMAT/AlterBBN-class extensions handling hadronic/electromagnetic injection, non-standard expansion and MeV-scale sectors, with a packaged likelihood.

Impact 917 (structure formation 338) · unblocks 75 models (22 via structure-formation observables) · 75 gap entries (calibration, data, likelihood, simulation, theory, tool) · typical effort medium.

Highest-priority blocked models:

- **Nonthermal sub-keV light dark matter fraction from radiative decays** ([arXiv:1912.05563](https://arxiv.org/abs/1912.05563), score 52, blocks_key_observables): No implemented pipeline connects the parent decay (E_gamma = 1.59-2.22 MeV, tau ~ 2e4 s) to a nonthermal-nucleosynthesis code, so the predicted lithium reduction and its compatibility with deuterium is asserted from the injection window rather than computed; the card notes no BBN cascade code was run and likelihood_available is 'no'.
- **Gravitino LSP dark matter with right-handed sneutrino NLSP** ([arXiv:0710.2968](https://arxiv.org/abs/0710.2968), score 37, degrades_precision): The BBN constraint on late Bino visible-energy injection exists only as literature bound curves read off by the authors; no machine-readable energy-injection likelihood over (tau_B, B_had Y_B E_vis) is available for this model's decay chain.
- **Right-sneutrino FIMP dark matter with long-lived stau NLSP** ([arXiv:1806.04488](https://arxiv.org/abs/1806.04488), score 36, degrades_precision): The BBN constraint on the stau NLSP is applied only as the crude tau_stau < 100 s criterion; light-element yields for this model's specific hadronic branching fractions are never computed, so the boundary of the allowed lifetime window is uncalibrated.

### 16. A modern PTA stochastic-background likelihood for dark sectors

**Deliverable.** NANOGrav-15yr/EPTA-class likelihoods packaged for dark-sector sources (strings, phase transitions, superradiance) so cards stop relying on pre-2017 exclusions.

Impact 881 (structure formation 132) · unblocks 73 models (8 via structure-formation observables) · 81 gap entries (calibration, data, derivation, likelihood, simulation, theory, tool) · typical effort medium.

Highest-priority blocked models:

- **U(1)' dark-photon self-interacting dark matter from a MeV first-order phase transition** ([arXiv:2306.16966](https://arxiv.org/abs/2306.16966), score 38, blocks_key_observables): No PTA stochastic-background likelihood is connected to the model's dark U(1)' phase-transition parameters; the paper compares the analytic GW spectrum to the nHz band by eye, so no statistical statement against NANOGrav/EPTA/PPTA/CPTA data is possible.
- **Hidden-sector phase-transition axion minicluster dark matter** ([arXiv:1609.00208](https://arxiv.org/abs/1609.00208), score 36, minor): The stochastic gravitational-wave background from the slow, strongly coupled hidden-sector transition is not computed anywhere in the route (the card lists the GW calculator as an unavailable required resource), so obs_hidden_phase_transition_gw cannot be evaluated.
- **PBH-evaporation gravitational dark matter from first-order-phase-transition PBHs** ([arXiv:2304.09194](https://arxiv.org/abs/2304.09194), score 35, blocks_key_observables): No likelihood or public sensitivity module exists for the MHz-GHz stochastic GW background from the phase transition; detectors in this band are only proposed, leaving the route's final comparison without a quantitative target.

### 17. A dark-sector phase-transition and defect computation toolkit

**Deliverable.** CosmoTransitions-class tooling extended to the registry's dark sectors (nucleation, GW spectra, string/wall networks) with validated defaults.

Impact 759 (structure formation 86) · unblocks 47 models (5 via structure-formation observables) · 47 gap entries (calibration, derivation, simulation, theory, tool) · typical effort medium.

Highest-priority blocked models:

- **Conformal hidden-QCD dark meson model** ([arXiv:1910.05025](https://arxiv.org/abs/1910.05025), score 37, blocks_key_observables): The finite-temperature NJL condensate-plus-singlet effective potential and the iterative O(3) bounce calculation that yield S3/T, T_n, alpha, and beta/H are not packaged in any public code, so the GW spectrum and DECIGO/BBO SNR cannot be recomputed away from the two quoted benchmarks.
- **split-seesaw B-L thermal sterile neutrino with entropy dilution** ([arXiv:1907.11696](https://arxiv.org/abs/1907.11696), score 37, blocks_key_observables): No first-order B-L phase-transition calculation exists for this model: the entropy-dilution factor Delta ~ O(1e2) and the momentum redshift factor are assumed inputs rather than outputs of the U(1)_B-L scalar potential, so the abundance and coldness cannot be predicted from Lagrangian parameters.
- **First-order phase-transition vector dark matter** ([arXiv:2403.03252](https://arxiv.org/abs/2403.03252), score 35, blocks_key_observables): No gauge-invariant derivation exists for massive-vector particle production from runaway bubble collisions; the longitudinal-mode contribution is currently estimated through the Goldstone equivalence theorem with an ad hoc gauge-artifact subtraction that the primary paper says lacks a rigorous resolution, so the predicted V_mu yield carries uncontrolled theory systematics.

### 18. A targeted non-CDM simulation campaign with public halo products

**Deliverable.** A coordinated N-body/hydro campaign spanning the registry's recurring non-CDM physics (velocity-dependent SIDM, decays, late-forming DM), releasing halo catalogs and calibrations others can build likelihoods on.

Impact 676 (structure formation 474) · unblocks 40 models (26 via structure-formation observables) · 41 gap entries (calibration, derivation, likelihood, simulation, tool) · typical effort large.

Highest-priority blocked models:

- **N MACHOs** ([arXiv:1911.13281](https://arxiv.org/abs/1911.13281), score 47, blocks_all_observables): No quantitative N-MACHO formation calculation exists: the conversion of hidden-sector particles into compact objects via cooling and collapse in high-density regions (ultra-compact minihalos or an early matter-dominated era) is only sketched, so neither the mass function nor the compact fraction f_compact can be predicted from (N, sector abundances).
- **Unified superfluid dark sector** ([arXiv:1810.09474](https://arxiv.org/abs/1810.09474), score 41, blocks_key_observables): No public halo phase-structure solver computes the superfluid core radius and normal-phase envelope as a function of halo mass and dark-sector thermodynamics for this two-state model, and no rotation-curve pipeline links the phonon-mediated force to galaxy data.
- **Six-flavor quark matter nugget dark matter** ([arXiv:1804.10249](https://arxiv.org/abs/1804.10249), score 40, degrades_precision): The nugget mass function rests on an unmodeled phase-transition history: no calculation exists of bubble nucleation, pocket size R_i, and pocket trapping for a first-order six-flavor QCD transition under electroweak supercooling, nor of nugget evaporation/survival during cooling, leaving the benchmark M_nugget ~ 1e10 g and R_nugget ~ 1e2 cm uncertain by orders of magnitude.

### 19. A 21-cm signal modeling and likelihood package for non-CDM

**Deliverable.** 21cmFAST-class modeling plus EDGES/HERA/SKA likelihoods for models altering the timing of structure formation or injecting energy.

Impact 534 (structure formation 120) · unblocks 28 models (8 via structure-formation observables) · 39 gap entries (data, likelihood, simulation, theory, tool) · typical effort medium.

Highest-priority blocked models:

- **Millicharged dark matter subcomponent with L_mu-L_tau vector depletion** ([arXiv:1803.02804](https://arxiv.org/abs/1803.02804), score 37, blocks_key_observables): No public code computes the cosmic-dawn baryon/dark-matter coupled thermal history for a millicharged subcomponent (fraction f_DM with Coulomb-like velocity-dependent scattering) through to the global 21-cm brightness temperature; the scattering_cooling step has no implementation.
- **Pseudo-scalar mediator dark matter with hidden neutrinos** ([arXiv:1703.02338](https://arxiv.org/abs/1703.02338), score 36, blocks_key_observables): No nonlinear structure-formation calibration exists for transfer functions with enhanced/oscillatory DAO peaks that overshoot CDM power; halo-mass-function prescriptions are calibrated on suppressed or CDM-like spectra, blocking the mapping from the linear spectrum to low-mass halo abundance and the 21 cm signal.
- **Nonthermal warm wino LSP dark matter** ([arXiv:1210.0191](https://arxiv.org/abs/1210.0191), score 35, blocks_key_observables): The predicted imprint sits at k > 100 Mpc^-1, beyond current data; the proposed probe is high-redshift (z ~ 30-200) 21 cm fluctuations, for which no dataset or forward-model likelihood at these scales exists.

### 20. A light-mediator constraint compilation with proper likelihoods

**Deliverable.** A maintained, recastable compilation of dark-photon/fifth-force/light-scalar constraints (beyond static exclusion plots) mapped to arbitrary coupling structures.

Impact 191 (structure formation 62) · unblocks 13 models (4 via structure-formation observables) · 15 gap entries (derivation, likelihood, simulation, theory, tool) · typical effort small.

Highest-priority blocked models:

- **Axion-SU(2) inflation vector boson dark matter** ([arXiv:2312.06889](https://arxiv.org/abs/2312.06889), score 34, degrades_precision): No worked recast maps published dark-photon dark-matter limits onto this model: the effective kinetic mixing epsilon ~ lambda m^2/(g^2 f^2) applies to only one of three degenerate SU(2) components, so limits must be rescaled by component fraction and degeneracy-breaking assumptions, and the cluster sigma/m ~ g^4/m^3 comparison is only a dimensional estimate with unquantified wave-regime corrections.
- **Massive dark photon from axion tachyonic production** ([arXiv:1912.01007](https://arxiv.org/abs/1912.01007), score 34, blocks_key_observables): No public, validated lattice simulation exists for tachyonic production of a massive dark photon from an oscillating ALP condensate (m_X up to m_a/2, alpha_D ~ 10-100 with backreaction), so the vector occupation spectrum that sets Omega_X, gamma_eq, and the GW source is only estimated analytically; the paper's improved Python code is not released.
- **Light decoupled techni-dilaton dark matter** ([arXiv:1201.4988](https://arxiv.org/abs/1201.4988), score 28, blocks_key_observables): No digitized likelihood or exclusion tables exist in the card for the diffuse X-ray bound on the eV-scale TD two-photon decay (only quoted upper masses of about 140-460 eV) or for sub-millimeter inverse-square-law/fifth-force searches, so the decay_and_detection step cannot be closed at experiment level.

### 21. An isocurvature constraint pipeline

**Deliverable.** From a model's isocurvature production mechanism to Planck isocurvature likelihoods, for axion-like and multi-field scenarios.

Impact 185 (structure formation 40) · unblocks 16 models (4 via structure-formation observables) · 16 gap entries (derivation, likelihood, tool) · typical effort medium.

Highest-priority blocked models:

- **Higgs-portal pseudo-Nambu-Goldstone hot-and-cold dark matter** ([arXiv:1310.1774](https://arxiv.org/abs/1310.1774), score 38, degrades_precision): The small-scale isocurvature/ultracompact-minihalo constraint on late-annihilating walls is applied only as the qualitative H_decay > 22 eV threshold; no derivation exists of the isocurvature power spectrum sourced by the wall network for this model, so the exclusion boundary cannot be computed quantitatively.
- **Spin-2 dark matter from inflation** ([arXiv:2305.13381](https://arxiv.org/abs/2305.13381), score 28, degrades_precision): The CMB isocurvature bound is applied through an order-of-magnitude estimate whose mapping from spin-2 spectator perturbations to observed isocurvature the paper explicitly leaves beyond scope for order-one sound speeds and EFT coefficients, so viability in that regime cannot be judged.
- **Primordial black-hole dark matter from stiff-era reheating collapse** ([arXiv:2309.14993](https://arxiv.org/abs/2309.14993), score 26, minor): The predicted small-scale baryon-to-photon fluctuation spectrum delta eta_B(k) is never converted into an observational likelihood (BBN/CMB constraints on baryon isocurvature or inhomogeneous nucleosynthesis), so this observable cannot be evaluated against data.

### 22. A compact-object capture and heating calculator

**Deliverable.** A public calculator for DM capture, thermalization and heating in neutron stars/white dwarfs, with observational comparison to cooling data.

Impact 175 (structure formation 16) · unblocks 14 models (2 via structure-formation observables) · 14 gap entries (derivation, likelihood, theory, tool) · typical effort medium.

Highest-priority blocked models:

- **Mirror-star dissipative mirror-baryon dark matter** ([arXiv:1909.04072](https://arxiv.org/abs/1909.04072), score 37, degrades_precision): No released code implements the SM capture/self-capture rate and the captured-nugget thermal structure (ionization, opacity, temperature across optically thin/thick regimes), which is the step converting stellar profiles and epsilon into observable luminosities.
- **Single keV sterile-neutrino warm dark matter** ([arXiv:1009.5870](https://arxiv.org/abs/1009.5870), score 31, minor): No detector response and background model exists for the beta-endpoint capture signature: the card computes the ideal capture rate and line position but notes that target activity, energy resolution, and backgrounds were not modeled, so laboratory sensitivity cannot be quantified.
- **Freeze-twin electron and positron dark matter** ([arXiv:1908.03559](https://arxiv.org/abs/1908.03559), score 31, degrades_precision): No supernova-cooling likelihood or recast exists for the twin sector: existing dark-photon SN1987A cooling bounds do not include the twin-electron pair-production and trapping channels of this model, so the epsilon-m_gamma_prime cooling region is only a qualitative overlay.

### 23. A stellar-stream perturbation likelihood

**Deliverable.** A likelihood from subhalo population predictions to observed stream density/track perturbations (GD-1, Pal 5, Rubin-era samples), usable by any model that predicts a subhalo mass function.

Impact 125 (structure formation 65) · unblocks 7 models (3 via structure-formation observables) · 7 gap entries (likelihood, simulation, tool) · typical effort large.

Highest-priority blocked models:

- **High-decay-constant QCD axion dark matter with PBH-seeded UCMHs** ([arXiv:2205.02255](https://arxiv.org/abs/2205.02255), score 33, blocks_key_observables): UCMH growth around PBH seeds and their tidal disruption into axion streams in the Galactic potential are modeled only with semi-analytic profiles and an assumed encounter rate; no simulation-calibrated model of stream density enhancement and Earth-encounter statistics exists.
- **Fragmenting non-periodic-potential axion-like dark matter** ([arXiv:2305.03756](https://arxiv.org/abs/2305.03756), score 26, blocks_key_observables): No event-level likelihood exists for dense-minihalo encounters with stellar streams (GD-1-like gaps) or pulsar-timing arrays for this model; the card frames both channels as qualitative prospects with encounter-rate and population modeling absent.
- **Vector wave dark matter in the nonrelativistic Schrödinger-Poisson limit** ([arXiv:2203.11935](https://arxiv.org/abs/2203.11935), score 25, blocks_key_observables): No likelihood exists for vector wave dark matter against dwarf-galaxy core, stellar-stream heating, or substructure data, and the lowest-energy vector soliton is density-degenerate with the scalar case, so scalar fuzzy-DM bounds cannot be recast without vector-specific (spin/polarization and multi-component) corrections.

### 24. Nonlinear-structure emulators for non-CDM cosmologies

**Deliverable.** Emulators mapping modified linear spectra to nonlinear power, halo mass functions and profiles, trained on the simulation campaign above.

Impact 98 (structure formation 62) · unblocks 7 models (5 via structure-formation observables) · 7 gap entries (calibration, likelihood, simulation) · typical effort large.

Highest-priority blocked models:

- **Vector-portal hidden-sector dark matter with an early matter-dominated era** ([arXiv:1906.00010](https://arxiv.org/abs/1906.00010), score 31, degrades_precision): Microhalo survival and gravitational heating at reheating dominate the boost-factor uncertainty: the boost is highly sensitive to the free-streaming cutoff and to how many prompt microhalos survive, and no simulation suite spans the (T_dom/T_RH, lambda_fs, m_X/m_Zprime) space needed to calibrate this beyond the paper's bracketing procedures.
- **Resonantly produced sterile neutrino dark matter** ([arXiv:astro-ph/0101524](https://arxiv.org/abs/astro-ph/0101524), score 30, blocks_key_observables): No public Ly-alpha flux-power likelihood or emulator accepts arbitrary resonant nonthermal sterile-neutrino distributions; the RPSN hydrodynamical grid covers only benchmark distribution shapes, and out-of-grid f_s(p) require new simulations (card assumption rpsn-hydrodynamical-grid, likelihood_available: no).
- **General interacting dark sector with dark matter and dark radiation** ([arXiv:1708.09406](https://arxiv.org/abs/1708.09406), score 23, degrades_precision): Nonlinear structure formation for IDS is uncalibrated (simulation_calibrated: no; halo and subhalo effects unknown), so weak-lensing and cluster-count constraints on the S8-suppression regime rely on nonlinear prescriptions never validated for DAO-like IDS spectra.

### 25. A strong-lensing substructure likelihood

**Deliverable.** Flux-ratio and gravitational-imaging likelihoods for suppressed or enhanced substructure, packaged for arbitrary transfer functions.

Impact 78 (structure formation 78) · unblocks 4 models (4 via structure-formation observables) · 5 gap entries (emulator, likelihood, tool) · typical effort large.

Highest-priority blocked models:

- **Inflation-produced dark photon dark matter with Proca-star substructure** ([arXiv:2203.10100](https://arxiv.org/abs/2203.10100), score 43, blocks_key_observables): No survey-recast machinery or likelihood exists to convert the predicted soliton/compact-halo population (M_s, M_h, density profiles) into pulsar-timing, microlensing, photometric microlensing, or extragalactic strong-lensing constraints, and finite-size, fuzzy-envelope lenses are not covered by point-mass PBH limits.
- **One-to-one resonantly produced mixed sterile-neutrino dark matter** ([arXiv:2306.16532](https://arxiv.org/abs/2306.16532), score 30, degrades_precision): Ly-alpha forest and strong-lensing constraints for this model rely on thermal-WDM-calibrated pipelines, but the resonant spectra are explicitly nonthermal and mixed with CDM, so no emulator or likelihood covers the model-specific T(k) shapes (thermal-WDM equivalent masses are only approximate per the card).
- **Two-body interacting superfluid dark matter around black holes** ([arXiv:2302.10286](https://arxiv.org/abs/2302.10286), score 21, blocks_key_observables): No ray-tracing/imaging forward model exists that takes the two-body superfluid n=1 Lane-Emden density profile around an SMBH and predicts photon-sphere shifts, shadow size, or strong-lensing deflections.
