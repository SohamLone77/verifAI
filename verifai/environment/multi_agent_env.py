"""Environment integration for the multi-agent panel"""

from typing import Any, Dict, Optional

from verifai.agents.multi_agent_panel import MultiAgentPanel
from verifai.models.agent_models import ConsensusConfig, ReviewRequest, ReviewResponse


class MultiAgentEnv:
    """Wrap multi-agent panel for environment integration"""

    def __init__(self, consensus_config: Optional[ConsensusConfig] = None):
        self.panel = MultiAgentPanel(consensus_config)

    def review_content(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
        review_depth: str = "standard",
    ) -> ReviewResponse:
        request = ReviewRequest(
            content=content,
            context=context,
            review_depth=review_depth,
        )
        return self.panel.review(request)
