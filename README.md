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
- **Authentication:** Email-based, passwordless login with verification codes
- **Multi-workspace Support:** Users can belong to multiple workspaces, each with its own connected integrations and data

---

## Stretch / Post-MVP Features

- **AI-Generated Summaries:** Automated written summaries of project and team status
- **Daily Report Delivery:** Automated reports via email (and potentially WhatsApp if feasible)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| Backend | FastAPI (Python) |
| ORM | SQLAlchemy |
| Database | PostgreSQL |
| Infrastructure | Docker, Nginx |
| CI/CD | GitHub Actions |
| Data Sources | Jira REST API, Notion REST API |

---

## Team

Developed by **Team Python D** as part of the **TechTalks Lebanon** internship program.

- Youssef Itani — Team Lead
- Paul Riachy
- Abbas Abed Al Nabi
- Nour Al Zahraa Hammoud

Mentor: Khaled Frayji

---

## Sprint Reports & Documentation

- Sprint 1 Report: [Notion Link](https://tasteful-persimmon-4c2.notion.site/Sprint-1-Report-39431913a1a180cbb7a8f8c414ba8201?source=copy_link)
- Sprint 2 Report: [Notion Link](https://tasteful-persimmon-4c2.notion.site/Sprint-2-Report-39331913a1a18048bf17d8f8496b478f?source=copy_link)
- SRS / Documentation: [link]
- Jira Board: [link]
