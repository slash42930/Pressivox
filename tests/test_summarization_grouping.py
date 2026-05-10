from app.services.summarization.grouping import top_meaning_groups


def test_top_meaning_groups_prefers_non_other_when_sufficient() -> None:
    groups = [
        {"meaning": "other", "top_score": 0.99},
        {"meaning": "planet", "top_score": 0.91},
        {"meaning": "mythology", "top_score": 0.89},
        {"meaning": "element", "top_score": 0.88},
    ]

    selected = top_meaning_groups(groups, limit=3, min_non_other_for_prefer=2)

    assert len(selected) == 3
    assert selected[0]["meaning"] == "planet"
    assert selected[1]["meaning"] == "mythology"
    assert selected[2]["meaning"] == "element"


def test_top_meaning_groups_keeps_sorted_groups_when_non_other_insufficient() -> None:
    groups = [
        {"meaning": "other", "top_score": 0.95},
        {"meaning": "general", "top_score": 0.8},
    ]

    selected = top_meaning_groups(groups, limit=2, min_non_other_for_prefer=2)

    assert [group["meaning"] for group in selected] == ["other", "general"]
