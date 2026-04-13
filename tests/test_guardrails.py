import pytest
from rag_service.guardrails import TopicDenylist
import tempfile
import os


@pytest.fixture
def denylist(tmp_path):
    f = tmp_path / "denylist.txt"
    f.write_text("hack\nexploit\njailbreak\n# this is a comment\npassword dump\n")
    return TopicDenylist(f)


class TestTopicDenylist:
    def test_clean_query_is_allowed(self, denylist):
        result = denylist.check_query("What is retrieval-augmented generation?")
        assert result.allowed is True
        assert result.rule_triggered is None

    def test_denied_topic_is_blocked(self, denylist):
        result = denylist.check_query("How do I hack into a system?")
        assert result.allowed is False
        assert result.rule_triggered == "topic_denylist"
        assert "hack" in result.reason

    def test_case_insensitive_matching(self, denylist):
        result = denylist.check_query("EXPLOIT this vulnerability")
        assert result.allowed is False

    def test_substring_match(self, denylist):
        result = denylist.check_query("I want to jailbreak my phone")
        assert result.allowed is False

    def test_multi_word_term(self, denylist):
        result = denylist.check_query("Find a password dump online")
        assert result.allowed is False

    def test_comment_lines_ignored(self, denylist):
        # "# this is a comment" should not be a denylist term
        result = denylist.check_query("this is a comment")
        assert result.allowed is True

    def test_fail_closed_on_missing_file(self):
        with pytest.raises(FileNotFoundError):
            TopicDenylist("/nonexistent/path/denylist.txt")

    def test_guardrail_is_active(self, denylist):
        assert denylist.active is True

    def test_term_count(self, denylist):
        assert denylist.term_count == 4  # hack, exploit, jailbreak, password dump (comment excluded)
