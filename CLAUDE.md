# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a text mining project focused on analyzing elementary school student responses from a science outreach program conducted by Tokyo Institute of Technology (Tokyo Tech). The project analyzes 200 text records including student comments and reasoning explanations about salt dissolution experiments, with a focus on measuring educational effectiveness through vocabulary acquisition analysis.

**Project Status**: Implementation-ready with complete analysis pipeline
**Analysis Period**: 4 weeks (28 days) - structured implementation workflow
**Primary Goal**: Scientific measurement of educational impact with statistical rigor

## Data Architecture

### Core Data Sources
- `data/raw/comments.csv` - Student reflections on the science lesson (21 records)
- `data/raw/q2_reasons_before.csv` - Pre-lesson explanations about why miso soup is salty (84 records)  
- `data/raw/q2_reasons_after.csv` - Post-lesson explanations about why miso soup is salty (95 records)

### Processed Data
- `data/processed/all_text_corpus.csv` - Unified corpus with columns: text, category, class, page_id
- `data/processed/metadata.json` - Project metadata and processing log

### Context Documents
- `data/context/DATA_CONTEXT.md` - Detailed survey methodology and experimental setup
- `docs/project_objectives.md` - Project goals, stakeholders, and success criteria
- `docs/evaluation_criteria.md` - Statistical analysis standards and reporting guidelines

### Implementation Documents (2025-05-31)
- `docs/workflows/implementation_workflow.md` - Complete 4-week implementation plan (67 tasks)
- `docs/workflows/implementation_summary.md` - Quick start guide and success criteria
- `docs/setup/environment_setup_guide.md` - Detailed environment setup with troubleshooting
- `docs/tasks/master_todo.md` - Task management and progress tracking

## Development Environment

### Quick Setup & Validation
```bash
# Environment validation (automatic dependency check)
python scripts/setup/validate_environment.py

# If validation passes, start analysis:
python scripts/analysis/02_vocabulary_analysis.py
```

### Dependencies Installation
```bash
# Basic dependencies
pip install -r requirements.txt

# Extended analysis packages
pip install fugashi unidic-lite plotly kaleido pingouin statsmodels
```

### Key Libraries
- **Japanese NLP**: janome (primary), MeCab (optional), spacy + ginza
- **Visualization**: matplotlib, seaborn, wordcloud, plotly (interactive)
- **ML/Topic Modeling**: scikit-learn, gensim
- **Sentiment Analysis**: textblob
- **Statistical Analysis**: scipy, pingouin, statsmodels

### System Requirements & Permission Issues
**MeCab (Optional)**: May need system privileges for installation:
- Ubuntu: `sudo apt-get install mecab mecab-ipadic-utf8`
- macOS: `brew install mecab mecab-ipadic`

**Permission Workaround**: Project uses janome as primary tokenizer (pure Python, no system installation required)

## Analysis Framework

### Educational Context
This is an educational impact assessment project measuring:
- Learning effectiveness (before/after concept understanding)
- Interest/engagement changes
- Teaching method effectiveness
- Qualitative learning experiences

