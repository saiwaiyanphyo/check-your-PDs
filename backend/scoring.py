"""Clinical risk scoring logic — extracted from original app.py."""


def compute_risk_score(
    age, sex,
    tremor, bradykinesia, rigidity,
    falls, gait_difficulty, weakness, asymmetric,
    cognitive_decline, sleep_disorder, constipation, depression,
    bedridden, walk_with_aid,
    has_cva, has_all_metabolic,
):
    score = 0
    breakdown = []

    if age and age != "Under 40":
        age_map = {"40-49": 0, "50-59": 0, "60-69": 1, "70-79": 2, "80+": 2}
        pts = age_map.get(age, 0)
        if pts > 0:
            score += pts
            breakdown.append(f"Age {age}: +{pts}")

    if sex == "Male":
        score += 1
        breakdown.append("Male sex: +1")

    if tremor:
        score += 2
        breakdown.append("Tremor: +2")
    if bradykinesia:
        score += 2
        breakdown.append("Bradykinesia: +2")
    if rigidity:
        score += 2
        breakdown.append("Rigidity: +2")

    if falls:
        score += 1
        breakdown.append("Falls/balance: +1")
    if gait_difficulty:
        score += 1
        breakdown.append("Gait difficulty: +1")
    if weakness:
        score += 1
        breakdown.append("Weakness: +1")
    if asymmetric:
        score += 1
        breakdown.append("Asymmetric symptoms: +1")

    if cognitive_decline:
        score += 1
        breakdown.append("Cognitive decline: +1")
    if sleep_disorder:
        score += 1
        breakdown.append("Sleep disorder: +1")
    if constipation:
        score += 1
        breakdown.append("Constipation: +1")
    if depression:
        score += 1
        breakdown.append("Depression: +1")

    if bedridden:
        score += 1
        breakdown.append("Bedridden: +1")
    if walk_with_aid:
        score += 1
        breakdown.append("Walking aid: +1")

    if has_cva:
        score += 1
        breakdown.append("Stroke history: +1")
    if has_all_metabolic:
        score += 1
        breakdown.append("Metabolic cluster: +1")

    return score, breakdown


def get_risk_level(score):
    if score <= 2:
        return "Low", 0.3, "🟢"
    elif score <= 5:
        return "Medium", 1.0, "🟡"
    else:
        return "High", 1.5, "🔴"


def combined_prediction(risk_score, cnn_confidence, max_score=22):
    norm_risk = risk_score / max_score
    _, risk_weight, _ = get_risk_level(risk_score)
    weighted_risk = min(norm_risk * risk_weight, 1.0)

    combined = weighted_risk * 0.35 + cnn_confidence * 0.65

    if combined >= 0.70:
        rec = "HIGH PROBABILITY"
        advice = "Strongly recommend consultation with a neurologist for comprehensive evaluation."
    elif combined >= 0.45:
        rec = "MODERATE PROBABILITY"
        advice = "Recommend scheduling a medical evaluation. Early detection enables better management."
    elif combined >= 0.25:
        rec = "LOW-MODERATE"
        advice = "Consider monitoring symptoms. Consult a doctor if symptoms worsen or new ones appear."
    else:
        rec = "LOW PROBABILITY"
        advice = "Low risk based on current assessment. Continue monitoring general health."

    return combined, rec, advice
