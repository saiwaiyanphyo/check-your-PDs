---
title: PD Prediction System
colorFrom: purple
colorTo: pink
sdk: gradio
sdk_version: 6.9.0
app_file: app.py
pinned: false
license: mit
short_description: Two-stage PD risk scoring + drawing classifier
---

# 🧠 Parkinson's Disease Prediction System

A two-stage clinical screening tool for Parkinson's disease risk assessment.

## Architecture

- **Stage 1**: Clinical questionnaire → Point-based risk scoring (derived from 1,340 hospital records)
- **Stage 2**: Hand-drawing upload → CNN classifier (PD vs Healthy)
- **Combined**: Weighted fusion (35% risk score + 65% CNN) → Final recommendation

## Usage

1. Complete the clinical questionnaire in Stage 1
2. Upload a hand-drawing (spiral/wave) in Stage 2
3. View the combined assessment in the Combined Result tab

## Disclaimer

This tool is for preliminary screening only and does not constitute a medical diagnosis.
