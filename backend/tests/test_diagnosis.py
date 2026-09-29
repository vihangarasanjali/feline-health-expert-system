from backend.app import diagnose


def test_uri():
    symptoms = [
        "sneezing",
        "nasal_discharge",
        "eye_discharge",
        "coughing",
        "fever",
        "lethargy"
    ]

    result = diagnose(symptoms)

    assert result["results"][0]["disease"] == "uri"

def test_diabetes_differentiator():
    symptoms = [
        "increased_thirst",
        "increased_urination",
        "weight_loss",
        "increased_appetite"
    ]

    result = diagnose(symptoms)

    assert result["results"][0]["disease"] == "diabetes"

def test_flutd_emergency():
    symptoms = [
        "straining_to_urinate",
        "blood_in_urine"
    ]

    result = diagnose(symptoms)

    assert result["urgency"] == "emergency"

def test_explanation_contains_triggered_rule():
    symptoms = [
        "head_shaking",
        "ear_discharge",
        "itching"
    ]

    result = diagnose(symptoms)

    assert "R6" in result["explanation"]

