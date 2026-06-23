# Check Your PDs

_Check Your PDs_ is a two-stage deep learning system for **Parkinson's Disease (PD) pre-detection screening**, developed as an academic research project at the Sirindhorn International Institute of Technology (SIIT), Thammasat University. It combines clinical record analysis (NLP) with hand-drawing image classification to flag individuals who may be at risk of PD and should seek further medical evaluation.

> **Disclaimer:** This is a *preliminary screening tool* targeting the prodromal phase, not a diagnostic system. It does not diagnose Parkinson's Disease. Results should be confirmed by a qualified medical professional.

## Overview

The system produces a combined risk score from two independent stages:

- **Stage 1 — Clinical NLP Scoring:** Regex-based feature extraction over mixed Thai-English clinical records, with per-symptom weighting tied to clinical relevance (cardinal motor symptoms weighted higher than non-specific ones).
- **Stage 2 — Hand-Drawing CNN Classification:** A MobileNetV2 transfer-learning model classifies spiral and wave drawings as healthy or PD-indicative, with Grad-CAM heatmaps for interpretability.

The final score fuses both stages (0.35·S₁ + 0.65·S₂), prioritizing the sensitivity/recall tradeoffs that matter in a clinical screening context.

## Features

- **Clinical Record Analysis:** NLP extraction of motor, non-motor, and functional-status indicators from clinical text.
- **Hand-Drawing Classification:** MobileNetV2-based classification of spiral and wave drawings.
- **Explainable Predictions:** Grad-CAM heatmaps highlight the drawing regions driving each prediction.
- **Combined Risk Score:** Weighted fusion of clinical and image-based scores.
- **Web Interface:** Deployed Gradio app for interactive screening.

## Technology Stack

- **ML Framework:** TensorFlow / Keras (MobileNetV2), trained on Google Colab (T4 GPU)
- **NLP:** Regex-based extraction, PyThaiNLP for mixed Thai-English text
- **Visualization:** Grad-CAM (pure PIL/numpy implementation)
- **Interface:** Gradio
- **Deployment:** Hugging Face Spaces

## Live Demo

The screening app is deployed on Hugging Face Spaces:
`https://huggingface.co/spaces/maggisai/parkinsons-detection-using-mobilenetv2`

## Datasets

- **Stage 1:** Clinical records from Udon Thani Hospital (mixed Thai-English).
- **Stage 2:** Kaggle Parkinson's drawings dataset (spiral and wave).

> **Note:** The two datasets have no patient overlap, so the combined score is *simulated* rather than prospectively validated. This is a core limitation of the current work.

## Results

| Drawing Type | Accuracy | AUC  |
|--------------|----------|------|
| Wave         | 85%      | ~0.94 |
| Spiral       | 79%      | ~0.87 |

Wave drawings outperform spiral, as they more consistently expose sustained fine motor control deficits.

## Future Work

- Brain MRI analysis for structural changes in the substantia nigra.
- Multimodal learning combining drawings with voice and keystroke data.
- Prospective validation on a single cohort with overlapping clinical and drawing data.

## Authors

- Sai Wai Yan Phyo (6722790282)
- Kantapon Makpisut (6622781241)
- Advisor: Dr. Sasiporn Usanavasin
- Prof. Thanaruk Theeramunkong

_Sirindhorn International Institute of Technology (SIIT), Thammasat University_

## License

Released under the MIT License.

## Acknowledgements

Developed as an undergraduate research project at SIIT. Thanks to Dr. Sasiporn Usanavasin and all mentors and peers who supported this work.
