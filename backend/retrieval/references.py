import re


def extract_circular_reference(question: str):
    """Reconnaît une circulaire ou une note, en français ou en arabe."""
    normalized = question.translate(
        str.maketrans(
            "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹",
            "01234567890123456789",
        )
    )

    match = re.search(
        r"(?P<kind>\bcirculaire\b|\bnote\b|"
        r"المنشور|منشور|المذكرة|مذكرة)"
        r"\s*(?:n[°ºo.]?|رقم|عدد)?\s*"
        r"(?P<year>(?:19|20)\d{2})"
        r"\s*[-–—‑/]\s*(?P<number>\d+)\b",
        normalized,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    kind = match.group("kind").lower()
    prefix = "Note" if kind in {"note", "المذكرة", "مذكرة"} else "Cir"

    return (
        prefix,
        int(match.group("year")),
        int(match.group("number")),
    )


def matches_circular(filename: str, reference) -> bool:
    """Vérifie le type, l'année et le numéro du document."""
    match = re.match(
        r"(Cir|Note)_(\d{4})_(\d+)(?:_|\.|$)",
        filename,
        flags=re.IGNORECASE,
    )

    if not match:
        return False

    prefix, year, number = reference

    return (
        match.group(1).lower() == prefix.lower()
        and int(match.group(2)) == year
        and int(match.group(3)) == number
    )
