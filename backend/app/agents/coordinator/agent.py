import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import UserContext
from app.mcps import MCPRequest, MCPResponse, create_mcp_client, get_registry
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class CoordinatorAgent:
    """协调 Agent - 通过 MCP 协议协调所有 Agent 工作"""
    
    def __init__(self, db: AsyncSession, user: UserContext):
        self.db = db
        self.user = user
        self.mcp_client = create_mcp_client(db, user)
        self.llm = LLMService()
        self.registry = get_registry()
    
    async def dispatch(self, intent: str, params: dict, context: dict = None) -> MCPResponse:
        """根据意图分发任务到合适的 Agent"""
        candidates = self.registry.find_by_intent(intent)
        
        if not candidates:
            logger.warning(f"No agent found for intent: {intent}")
            return MCPResponse(
                success=False,
                error=f"未找到处理该意图的 Agent: {intent}",
                confidence=0.0
            )
        
        agent_info = candidates[0]
        agent_id = agent_info["capability"].agent_id
        
        logger.info(f"Dispatching to agent: {agent_id} for intent: {intent}")
        
        request = MCPRequest(
            action=self._intent_to_action(intent, params),
            params=params,
            context=context
        )
        
        response = await self.mcp_client.call(agent_id, request)
        
        if not response.success and len(candidates) > 1:
            for agent_info in candidates[1:]:
                agent_id = agent_info["capability"].agent_id
                response = await self.mcp_client.call(agent_id, request)
                if response.success:
                    break
        
        return response
    
    def _intent_to_action(self, intent: str, params: dict) -> str:
        """将意图转换为具体操作"""
        if intent == "PURE_DB":
            if params.get("employee_name"):
                return "get_employee_by_name"
            elif params.get("employee_id"):
                return "get_employee_by_id"
            elif params.get("department"):
                return "get_employees_by_department"
            return "get_employee_by_name"
        
        elif intent == "PURE_KB":
            if params.get("query"):
                return "search"
            return "search"
        
        elif intent == "HYBRID":
            return "search"
        
        return "search"
    
    async def handle_db_query(self, question: str, intent_result: dict) -> dict:
        """处理纯数据库查询（兼容旧接口）"""
        entities = intent_result.get("entities", {})
        params = {}
        
        if entities.get("employee_names"):
            params["action"] = "get_employee_by_name"
            params["employee_name"] = entities["employee_names"][0]
        
        elif entities.get("departments"):
            params["action"] = "count_by_department"
            params["department"] = entities["departments"][0]
        
        elif intent_result.get("keywords"):
            params["action"] = "get_employee_by_name"
            params["employee_name"] = question
        
        response = await self.dispatch("PURE_DB", params)
        
        if response.success and response.data:
            answer = await self._generate_db_answer(question, response.data)
            return {
                "answer": answer,
                "sources": response.sources,
                "confidence": response.confidence
            }
        
        return {
            "answer": "未找到相关的员工信息。",
            "sources": [],
            "confidence": 0.0
        }
    
    async def handle_kb_query(self, question: str, intent_result: dict) -> dict:
        """处理纯知识库查询（兼容旧接口）"""
        params = {
            "action": "search",
            "query": question,
            "top_k": 5
        }
        
        response = await self.dispatch("PURE_KB", params)
        
        if response.success and response.data:
            results = response.data.get("items", []) + response.data.get("results", [])
            if results:
                answer = await self._generate_kb_answer(question, results)
                return {
                    "answer": answer,
                    "sources": response.sources,
                    "confidence": response.confidence
                }
        
        return {
            "answer": "知识库查询功能正在开发中。",
            "sources": [],
            "confidence": 0.5
        }
    
    async def handle_hybrid_query(self, question: str, intent_result: dict) -> dict:
        """处理混合查询（数据库 + 知识库）"""
        db_response = await self.handle_db_query(question, intent_result)
        kb_response = await self.handle_kb_query(question, intent_result)
        
        combined_answer = self._combine_answers(db_response["answer"], kb_response["answer"])
        combined_sources = db_response["sources"] + kb_response["sources"]
        combined_confidence = (db_response["confidence"] + kb_response["confidence"]) / 2
        
        return {
            "answer": combined_answer,
            "sources": combined_sources,
            "confidence": combined_confidence
        }
    
    async def _generate_db_answer(self, question: str, employee_data: dict) -> str:
        """根据数据库数据生成回答"""
        name = employee_data.get("name", "该员工")
        
        if "部门" in question:
            return f"{name}的部门是{employee_data.get('department', '未填写')}。"
        elif "上级" in question or "领导" in question:
            if employee_data.get("manager_id"):
                manager = await self.mcp_client.call(
                    "db_agent",
                    MCPRequest(action="get_employee_by_id", params={"employee_id": employee_data["manager_id"]})
                )
                if manager.success and manager.data:
                    return f"{name}的上级是{manager.data.get('name', '未知')}。"
            return f"{name}没有上级信息。"
        elif "工号" in question:
            return f"{name}的工号是{employee_data.get('employee_id', '未填写')}。"
        elif "入职" in question:
            return f"{name}的入职日期是{employee_data.get('hire_date', '未填写')}。"
        elif "职级" in question or "级别" in question:
            return f"{name}的职级是{employee_data.get('level', '未填写')}。"
        else:
            return (
                f"员工信息：\n"
                f"- 姓名：{employee_data.get('name', '未填写')}\n"
                f"- 工号：{employee_data.get('employee_id', '未填写')}\n"
                f"- 部门：{employee_data.get('department', '未填写')}\n"
                f"- 职级：{employee_data.get('level', '未填写')}\n"
                f"- 状态：{employee_data.get('status', '未填写')}"
            )
    
    async def _generate_kb_answer(self, question: str, results: list) -> str:
        """根据知识库结果生成回答"""
        if not results:
            return "未找到相关文档。"
        
        summaries = []
        for i, result in enumerate(results[:2]):
            title = result.get("title", "") or result.get("content", "")[:30]
            content = result.get("content", "")[:100]
            summaries.append(f"{i+1}. {title}\n   {content}")
        
        return "\n\n".join(summaries)
    
    def _combine_answers(self, db_answer: str, kb_answer: str) -> str:
        """合并两个回答"""
        if "未找到" in db_answer:
            return kb_answer
        if "正在开发" in kb_answer or "未找到" in kb_answer:
            return db_answer
        return f"{db_answer}\n\n相关文档：\n{kb_answer}"
    
    async def list_agents(self) -> list:
        """获取所有已注册的 Agent"""
        capabilities = await self.mcp_client.discover()
        return [{
            "agent_id": cap.agent_id,
            "name": cap.name,
            "description": cap.description,
            "supported_intents": cap.supported_intents,
            "version": cap.version
        } for cap in capabilities]
