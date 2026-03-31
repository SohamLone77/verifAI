from types import SimpleNamespace

from click.testing import CliRunner

import verifai_sdk.cli as cli


class DummyClient:
    def __init__(self, config=None, **kwargs):
        pass

    def review(self, *args, **kwargs):
        return SimpleNamespace(
            score=0.5,
            flags=[],
            rubric_scores={},
            cost=0.01,
            latency_ms=12.0,
            model_used="gpt-4",
        )

    def close(self):
        return None


def test_cli_review_json(monkeypatch):
    monkeypatch.setattr(cli, "VerifAIClient", DummyClient)

    runner = CliRunner()
    result = runner.invoke(cli.cli, ["review", "hello", "--json"])

    assert result.exit_code == 0
    assert "\"score\"" in result.output
