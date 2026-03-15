🛠️ Individual Contribution: Lead Data Analysis (County-Level Methodology)
While the final team deliverables summarize findings at a state level, the ground-truth analysis and geospatial engine were developed with county-level granularity to address the structural and demographic nuances of Challenge 3.
1. Geospatial Pipeline & Haversine Implementation
•	Granularity: Modeled data for all 3,135 U.S. counties using the NIRD 2023 dataset.
•	Weighted Distance: Implemented a population-weighted distance pipeline measuring from U.S. Census 2020 county centroids rather than arbitrary geographic centers.
•	Quality Gap Metrics: Calculated two distinct distance vectors for every county: distance to any burn center vs. distance to ABA-verified care.
2. Socio-Demographic Equity Modeling (SVI Integration)
•	Data Fusion: Merged the CDC/ATSDR Social Vulnerability Index (SVI) 2022 with geographic distance metrics at the county level.
•	Equitable Access Discovery: Identified that poverty acts as a compounding barrier, creating a 2.1x distance burden to any specialized care and a 1.4x burden to reach ABA-verified expertise.
•	Disparity Variables: Explicitly modeled the impact of Vehicle Access, Minority Status, and Poverty on care-seeking timelines.
3. Prescriptive Impact Modeling
•	Hub Identification: Developed an Opportunity Index to score 351 high-priority trauma centers for Tele-Burn deployment based on their proximity to high-vulnerability county clusters.
•	Economic ROI: Built a modeled estimate based on Huang et al. (2021) infection rates ($24,000/infection benchmark) to project an annual saving of $24M and reach 14,514 patients.
4. Model Validation
•	Sensitivity Analysis: Conducted sensitivity testing across 5 weight schemes for the Composite Vulnerability Index (CVI).
•	Statistical Stability: Proven that "Critical-tier" state rankings (CVI > 0.65) remained stable across all scenarios, confirming that the county-to-state aggregation was methodologically robust.
🚀 Future Research & Extended Methodology
The county-level geospatial engine developed for this hackathon serves as a foundation for deeper clinical and social research. While the current scope addresses state-level tiering, I am interested in expanding this analysis to solve for micro-geographic disparities if the data remains available or through future partnerships with the American Burn Association and BData.
Extended Analysis Roadmap:
•	Outcome-Distance Correlation: Performing a patient-level outcomes analysis to link the calculated Haversine distances directly to mortality rates and length-of-stay (LOS) metrics.
•	Longitudinal Access Shifts: Incorporating historical NIRD data to track how care access and referral patterns have evolved over the last decade.
•	Micro-Barrier Integration: Expanding the model coefficients to include county-specific transit infrastructure, insurance/payer mix, and language barriers.
•	Predictive Decision Models: Utilizing the current geographic features to build predictive referral decision models aimed at reducing the 88.1% referral bottleneck found in trauma centers.

