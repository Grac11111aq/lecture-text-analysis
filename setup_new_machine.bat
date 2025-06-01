@echo off
echo 🚀 Setting up lecture-text-analysis environment...

REM Create and activate virtual environment
python -m venv venv
call venv\Scripts\activate

REM Install all dependencies
pip install -r requirements.txt
pip install fugashi unidic-lite plotly kaleido pingouin statsmodels

REM Create required directories
mkdir fonts logs 2>nul
mkdir outputs\wordcloud_configs 2>nul
mkdir outputs\wordclouds 2>nul
mkdir outputs\vocabulary 2>nul
mkdir outputs\sentiment_results 2>nul
mkdir outputs\topic_models 2>nul
mkdir outputs\statistics 2>nul
mkdir outputs\visualizations 2>nul

REM Download Japanese fonts
python scripts\setup\download_japanese_fonts.py

REM Validate environment
python scripts\setup\validate_environment.py

echo ✅ Setup complete! Run 'venv\Scripts\activate' to activate the environment.