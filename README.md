# HeatmapHackathon
Team 13 – Heatmap Hackathon 2026
Project: Advancing Equitable Access to Burn Care
Challenge Statement:
How can data be used to identify and reduce disparities in access to timely, high-quality burn care across different populations and geographies in the U.S.?

Our team explored this question by analyzing geographic access to burn centers, integrating social vulnerability indices, and proposing data-driven recommendations to improve equity in burn care delivery.

👥 Team Members
Name	Role / Focus Area	GitHub
Emmanuel Chea	Lead Analyst – Distance analysis, SVI integration, Use Case framing	@efchea1
Feifei Li	Visualization Lead – Interactive maps, alternative presentation design	@feifei-li
Lance McDonald	GitHub Repo Host, Technical Support	@mcdonaldlk
Shreya Pramanik	[Add role if known]	@Shreya-bristi
Josh Spitzer-Resnick	[Add role if known]	@joshsr
📁 Repository Structure
text
├── code/
│   ├── emmanuel/          # Distance analysis, SVI, etc.
│   ├── feifei/            # Interactive maps, EDA notebooks
│   ├── lance/             # Repo setup, supporting scripts, Tech support 
│   ├── shreya/            # (if applicable)
│   └── josh/              # (if applicable)
│
├── data/                   # Public datasets used (see sources below)
├── outputs/                # Visualizations, maps, charts
├── presentation/
│   ├── main_deck/          # Emmanuel's version (primary)
│   └── alternatives/       # Feifei's visual slides (for reference)
├── README.md               # You are here
└── requirements.txt        # Python dependencies
📊 Datasets Used
NIRD Database (2023) – Hackathon-provided burn care data

CDC SVI 2022 – Social Vulnerability Index (county level)

Census Population Estimates 2020–2025 – Population data

Rural-Urban Continuum Codes 2023 – USDA economic research service

NFIRS – National Fire Incident Reporting System (referenced)

All public datasets are documented in /data/sources.md.

🧠 Key Analyses
Emmanuel
Distance to nearest burn center (population-weighted)

Integration with SVI and rurality

Composite vulnerability scoring

Tele-burn hub recommendations

Feifei
Interactive county-level maps

Visual EDA and alternative presentation design

Population distribution overlays

Lance
GitHub infrastructure

[Add if applicable]

Shreya / Josh
[Add contributions if shared]

📈 How to Run the Code
Clone the repository:

bash
git clone https://github.com/mcdonaldlk/HeatmapHackathon.git
Install dependencies:

bash
pip install -r requirements.txt
Place the NIRD dataset (not included) in /data/

Run individual notebooks from /code/[name]/

🏆 Presentation
Our final submission includes:

Main presentation deck (Emmanuel) – /presentation/main_deck/

Alternative visual deck (Feifei) – /presentation/alternatives/ – for reference and visual inspiration

📝 License
This project is shared for educational and research purposes under the terms of the hackathon. Data remains the property of its original owners. Code is open-sourced under the MIT License.

🙌 Acknowledgments
Thanks to the hackathon organizers, mentors, and the American Burn Association for providing the data and challenge.

📬 Contact
For questions about this repository, please contact Lance or open an issue.

Why This README Works
Element	Purpose
Clear team roles	Shows everyone contributed
Folder structure	Transparent, organized
Separate credit sections	No one is erased
Alternative presentation listed	Your work is visible without competing
Professional tone	Looks great to judges
Would you like help tailoring this further once others share their specific contributions?


Collaborative Repo for Heatmap Hackathon authored by Emmanuel Fle Chea, Josh Spitzer-Resnick, Shreya Pramanik, Feifei Li, Lance Killian McDonald
## Interactive Maps
[Figure 1i: Burn Center Density By State](https://mcdonaldlk.github.io/HeatmapHackathon/Figure_1i.html)

[Figure 2i: Burn Bed Capacity By State](https://mcdonaldlk.github.io/HeatmapHackathon/Figure_2i.html)

[Figure 2i map: Geographic Burn Bed Capacity](https://mcdonaldlk.github.io/HeatmapHackathon/Figure_2i_map.html)

[Figure 3i: The Referral Gap](https://mcdonaldlk.github.io/HeatmapHackathon/Figure_3i.html)

[Figure 3.5i: The Referral Bottleneck](https://mcdonaldlk.github.io/HeatmapHackathon/Figure_3.5i_The_Referral_Bottleneck.html)

[Figure 4i Telemedicine: Burn Center Density By State](https://mcdonaldlk.github.io/HeatmapHackathon/Figure_4i_Telemedicine.html)

[Figure 5i: The Pediatric Access Gap](https://mcdonaldlk.github.io/HeatmapHackathon/Figure_5i_Pediatric_Gap.html)

[Figure 6i: ABA Verification By State](https://mcdonaldlk.github.io/HeatmapHackathon/Figure_6i_ABA_Verification.html)

[Figure 7i: National Equity Priority Map](https://mcdonaldlk.github.io/HeatmapHackathon/Figure_7i_Priority_Map.html)

[Figure 7is: Equity Quadrant - Access Vs Quality](https://mcdonaldlk.github.io/HeatmapHackathon/Figure_7i_Scatter.html)

[Figure 7.5i: Distance Paradox](https://mcdonaldlk.github.io/HeatmapHackathon/Analysis_7_5_Distance_Paradox.html)

[Figure 8i: Social Demand (Need) - State SVI Average](https://mcdonaldlk.github.io/HeatmapHackathon/Figure_8i_Social_Vulnerability.html)

[Figure 9i: Composite Burn Care Vulnerability Index](https://mcdonaldlk.github.io/HeatmapHackathon/Figure_9i_Vulnerability_Index.html)

[Figure 10i: Population Density vs Distance Burden](https://mcdonaldlk.github.io/HeatmapHackathon/Figure10i_Population_Density_vs_Distance_Burden.html)

[Figure 13i: Modeled Impact of Burn Under-Referral](https://mcdonaldlk.github.io/HeatmapHackathon/Figure_13i_Impact_Projection.html)

[Figure 14i: The Burn Care Crisis Narrative](https://mcdonaldlk.github.io/HeatmapHackathon/Figure_14i_Narrative_Arc.html)

[Figure 15i: Sensitivity Analysis Dashboard](https://mcdonaldlk.github.io/HeatmapHackathon/Figure_15i_Sensitivity.html)


