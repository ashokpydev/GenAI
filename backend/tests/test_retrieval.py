from app.services.document_ingestion import lexical_score, split_text


def test_lexical_score_rewards_matching_terms():
    assert lexical_score("source citations", "answers include source citations") > lexical_score("unrelated", "answers include source citations")


def test_split_text_handles_large_text():
    chunks = split_text("alpha " * 500)
    assert len(chunks) > 1
