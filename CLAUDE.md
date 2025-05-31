# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a text mining project focused on analyzing elementary school student responses from a science outreach program conducted by Tokyo Tech. The project analyzes 200 text records including student comments and reasoning explanations about salt dissolution experiments.

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

## Development Environment

### Dependencies Installation
```bash
pip install -r requirements.txt
```

### Key Libraries
- **Japanese NLP**: janome (morphological analysis), spacy + ginza
- **Visualization**: matplotlib, seaborn, wordcloud  
- **ML/Topic Modeling**: scikit-learn, gensim
- **Sentiment Analysis**: textblob

### System Requirements
MeCab may need separate installation:
- Ubuntu: `sudo apt-get install mecab mecab-ipadic-utf8`
- macOS: `brew install mecab mecab-ipadic`

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

### Target Outputs
- `outputs/wordclouds/` - Visual frequency analysis
- `outputs/sentiment_results/` - Emotional response analysis  
- `outputs/topic_models/` - Thematic content extraction

## Analysis Standards

### Statistical Criteria
- Significance threshold: p < 0.05
- Minimum meaningful effect: Cohen's d > 0.2
- High interest threshold: Mean > 3.5 on 4-point scale

### Text Analysis Approach
- Focus on scientific vocabulary acquisition
- Track conceptual explanation improvements  
- Identify effective teaching elements from student feedback
- Analyze class-level differences (4 classes total)

### Stakeholder Reporting
Four distinct audiences requiring different emphasis:
1. **Project team** - Comprehensive technical results
2. **Faculty** - Academic rigor and theoretical connections
3. **Elementary teachers** - Practical classroom insights
4. **Institution** - Social impact demonstration

## Important Notes

- All analysis must maintain student privacy (no individual identification)
- Results should avoid overgeneralization beyond the specific experimental context
- Focus on practical educational insights rather than theoretical model building
- Statistical results must include effect sizes, not just p-values