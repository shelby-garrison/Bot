from __future__ import annotations

from typing import Optional

DISEASE_TREATMENTS = {
    "diabetes": (
        "Diabetes care: take prescribed anti-diabetic medicines regularly, monitor blood sugar, "
        "follow low-sugar/high-fiber diet, walk daily, and do periodic HbA1c tests."
    ),
    "hypertension": (
        "High blood pressure care: take BP medicines on schedule, reduce salt, monitor BP at home, "
        "exercise regularly, and limit stress and smoking."
    ),
    "asthma": (
        "Asthma care: use controller inhaler regularly, keep rescue inhaler available, avoid smoke/dust triggers, "
        "and follow doctor-approved inhaler technique."
    ),
    "arthritis": (
        "Arthritis care: pain-relief medicines as prescribed, light joint exercises/physiotherapy, weight control, "
        "and hot/cold compresses for stiffness and pain."
    ),
    "heart disease": (
        "Heart disease care: continue cardiac medicines exactly as prescribed, reduce salt/oily food, "
        "maintain daily walking if allowed, and attend routine cardiac follow-ups."
    ),
    "knee pain": (
        "Knee pain care: use doctor-advised pain relief, reduce stair strain, do gentle quadriceps exercises, "
        "maintain healthy weight, and consider physiotherapy for persistent pain."
    ),
    "thyroid": (
        "Thyroid care: take thyroid medicine at fixed morning timing on empty stomach, check TSH regularly, "
        "and avoid changing dosage without doctor advice."
    ),
    "copd": (
        "COPD care: use inhalers correctly and regularly, stop smoking, avoid dust/smoke exposure, "
        "do breathing exercises, and seek urgent care for worsening breathlessness."
    ),
    "ckd": (
        "CKD care: follow kidney-friendly diet (salt/protein control as advised), monitor BP and sugars, "
        "take nephrologist-prescribed medicines, and do periodic kidney function tests."
    ),
    "gerd": (
        "GERD care: avoid spicy/fried foods, eat smaller meals, avoid lying down for 2-3 hours after meals, "
        "and use acid-control medicines as prescribed."
    ),
    "migraine": (
        "Migraine care: identify and avoid triggers, maintain regular sleep/hydration, "
        "use acute migraine medicine early in attack, and discuss preventive therapy if frequent."
    ),
    "anemia": (
        "Anemia care: take iron/B12/folate supplements as prescribed, include iron-rich foods, "
        "and repeat blood tests to track hemoglobin improvement."
    ),
    "osteoporosis": (
        "Osteoporosis care: take calcium/vitamin D and bone medicines as prescribed, perform weight-bearing exercises, "
        "and prevent falls with safe footwear and home safety."
    ),
    "urinary tract infection": (
        "UTI care: complete full antibiotic course if prescribed, drink enough water, "
        "and seek care quickly for fever, flank pain, or recurrent symptoms."
    ),
    "depression": (
        "Depression care: continue prescribed mental health treatment, maintain sleep and routine activity, "
        "stay socially connected, and seek urgent help for any self-harm thoughts."
    ),
}

TREATMENT_QUERY_HINTS = ("treatment", "cure", "medicine for", "how to treat", "management")
DISEASE_ALIASES = {
    "knee pain": ("knee pain", "knee ache", "joint pain"),
    "thyroid": ("thyroid", "hypothyroid", "hyperthyroid", "thyroid problem"),
    "copd": ("copd", "chronic obstructive pulmonary disease"),
    "ckd": ("ckd", "chronic kidney disease", "kidney disease"),
    "gerd": ("gerd", "acidity", "acid reflux", "heartburn"),
    "migraine": ("migraine", "severe headache"),
    "urinary tract infection": ("uti", "urinary tract infection", "urine infection"),
}


RULES = [
    (
        ("diet", "food", "eat"),
        "Try low-salt, low-sugar meals with enough water. Include fruits, vegetables, and regular meal timing.",
    ),
    (
        ("exercise", "walk", "activity"),
        "Aim for light daily activity like a 20-30 minute walk if your doctor allows it.",
    ),
    (
        ("bp", "blood pressure"),
        "Take BP medicine on time, reduce salt intake, and check BP regularly.",
    ),
    (
        ("sugar", "diabetes", "glucose"),
        "Monitor sugar levels regularly and avoid high-sugar foods. Take medicines at fixed times.",
    ),
    (
        ("sleep", "insomnia", "rest"),
        "Maintain a fixed sleep schedule and avoid caffeine late evening.",
    ),
]


def rule_based_reply(text: str) -> Optional[str]:
    normalized = text.lower().strip()
    if not normalized:
        return None

    # Disease-treatment Q&A for direct health questions.
    if any(hint in normalized for hint in TREATMENT_QUERY_HINTS):
        for disease, response in DISEASE_TREATMENTS.items():
            aliases = DISEASE_ALIASES.get(disease, (disease,))
            if any(alias in normalized for alias in aliases):
                return response

    # Also answer when disease is mentioned without explicit "treatment" keyword.
    for disease, response in DISEASE_TREATMENTS.items():
        aliases = DISEASE_ALIASES.get(disease, (disease,))
        if any(alias in normalized for alias in aliases):
            return response

    for keywords, response in RULES:
        if any(keyword in normalized for keyword in keywords):
            return response

    if normalized in {"help", "menu"}:
        return (
            "Commands: hi, 1 (taken), 2 (not taken), stats (admin), "
            "or ask a health question like diet/exercise/sleep."
        )

    return None


def is_unwell_response(text: str) -> bool:
    normalized = text.lower().strip()
    bad_signals = ["not well", "bad", "pain", "dizzy", "fever", "unwell", "weak", "sick"]
    return any(token in normalized for token in bad_signals)

