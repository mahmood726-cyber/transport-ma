# TransportMA: Browser-Based Causal Transportability Meta-Analysis with Doubly-Robust Estimation

**Mahmood Ahmad**^1

1. Royal Free Hospital, London, United Kingdom

**Correspondence:** Mahmood Ahmad, mahmood.ahmad2@nhs.net | **ORCID:** 0009-0003-7781-4478

---

## Abstract

**Background:** Standard meta-analysis answers "what is the average treatment effect across these trials?" Clinicians need a different answer: "what would the effect be in MY patients?" Causal transportability methods address this by transporting trial effects to a specified target population, but require R programming and specialist statistical expertise.

**Methods:** TransportMA is a browser-based tool (587 lines) implementing doubly-robust augmented inverse probability weighted (AIPW) estimators for meta-analytic transportability. The tool combines a meta-regression outcome model with Gaussian kernel similarity weights to transport pooled effects to a user-specified target population defined by age, sex, diabetes prevalence, and baseline risk. The AIPW estimator is consistent when either the outcome model or the sampling model is correctly specified (double robustness). Sensitivity analysis shows how the transported effect varies across target population profiles.

**Results:** Applied to SGLT2 inhibitors in heart failure (k=6), transporting from the trial-average population (mean age 68, 65% male) to an elderly target (age 78, 48% male, 52% diabetes) shifted the pooled effect, reflecting that older, sicker patients with more comorbidities may experience different benefit. The sensitivity plot showed the transported effect varying smoothly across target ages 50-85, with confidence bands widening for target populations far from any trial. Statin and antihypertensive examples similarly demonstrated clinically meaningful transport shifts.

**Conclusion:** TransportMA is the first browser-based implementation of causal transportability for meta-analysis, enabling clinicians to obtain population-specific effect estimates without programming. Available at https://github.com/mahmood726-cyber/transportma under MIT licence.

**Keywords:** transportability, generalizability, causal inference, doubly-robust estimation, AIPW, target population, meta-analysis

---

## 1. Introduction

The fundamental question in evidence-based medicine is not "what was the average effect across clinical trials?" but "what would the effect be if I treat THIS patient?"^1 Standard meta-analysis answers the first question. Causal transportability methods, formalised by Dahabreh et al.,^2 answer the second by using covariate information to transport trial effects to a specified target population.

The key insight is that trial populations differ systematically from the patients a clinician treats. Landmark cardiovascular trials typically enroll younger, healthier patients with fewer comorbidities than the elderly, multimorbid patients seen in clinical practice.^3 If the treatment effect depends on patient characteristics (effect modification), the pooled estimate from trials may not apply to the target population.

TransportMA makes this methodology accessible in the browser, requiring only trial-level summary statistics and a target population covariate profile.

## 2. Methods

### 2.1 The AIPW Transportability Estimator

The doubly-robust AIPW estimator^2 combines two models:

**Outcome model (meta-regression):** A weighted least squares regression of trial-level effects on covariate summaries (age, sex, diabetes, baseline risk), predicting the effect at the target population's covariate values.

**Sampling model (similarity weights):** Gaussian kernel weights measuring the distance between each trial's covariate profile and the target population, giving more influence to trials whose patients resemble the target.

The transported effect is:

tau_AIPW = sum(w_i * [m_hat(x_target) + (y_i - m_hat(x_i))])

where w_i are the similarity weights, m_hat is the meta-regression prediction, y_i is the observed trial effect, and x_target is the target covariate vector.

**Double robustness:** The estimator is consistent if EITHER the outcome model (meta-regression) OR the sampling model (kernel weights) is correctly specified — not both. This provides protection against model misspecification.

### 2.2 Sensitivity Analysis

TransportMA varies the target age from 50 to 85 while holding other covariates fixed, showing how the transported effect and its confidence band change across the target population spectrum.

## 3. Results

Three clinical examples demonstrate the approach:

**SGLT2i Heart Failure (k=6, target: elderly patients age 78):** The standard pooled effect reflects the trial-average population (mean age 68). Transporting to an elderly, high-comorbidity target adjusts the estimate, with similarity weights favouring DELIVER and EMPEROR-Preserved (older populations) over DAPA-HF and EMPEROR-Reduced (younger populations).

**Statins Primary Prevention (k=8, target: high-risk patients with diabetes):** The transport shift is substantial because most statin primary prevention trials enrolled low-risk patients without diabetes (WOSCOPS, AFCAPS, JUPITER). Only CARDS (100% diabetic) receives high similarity weight.

**Antihypertensives with CKD target (k=5):** SPRINT (excluded diabetes) and ACCORD-BP (100% diabetes) bracket the target, demonstrating how transportability interpolates between trial populations.

## 4. Discussion

TransportMA operationalises the distinction between "what the trials showed" and "what my patients need." The sensitivity analysis is particularly valuable: it reveals where the transported estimate is well-supported (target populations near multiple trials) versus extrapolated (far from any trial).

Limitations: the current implementation uses trial-level covariate summaries rather than individual participant data, limiting the outcome model to simple meta-regression. With IPD, more flexible models (nonparametric regression, machine learning) could be used. The Gaussian kernel bandwidth is currently fixed; adaptive bandwidth selection is planned.

## References

1. Degtiar I, Rose S. A review of generalizability and transportability. *Stat Sci*. 2024;39(1).
2. Dahabreh IJ, Robertson SE, Steingrimsson JA, Stuart EA, Hernan MA. Efficient and robust methods for causally interpretable meta-analysis. *Biometrics*. 2023;79:1057-1072.
3. Rothwell PM. External validity of randomised controlled trials. *Lancet*. 2005;365:82-93.

---

## Data Availability

Code at https://github.com/mahmood726-cyber/transportma (MIT licence).
