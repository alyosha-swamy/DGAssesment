# DGAssesment

Social Media Forensics Tool - A digital investigation platform for analyzing social media footprints.

## Overview

This project enables comprehensive forensic analysis of social media data to:

- Extract posts, comments, and metadata from major social platforms
- Analyze sentiment patterns and detect anomalies in user behavior
- Map network connections between users to identify suspicious relationships
- Generate detailed forensic reports for cybersecurity investigations

## Features

- **Data Collection**: Simulates API access to Twitter, Facebook, Instagram, and LinkedIn
- **Sentiment Analysis**: Detects emotion and suspicious content in posts
- **Anomaly Detection**: Identifies unusual posting patterns and behavior
- **Network Analysis**: Maps connections to detect coordinated activity
- **Suspicious Account Detection**: Flags potentially fake or bot accounts
- **Forensic Reporting**: Generates detailed PDF reports with visualizations
- **Interactive Dashboard**: Real-time visualization of analysis results

## Getting Started

Clone this repository and install the required dependencies:

```bash
git clone https://github.com/alyosha-swamy/DGAssesment.git
cd DGAssesment
pip install -r brain_forensics/requirements.txt
```

## Usage

Run a forensic analysis on a username:

```bash
cd brain_forensics
python main.py johndoe
```

Or launch the interactive dashboard:

```bash
cd brain_forensics
python -m visualization.dashboard
```

## License

This project is licensed under the MIT License. 