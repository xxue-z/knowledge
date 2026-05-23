from typing import Any, Callable, Optional, Dict, List, Type
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession


class AgentCapability(BaseModel):
    """Agent 能力描述"""
    agent_id: str = Field(..., description="Agent 唯一标识")
    name: str = Field(..., description="Agent 名称")
    description: str = Field(..., description="Agent 功能描述")
    input_schema: Dict[str, Any] = Field(..., description="输入参数 JSON Schema")
    output_schema: Dict[str, Any] = Field(..., description="输出参数 JSON Schema")
    supported_intents: List[str] = Field(..., description="支持的意图列表")
    version: str = Field("1.0", description="Agent 版本")
    priority: int = Field(100, description="优先级，数值越小优先级越高")


class MCPRequest(BaseModel):
    """MCP 请求"""
    action: str = Field(..., description="操作类型")
    params: Dict[str, Any] = Field(..., description="请求参数")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")
    trace_id: Optional[str] = Field(None, description="链路追踪 ID")
    span_id: Optional[str] = Field(None, description="Span ID")
    db_session: Optional[Any] = Field(None, description="数据库会话")
    user_context: Optional[Any] = Field(None, description="用户上下文")


class MCPResponse(BaseModel):
    """MCP 响应"""
    success: bool = Field(..., description="请求是否成功")
    data: Optional[Any] = Field(None, description="返回数据")
    error: Optional[str] = Field(None, description="错误信息")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="数据来源")
    confidence: float = Field(0.0, description="结果置信度")
    trace_id: Optional[str] = Field(None, description="链路追踪 ID")
    span_id: Optional[str] = Field(None, description="Span ID")


class MCPClient:
    """MCP 客户端接口"""
    
    async def call(self, agent_id: str, request: MCPRequest) -> MCPResponse:
        """调用指定 Agent"""
        raise NotImplementedError
    
    async def discover(self) -> List[AgentCapability]:
        """发现所有可用 Agent"""
        raise NotImplementedError
