# Heatmap Hackathon 2026: Advancing Equitable Access to Burn Care

**Challenge Statement**: How can data be used to identify and reduce disparities in access to timely, high-quality burn care across different populations and geographies in the U.S.?

Our team explored this question by analyzing geographic access to burn centers, integrating social vulnerability indices, and proposing data-driven recommendations to improve equity in burn care delivery.

This is a collaborative repository for brainstorming and analysis authored by Emmanuel Fle Chea, Feifei Li, Lance Killian McDonald, Josh Spitzer-Resnick, and Shreya Pramanik. The **final repository** for submission can be found [**here**](https://github.com/efchea1/HeatMap_Burn_2026_Hackathon_Burn_Care_Access_Analysis/).

## 👥 Team 13 Members

| Name | GitHub | Role |
| :- | :- | :- |
| Emmanuel Fle Chea | @efchea1 | Lead Analyst – Distance analysis, SVI integration, Use Case framing |
| Feifei Li | @fayfayMN | Visualization Lead – Interactive maps, alternative presentation design |
| Lance Killian McDonald | @mcdonaldlk | GitHub Repo Host, Technical Support |
| Josh Spitzer-Resnick | @joshspitzerresnick | Geospatial analysis |
| Shreya Pramanik | @Shreya-bristi | Literature review |

## 📊 Datasets Used
All public datasets are documented in `/data/sources.md`

| Name | Description |
| :- | :- |
| NIRD Database (2023) | Hackathon-provided burn care data |
| CDC SVI 2022 | Social Vulnerability Index (county level) |
| Census Population Estimates 2020–2025 | Population data |
| Rural-Urban Continuum Codes 2023 | USDA economic research service |
| NFIRS | National Fire Incident Reporting System (referenced) |

## 🧠 Key Analyses

- Emmanuel
  - Distance to nearest burn center (population-weighted)
  - Integration with SVI and rurality
  - Composite vulnerability scoring
  - Tele-burn hub recommendations

- Feifei
  - Interactive county-level maps
  - Visual EDA and alternative presentation design
  - Population distribution overlays

- Lance
  - GitHub infrastructure

## 📈 How to Run the Code

1. Clone the repository:
```bash
git clone https://github.com/mcdonaldlk/HeatmapHackathon.git
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Place the NIRD dataset (not included) in /data/
4. Run individual notebooks from /code/[name]/

## 🏆 Presentation

Our final submission includes:
- a 1-page overview explaining your solution
- a README with your code submission
- a presentation deck (max 10 slides)

## 📝 License

This project is shared for educational and research purposes under the terms of the hackathon. Data remains the property of its original owners. Code is open-sourced under the MIT License.

## 🙌 Acknowledgments

Thanks to the hackathon organizers, mentors, and the American Burn Association for providing the data and challenge.

## 📬 Contact

For questions about this repository, please contact Lance (@mcdonaldlk) or open an issue.

## Interactive Maps

- [Figure 1i: Burn Center Density By State](https://mcdonaldlk.github.io/HeatmapHackathon/outputs/Figure_1i.html)
- [Figure 2i: Burn Bed Capacity By State](https://mcdonaldlk.github.io/HeatmapHackathon/outputs/Figure_2i.html)
- [Figure 2i map: Geographic Burn Bed Capacity](https://mcdonaldlk.github.io/HeatmapHackathon/outputs/Figure_2i_map.html)
- [Figure 3i: The Referral Gap](https://mcdonaldlk.github.io/HeatmapHackathon/outputs/Figure_3i.html)
- [Figure 3.5i: The Referral Bottleneck](https://mcdonaldlk.github.io/HeatmapHackathon/outputs/Figure_3.5i_The_Referral_Bottleneck.html)
- [Figure 4i Telemedicine: Burn Center Density By State](https://mcdonaldlk.github.io/HeatmapHackathon/outputs/Figure_4i_Telemedicine.html)
- [Figure 5i: The Pediatric Access Gap](https://mcdonaldlk.github.io/HeatmapHackathon/outputs/Figure_5i_Pediatric_Gap.html)
- [Figure 6i: ABA Verification By State](https://mcdonaldlk.github.io/HeatmapHackathon/outputs/Figure_6i_ABA_Verification.html)
- [Figure 7i: National Equity Priority Map](https://mcdonaldlk.github.io/HeatmapHackathon/outputs/Figure_7i_Priority_Map.html)
- [Figure 7is: Equity Quadrant - Access Vs Quality](https://mcdonaldlk.github.io/HeatmapHackathon/outputs/Figure_7i_Scatter.html)
- [Figure 7.5i: Distance Paradox](https://mcdonaldlk.github.io/HeatmapHackathon/outputs/Analysis_7_5_Distance_Paradox.html)
- [Figure 8i: Social Demand (Need) - State SVI Average](https://mcdonaldlk.github.io/HeatmapHackathon/outputs/Figure_8i_Social_Vulnerability.html)
- [Figure 9i: Composite Burn Care Vulnerability Index](https://mcdonaldlk.github.io/HeatmapHackathon/outputs/Figure_9i_Vulnerability_Index.html)
- [Figure 10i: Population Density vs Distance Burden](https://mcdonaldlk.github.io/HeatmapHackathon/outputs/Figure10i_Population_Density_vs_Distance_Burden.html)
- [Figure 13i: Modeled Impact of Burn Under-Referral](https://mcdonaldlk.github.io/HeatmapHackathon/outputs/Figure_13i_Impact_Projection.html)
- [Figure 14i: The Burn Care Crisis Narrative](https://mcdonaldlk.github.io/HeatmapHackathon/outputs/Figure_14i_Narrative_Arc.html)
- [Figure 15i: Sensitivity Analysis Dashboard](https://mcdonaldlk.github.io/HeatmapHackathon/outputs/Figure_15i_Sensitivity.html)
