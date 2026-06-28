# Techtalks Project Pulse

> A unified project management and analytics web application developed as an internship project within the TechTalks Lebanon program.

---

## About the Project

Project Pulse is a web application that aggregates and normalizes project data from multiple sources (primarily **Jira** and **Notion** via their REST APIs) and presents it through clean, unified dashboards, graphs, and tables. The goal is to give teams a single place to monitor productivity, track progress, and gain actionable insights across their tools.

---

## The Problem It Solves

Teams that use multiple project management tools (Jira, Notion, etc.) often struggle to get a unified view of their work. Switching between platforms, manually compiling reports, and tracking team performance across disconnected tools wastes time and creates blind spots. Project Pulse solves this by pulling all that data into one place and surfacing it through meaningful analytics.

---

## Main Features (MVP)

- **Jira & Notion Integration:** Extract and normalize project data from both platforms via their APIs into a unified internal schema
- **Unified Dashboard:** Visual display of normalized data through tables, charts, and graphs
- **Productivity Analytics:** Calculated insights including task completion rates, team velocity, workload distribution, and performance metrics
- **Authentication:** User and team-based login and access control
- **Multi-team Support:** Users can belong to multiple teams, each with its own connected integrations and data

---

## Stretch / Post-MVP Features

- **AI-Generated Summaries:** Automated written summaries of project and team status
- **Daily Report Delivery:** Automated reports via email (and potentially WhatsApp if feasible)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python) |
| ORM | SQLAlchemy |
| Frontend | HTML / CSS / JavaScript (Vanilla) |
| Data Sources | Jira REST API, Notion REST API |

---

## Team

Developed by a team of 6 as an internship project within the **TechTalks Lebanon** program.
