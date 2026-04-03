from presidio_analyzer import PatternRecognizer, Pattern

def build_custom_recognizers():
    recognizers = []

    url_pattern = Pattern(
        name="url_pattern",
        regex=r"https?://[^\s\]\)]+",
        score=0.8,
    )
    recognizers.append(
        PatternRecognizer(
            supported_entity="URL",
            patterns=[url_pattern],
        )
    )

    account_pattern = Pattern(
        name="account_pattern",
        regex=r"\.\.\.\d{4}",
        score=0.9,
    )
    recognizers.append(
        PatternRecognizer(
            supported_entity="ACCOUNT_NUMBER",
            patterns=[account_pattern],
        )
    )

    address_pattern = Pattern(
        name="address_pattern",
        regex=r"\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Ave|St|Rd|Blvd|Lane|Way)",
        score=0.8,
    )
    recognizers.append(
        PatternRecognizer(
            supported_entity="ADDRESS",
            patterns=[address_pattern],
        )
    )

    return recognizers