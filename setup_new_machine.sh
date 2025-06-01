#!/bin/bash
echo "🚀 Setting up lecture-text-analysis environment..."

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
pip install fugashi unidic-lite plotly kaleido pingouin statsmodels

# Create required directories
mkdir -p fonts logs
mkdir -p outputs/{wordcloud_configs,wordclouds,vocabulary,sentiment_results,topic_models,statistics,visualizations}

# Download Japanese fonts
python scripts/setup/download_japanese_fonts.py

# Validate environment
python scripts/setup/validate_environment.py

echo "✅ Setup complete! Run 'source venv/bin/activate' to activate the environment."