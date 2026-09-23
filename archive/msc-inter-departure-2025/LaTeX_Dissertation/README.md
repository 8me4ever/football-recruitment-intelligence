# Multi-layer Probability Fusion Algorithm LaTeX Dissertation

## Overview

This folder contains the complete LaTeX dissertation for the Master of Science in Data Science degree at the University of Birmingham, titled:

**"Multi-layer Probability Fusion Algorithm Based on Relative Percentile Ranking with Weight Optimization: Application to Football Transfer Prediction"**

## File Structure

```
LaTeX_Dissertation/
├── main.tex                    # Main LaTeX document (compile this file)
├── introduction.tex            # Chapter 1: Introduction
├── analysis_requirements.tex   # Chapter 2: Analysis and Requirements Capture  
├── design.tex                  # Chapter 3: Design
├── data_collection.tex         # Chapter 4: Data Collection
├── implementation.tex          # Chapter 5: Implementation and Data Processing
├── results.tex                 # Chapter 6: Results
├── discussion_conclusion.tex   # Chapter 7: Discussion and Conclusion
└── README.md                   # This file
```

## Compilation Instructions

### Requirements
- LaTeX distribution (TeX Live, MiKTeX, or MacTeX)
- Required packages (automatically handled by most modern LaTeX distributions):
  - amsmath, amsfonts, amssymb
  - graphicx, float
  - hyperref, natbib
  - geometry, setspace
  - listings, xcolor
  - booktabs, longtable, array, multirow
  - algorithm, algpseudocode

### Compilation Steps

1. **Primary Compilation**:
   ```bash
   pdflatex main.tex
   ```

2. **For Bibliography** (if adding references):
   ```bash
   pdflatex main.tex
   bibtex main
   pdflatex main.tex
   pdflatex main.tex
   ```

3. **Alternative using latexmk** (recommended):
   ```bash
   latexmk -pdf main.tex
   ```

## Document Structure

### Chapter Overview

1. **Introduction** (5,500 words)
   - Research motivation and problem statement
   - Innovation contributions and objectives  
   - Research scope and dissertation structure

2. **Analysis and Requirements Capture** (6,200 words)
   - Literature review of sports analytics and transfer prediction
   - Problem analysis and Inter Milan case study context
   - Functional and non-functional requirements specification
   - Success criteria and validation framework

3. **Design** (5,800 words)
   - System architecture overview
   - Percentile-based feature engineering design
   - Multi-algorithm optimization framework design
   - Prediction generation and evaluation system design

4. **Data Collection** (5,000 words)  
   - Data sources and acquisition methodology
   - Data quality assessment and validation procedures
   - Ground truth transfer outcome compilation
   - Ethical considerations and data limitations

5. **Implementation and Data Processing** (6,500 words)
   - Development environment and technical infrastructure
   - Core algorithm implementation with code examples
   - Technical challenges and solutions
   - Multi-source data integration framework

6. **Results** (6,200 words)
   - Experimental setup and validation framework
   - Algorithm performance comparison and statistical analysis
   - Individual player predictions and ground truth validation
   - Sensitivity analysis and robustness testing

7. **Discussion and Conclusion** (5,800 words)
   - Research findings and theoretical contributions
   - Practical implications for football analytics
   - Research limitations and constraints
   - Future research directions and final reflection

### Key Features

- **Academic Rigor**: Comprehensive literature review, statistical validation, and methodological soundness
- **Technical Depth**: Detailed algorithm descriptions with mathematical formulations and code implementations  
- **Practical Relevance**: Real-world validation using Inter Milan transfer outcomes
- **Professional Presentation**: Full LaTeX formatting following UK university dissertation standards

## Research Contributions

The dissertation makes several significant contributions:

1. **Algorithmic Innovation**: Novel percentile-based feature engineering algorithm
2. **Optimization Framework**: Systematic comparison of multiple optimization algorithms  
3. **Empirical Achievement**: 92.0% prediction accuracy (35.3% improvement over baseline)
4. **Methodological Advancement**: Comprehensive framework for sports analytics research
5. **Practical Application**: Actionable insights for football transfer strategy

## Usage Notes

- The document is configured for A4 paper with UK university formatting standards
- All chapters are modular and can be compiled independently for review
- Code listings are properly formatted with syntax highlighting
- Tables and figures are professionally formatted for academic presentation
- Hyperlinks are configured for PDF navigation

## Contact Information

**Author**: Ziming Chen  
**Institution**: University of Birmingham, School of Computer Science  
**Program**: Master of Science in Data Science  
**Supervisor**: Todd  
**Year**: 2024

## License

This dissertation is submitted as academic work for degree requirements. All code implementations and methodological frameworks described may be adapted for academic research purposes with appropriate citation.

---

*This dissertation represents approximately 40,000 words of original research on algorithmic innovation in sports analytics, with comprehensive validation and practical application to football transfer prediction.*