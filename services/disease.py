def get_disease_advice(crop, symptoms):
    if not symptoms.strip():
        return "No symptoms provided. Regular inspection is recommended."

    return (
        f"For {crop}, the reported symptoms ({symptoms}) may indicate a stress issue or disease. "
        f"Inspect leaves, roots, and soil moisture immediately and consider contacting a local agronomist."
    )
