from app.agents.orchestrator import OrchestratorAgent
from app.models.schemas import UserContext


class QAService:
    def __init__(self):
        pass

    async def ask_question(self, user: UserContext, question: str, db_session=None) -> dict:
        agent = OrchestratorAgent(db_session, user)
        result = await agent.process_query(question)
        return result