### Key Constraints
- **No individual tracking**: Page_IDs are not personal identifiers
- **Independent group analysis**: Before/after groups treated as separate samples
- **Statistical rigor required**: Effect sizes (Cohen's d > 0.2), confidence intervals, multiple comparison corrections
- **Cautious interpretation**: Correlation vs. causation, limited generalization

### Core Analysis Targets
1. **Scientific Vocabulary Acquisition**: "塩" → "ナトリウム" transition analysis
2. **Class-wise Effect Comparison**: 4-class differential impact assessment
3. **Sentiment & Interest Analysis**: Experiment reaction quantification
4. **Educational Method Evaluation**: Flame reaction vs. recrystallization effectiveness

### Target Outputs
- `outputs/vocabulary/` - Vocabulary change analysis with statistical tests
- `outputs/wordclouds/` - Visual frequency analysis (overall + class-specific)
- `outputs/sentiment_results/` - Emotional response analysis  
- `outputs/topic_models/` - Thematic content extraction
- `outputs/statistics/` - Comprehensive statistical test results
- `outputs/visualizations/` - Effect size plots, heatmaps, forest plots

## Analysis Standards

### Statistical Criteria
- **Significance threshold**: p < 0.05
- **Minimum meaningful effect**: Cohen's d > 0.2 (small effect), > 0.5 (medium), > 0.8 (large)
- **High interest threshold**: Mean > 3.5 on 4-point scale
- **Multiple comparison correction**: Bonferroni method for family-wise error control
- **Non-parametric preference**: Mann-Whitney U, Kruskal-Wallis for robust analysis

### Text Analysis Approach & Vocabulary Hierarchy
- **Basic food terms**: みそ, みそ汁, みそしる
- **Basic salt terms**: 塩, 食塩, 塩分
- **Scientific terms**: ナトリウム, 塩化ナトリウム, Na
- **Advanced terms**: Na+, NaCl, イオン

**Analysis Focus**:
- Scientific vocabulary acquisition quantification
- Conceptual explanation improvement tracking
- Effective teaching element identification from student feedback
- Class-level differential analysis (4 classes: 1.0, 2.0, 3.0, 4.0)

### Stakeholder Reporting
Four distinct audiences requiring different emphasis:
1. **Project team** - Comprehensive technical results
2. **Faculty** - Academic rigor and theoretical connections
3. **Elementary teachers** - Practical classroom insights
4. **Institution** - Social impact demonstration

## Implementation Workflow

### Phase Structure (4 Weeks, 67 Tasks)
- **Week 1**: Environment setup, data foundation, exploratory analysis
- **Week 2**: Core vocabulary analysis, sentiment analysis, initial results
- **Week 3**: Advanced modeling, statistical validation, robustness testing
- **Week 4**: Integration, reporting, stakeholder-specific deliverables

### Key Scripts & Entry Points
```bash
# Environment validation & setup
python scripts/setup/validate_environment.py

# Data quality check & loading
python scripts/utils/data_loader.py

# Core vocabulary change analysis (PRIMARY)
python scripts/analysis/02_vocabulary_analysis.py

# Additional analyses (to be implemented)
python scripts/analysis/01_data_exploration.py
python scripts/analysis/03_class_comparison.py
python scripts/analysis/04_sentiment_analysis.py
python scripts/analysis/05_topic_modeling.py
python scripts/analysis/06_statistical_testing.py
```

### Configuration Management
- **Main config**: `config/analysis_config.yaml` - All analysis parameters
- **Path management**: Centralized file path configuration
- **Visualization settings**: Consistent styling across all outputs

## Important Notes

### Privacy & Ethics
- All analysis maintains student privacy (no individual identification)
- Page_IDs are not personal identifiers - safe for class-level analysis
- Results focus on aggregate patterns, not individual student performance

### Statistical Interpretation Guidelines
- **Effect size priority**: Report Cohen's d alongside p-values
- **Confidence intervals**: 95% CI required for all effect estimates
- **Multiple comparison awareness**: Bonferroni correction for class comparisons
- **Causation limitations**: Correlation-based findings, avoid causal claims
- **Generalization boundaries**: Results specific to this experimental context

### Practical Implementation Notes
- **Permission handling**: MeCab installation may require system privileges - use janome fallback
- **Memory management**: Large text processing handled via chunking
- **Error resilience**: Comprehensive error handling with detailed logging
- **Reproducibility**: All analyses use fixed random seeds where applicable

### Success Metrics
- **Technical**: All scripts execute without errors, statistical assumptions validated
- **Statistical**: Significant vocabulary change (p < 0.05), meaningful effect sizes (d > 0.2)
- **Educational**: Clear class differentiation, actionable teaching recommendations
- **Reporting**: Four stakeholder-specific reports completed and validated

## Major Updates (2025-06-01)

### Completed Analysis Implementation
- **Core Analysis Scripts**: Successfully executed vocabulary and sentiment analysis
- **Key Findings**: 
  - Dramatic vocabulary shift: 0% → 42.1% sodium usage (Cohen's d = 1.164)
  - 0% negative sentiment, high experiment engagement (57.1% flame reaction mentions)
  - Class 3.0 showed highest educational impact
- **Final Report**: Generated comprehensive analysis report at `outputs/final_analysis_report.md`

### Japanese Wordcloud Web Application (Updated: 2025-06-01)
- **Purpose**: Interactive tool for real-time wordcloud configuration with Japanese font support
- **Location**: `wordcloud_app/` directory
- **Updated Branding**: Tokyo Kosen (東京高専) specialized for outreach program analysis
- **Production Data Integration**: Uses actual project data (comments, before/after responses)

#### 🌐 **Dual Version Architecture (Ver.1 & Ver.2)**

**Ver.1 - Customizable Version (localhost:5001)**
```bash
# Standard version with full customization options
cd /home/grace/projects/social-implement/lecture-survey-analysis/lecture-text-analysis
source venv/bin/activate
nohup python wordcloud_app/app.py > logs/wordcloud_app.log 2>&1 &
```

**Ver.2 - Word Exclusion Test Version (localhost:5002)**
```bash
# Fixed parameter version for consistent word exclusion testing
cd /home/grace/projects/social-implement/lecture-survey-analysis/lecture-text-analysis
source venv/bin/activate
nohup python wordcloud_app/app_v2.py > logs/wordcloud_app_v2.log 2>&1 &
```

#### ⚠️ **Server Management**
| Version | Port | Process Pattern | Log File |
|---------|------|----------------|----------|
| **Ver.1** | 5001 | `python.*app.py` | `logs/wordcloud_app.log` |
| **Ver.2** | 5002 | `python.*app_v2.py` | `logs/wordcloud_app_v2.log` |

**Process Management**:
```bash
# Check all wordcloud processes
ps aux | grep "app.py\|app_v2.py" | grep -v grep

# Kill specific version
pkill -f "python.*app.py"     # Ver.1
pkill -f "python.*app_v2.py"  # Ver.2

# Health check
curl -s http://localhost:5001 >/dev/null && echo "Ver.1 OK" || echo "Ver.1 Down"
curl -s http://localhost:5002 >/dev/null && echo "Ver.2 OK" || echo "Ver.2 Down"
```

#### 🎨 **Ver.1 Features (localhost:5001) - Customizable Version**
- **Custom Color Palettes**: 5 Orange+Blue themed colormaps + 3-color custom system
  - `orange_blue`: Orange to blue gradient
  - `blue_orange`: Blue to orange gradient  
  - `orange_white_blue`: Balanced orange-white-blue
  - `tokyo_kosen_warm`: Warm orange tones
  - `tokyo_kosen_cool`: Cool blue tones
  - **3-Color Custom**: User-defined orange/gray/blue combinations with ListedColormap
- **Background Control**: Brightness slider (90-100% light range) with live preview
- **Flexible Parameters**: All visual parameters user-adjustable
- **Production Presets**: Tokyo Kosen-specific configuration presets

#### 🔍 **Ver.2 Features (localhost:5002) - Word Exclusion Test Version**
- **Fixed Visual Parameters**: Consistent results for comparison testing
  - Min/Max Font: 24px - 174px
  - Horizontal Preference: 90%
  - Relative Scaling: 0.4
  - Max Words: 140
  - Background: #f8f8f8
- **WCAG 2.1 Level AA Colors**: Accessibility-compliant color scheme
  - Orange: #d06500, Blue: #0066cc, Brown: #331a00
- **Advanced Word Exclusion**:
  - **Category-based**: General/Thanks/School/Experiment word groups
  - **Custom exclusion**: Comma-separated user-defined words
  - **Real-time filtering**: Immediate tokenization with exclusions applied
- **Accessibility Features**:
  - Screen reader support with live announcements
  - Keyboard navigation optimization
  - High contrast support
  - Skip links and ARIA labels

#### 📊 **Common Features (Both Versions)**
- **Improved Japanese NLP**: Janome tokenizer with proper word segmentation
- **Real Data Sources**: 4 data source options (all responses, comments only, before/after)

#### 📊 **Data Source Options**
1. **All Responses (統合)**: Complete dataset analysis
2. **Comments Only (感想文のみ)**: Student reflection focus
3. **Q2 Before (授業前)**: Pre-lesson understanding
4. **Q2 After (授業後)**: Post-lesson understanding

### Japanese Font Infrastructure
- **Font Downloader**: `scripts/setup/download_japanese_fonts.py` - Automated font installation
- **Available Fonts** (7 total):
  - IPAex Gothic/Mincho, IPA Gothic/Mincho
  - はんなり明朝 (Hannari Mincho) - Successfully added from official source
  - Noto Sans JP, Noto Serif JP
- **Font Directory**: `fonts/` with automatic loading in web app
- **Note**: こはるいろサンレイ unavailable (distribution site closed)

### Documentation Updates
- **Wordcloud Algorithm**: Detailed explanation at `docs/wordcloud_algorithm_explanation.md`
- **Implementation Workflow**: Comprehensive 4-week plan with 67 tasks
- **Test Scripts**: E2E testing (`wordcloud_app/test_e2e.py`) and font verification

### Technical Improvements
- **Virtual Environment**: Created to handle externally-managed Python environment
- **Error Handling**: Robust handling for statistical tests with zero-variance data
- **Font Path Resolution**: Automatic project-relative path handling
- **Sample vs Actual Data**: Clear separation for demo and production usage
- **Japanese Morphological Analysis**: Enhanced word segmentation with Janome
- **Custom Colormap System**: Dynamic colormap generation for brand consistency

## Version Management & Deployment Strategy (2025-06-01)

### Dual Application Architecture
The project now maintains two parallel web applications for different use cases:

| Aspect | Ver.1 (Port 5001) | Ver.2 (Port 5002) |
|--------|-------------------|-------------------|
| **Purpose** | Full customization & exploration | Consistent testing & accessibility |
| **Target Users** | Researchers, designers | Educators, accessibility users |
| **Visual Parameters** | User-adjustable | Fixed for consistency |
| **Color System** | Custom 3-color + presets | WCAG 2.1 AA compliant |
| **Key Feature** | Real-time customization | Advanced word exclusion |
| **Accessibility** | Standard | Enhanced (WCAG 2.1 Level AA) |

### Development Context Updates

#### New File Structure
```
wordcloud_app/
├── app.py              # Ver.1 - Customizable version
├── app_v2.py           # Ver.2 - Word exclusion test version
├── templates/
│   ├── index.html      # Ver.1 template
│   └── index_v2.html   # Ver.2 template (accessibility-focused)
├── static/
│   ├── css/
│   │   ├── style.css   # Ver.1 styles
│   │   └── style_v2.css # Ver.2 styles (WCAG compliant)
│   └── js/
│       ├── app.js      # Ver.1 JavaScript
│       └── app_v2.js   # Ver.2 JavaScript (accessibility enhanced)
└── logs/               # Separate log files for each version
```

#### Research Applications
1. **Visual Parameter Studies**: Ver.1 for testing different visual configurations
2. **Word Exclusion Research**: Ver.2 for systematic stop-word effectiveness studies
3. **Accessibility Compliance**: Ver.2 demonstrates WCAG 2.1 Level AA implementation
4. **Comparative Analysis**: Both versions can analyze the same data with different approaches

#### Production Considerations
- **Concurrent Operation**: Both versions can run simultaneously on different ports
- **Data Consistency**: Both use the same processed dataset (`data/processed/all_text_corpus.csv`)
- **Configuration Export**: Ver.2 includes version metadata in exported configurations
- **Log Separation**: Independent logging for debugging and monitoring