# Social Media Forensics Tool

A tool for extracting, analyzing, and visualizing digital footprints from social media platforms.

## Overview

This project enables forensic analysis of social media data to:

- Extract posts, comments, and metadata from social platforms
- Analyze sentiment patterns and detect anomalies
- Map network connections between users
- Identify suspicious accounts and behavior
- Generate comprehensive forensic reports

## Features

- **Social Media Data Collection**: Simulates API access to major platforms (Twitter, Facebook, Instagram, LinkedIn)
- **Sentiment Analysis**: Detects emotion and subjective content in posts
- **Anomaly Detection**: Identifies unusual posting patterns and behavior
- **Network Analysis**: Maps connections between users to detect coordinated behavior
- **Suspicious Account Detection**: Flags potentially fake or bot accounts
- **Forensic Reporting**: Generates detailed PDF reports with visualizations
- **Interactive Dashboard**: Visualizes findings through a web interface

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd brain_forensics
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables by creating a `.env` file:
   ```
   TAVILY_API_KEY=your_api_key
   ```

## Usage

### Command Line Interface

Run a forensic analysis on a username:

```bash
python main.py johndoe
```

Analyze a specific platform:

```bash
python main.py johndoe --platform twitter
```

### Interactive Dashboard

Launch the web dashboard:

```bash
python -m visualization.dashboard
```

Then open your browser to `http://localhost:8050` to access the dashboard.

## Project Structure

- `/api`: Modules for accessing social media data
- `/analysis`: Sentiment analysis and network analysis tools
- `/reports`: Report generation functionality
- `/visualization`: Interactive dashboard
- `/data`: Storage for cached data and analysis results

## Example Output

The tool generates:

1. **PDF Reports** - Comprehensive forensic analysis with user profile, sentiment analysis, network connections, and risk assessment
2. **Network Visualizations** - Visual graphs showing connections between users
3. **Interactive Dashboard** - Real-time visualization of analysis results

## Limitations

This is a prototype with the following limitations:

- Uses simulated data instead of real API access
- Limited analysis capabilities compared to commercial tools
- May produce false positives when detecting suspicious behavior

## Future Enhancements

- Integrate with actual social media APIs
- Add more advanced natural language processing capabilities
- Improve bot detection algorithms
- Expand to analyze dark web connections
- Add deepfake detection for images/videos

## License

This project is licensed under the MIT License - see the LICENSE file for details. 