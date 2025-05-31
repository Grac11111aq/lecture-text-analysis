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