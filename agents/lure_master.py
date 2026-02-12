"""
路亚钓鱼宗师 Agent
核心对话逻辑实现
"""
import json
import re
from typing import Optional, Dict, Any, List
from .base import BaseAgent, ConversationState
from llm import LLMFactory, BaseLLM, Message
from tools import ToolManager
from config.prompts import (
    SYSTEM_PROMPT,
    INFO_COLLECTION_PROMPT,
    FISHING_ADVICE_PROMPT,
    FOLLOW_UP_PROMPT,
)
from config.settings import get_settings


class LureMasterAgent(BaseAgent):
    """路亚钓鱼宗师 Agent"""
    
    name = "lure_master"
    description = "路亚钓鱼宗师 - 专业的路亚钓鱼指导助手"
    
    # 必填字段
    REQUIRED_FIELDS = ["time", "location"]
    
    # 可选字段
    OPTIONAL_FIELDS = ["target_fish", "equipment", "companions"]
    
    def __init__(self, llm: Optional[BaseLLM] = None):
        """
        初始化路亚宗师 Agent
        
        Args:
            llm: LLM 实例（可选，不传则自动选择）
        """
        super().__init__()
        
        settings = get_settings()
        self.llm = llm or LLMFactory.get_first_available()
        self.tools = ToolManager()
        self.mock_mode = settings.mock_mode
        
        # 初始化系统提示
        self.system_prompt = SYSTEM_PROMPT
    
    def chat(self, user_input: str) -> str:
        """
        与 Agent 对话
        
        Args:
            user_input: 用户输入
            
        Returns:
            Agent 回复
        """
        # 先记录用户消息，这样后续处理可以看到当前输入
        self.state.add_message("user", user_input)
        
        # 根据当前阶段处理
        if self.state.current_stage == "greeting":
            response = self._handle_greeting(user_input)
        elif self.state.current_stage == "collecting":
            response = self._handle_collecting(user_input)
        elif self.state.current_stage == "analyzing":
            response = self._handle_analyzing()
        elif self.state.current_stage == "advising":
            response = self._handle_advising(user_input)
        else:
            response = self._handle_general(user_input)
        
        # 记录助手回复
        self.state.add_message("assistant", response)
        
        return response
    
    def _handle_greeting(self, user_input: str) -> str:
        """处理问候阶段"""
        # 分析用户意图
        intent = self._analyze_intent(user_input)
        
        if intent == "fishing_plan":
            # 用户有钓鱼计划，开始收集信息
            self.state.current_stage = "collecting"
            return self._handle_collecting(user_input)
        else:
            # 一般问候或问题
            return self._chat_with_llm(user_input)
    
    def _handle_collecting(self, user_input: str) -> str:
        """处理信息收集阶段"""
        # 尝试从用户输入中提取信息
        extracted = self._extract_info(user_input)
        
        # 更新已收集的信息
        for key, value in extracted.items():
            if value and key not in ["missing_fields"]:
                self.state.update_info(key, value)
        
        # 检查必填信息是否完整
        missing = self._check_missing_fields()
        
        if not missing:
            # 信息完整，进入分析阶段
            self.state.current_stage = "analyzing"
            return self._handle_analyzing()
        else:
            # 继续收集信息
            return self._ask_follow_up(missing)
    
    def _handle_analyzing(self) -> str:
        """处理分析阶段"""
        collected = self.state.collected_info
        
        # 获取天气信息
        weather_info = self._get_weather_info(collected.get("location", ""))
        
        # 获取知识库信息
        knowledge_info = self._get_knowledge_info(collected)
        
        # 存储分析结果
        self.state.update_info("weather", weather_info)
        self.state.update_info("knowledge", knowledge_info)
        
        # 进入建议阶段
        self.state.current_stage = "advising"
        
        # 生成钓鱼建议
        return self._generate_advice()
    
    def _handle_advising(self, user_input: str) -> str:
        """处理建议阶段"""
        # 用户可能有追问或新的需求
        intent = self._analyze_intent(user_input)
        
        if intent == "fishing_plan":
            # 新的钓鱼计划，重置状态
            self.reset()
            self.state.current_stage = "collecting"
            return self._handle_collecting(user_input)
        else:
            # 继续对话，带上已收集的钓鱼计划上下文
            return self._chat_with_context(user_input)
    
    def _handle_general(self, user_input: str) -> str:
        """处理一般对话"""
        return self._chat_with_llm(user_input)
    
    def _analyze_intent(self, user_input: str) -> str:
        """分析用户意图"""
        # 简单的关键词匹配
        fishing_keywords = ["钓鱼", "钓", "去钓", "想钓", "打算钓", "明天", "后天", "周末", "早起"]
        
        for keyword in fishing_keywords:
            if keyword in user_input:
                return "fishing_plan"
        
        return "general"
    
    def _extract_info(self, user_input: str) -> Dict[str, Any]:
        """从用户输入中提取信息"""
        result = {
            "time": None,
            "location": None,
            "target_fish": None,
            "equipment": None,
            "companions": None,
        }
        
        # 时间提取
        time_patterns = [
            r"明天(早上|上午|下午|晚上|傍晚|清晨)?",
            r"后天(早上|上午|下午|晚上|傍晚|清晨)?",
            r"周末",
            r"下(周|星期)",
            r"(\d+)号",
            r"(早上|上午|下午|晚上|傍晚|清晨|早起)",
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, user_input)
            if match:
                result["time"] = match.group()
                break
        
        # 地点提取
        location_patterns = [
            r"去(.+?)钓",
            r"在(.+?)钓",
            r"到(.+?)钓",
            r"(.+?)有(鱼|鳜鱼|鲈鱼|翘嘴)",
            r"(太湖|阳澄湖|千岛湖|洞庭湖|水库|河|湖)",
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, user_input)
            if match:
                result["location"] = match.group(1) if match.lastindex else match.group()
                break
        
        # 目标鱼种提取
        fish_keywords = ["鳜鱼", "鲈鱼", "翘嘴", "黑鱼", "军鱼", "桂鱼", "白鱼"]
        for fish in fish_keywords:
            if fish in user_input:
                result["target_fish"] = fish
                break
        
        # 装备提取
        equipment_keywords = ["路亚竿", "渔轮", "鱼竿", "竿子", "MH", "M调", "L调"]
        for equip in equipment_keywords:
            if equip in user_input:
                result["equipment"] = equip
                break
        
        # 人数提取
        companions_match = re.search(r"(\d+)个?人", user_input)
        if companions_match:
            result["companions"] = int(companions_match.group(1))
        
        return result
    
    def _check_missing_fields(self) -> List[str]:
        """检查缺失的必填字段"""
        missing = []
        for field in self.REQUIRED_FIELDS:
            if not self.state.collected_info.get(field):
                missing.append(field)
        return missing
    
    def _ask_follow_up(self, missing_fields: List[str]) -> str:
        """生成追问"""
        collected = self.state.collected_info
        known_info = "\n".join([f"- {k}: {v}" for k, v in collected.items() if v])
        
        prompt = FOLLOW_UP_PROMPT.format(
            user_intent="钓鱼",
            known_info=known_info or "暂无",
            missing_fields="、".join(missing_fields)
        )
        
        # 构建增强的系统提示
        enhanced_system = self.system_prompt + f"\n\n## 当前任务\n{prompt}"
        
        # 构建消息列表
        messages = [Message(role="system", content=enhanced_system)]
        
        # 添加对话历史（已包含当前用户消息）
        history = self.state.get_history(limit=10)
        for msg in history:
            messages.append(Message(role=msg["role"], content=msg["content"]))
        
        return self.llm.chat(messages)
    
    def _get_weather_info(self, location: str) -> Dict[str, Any]:
        """获取天气信息"""
        if not location:
            return {}
        
        result = self.tools.run_tool("weather", location=location, days=3)
        
        if result.success:
            return result.data
        else:
            return {"error": result.error}
    
    def _get_knowledge_info(self, collected: Dict[str, Any]) -> Dict[str, Any]:
        """获取知识库信息"""
        knowledge = {}
        
        # 获取目标鱼种信息
        target_fish = collected.get("target_fish")
        if target_fish:
            fish_info = self.tools.get_tool("knowledge").get_fish_info(target_fish)
            if fish_info:
                knowledge["fish_info"] = fish_info
        
        # 获取钓点信息
        location = collected.get("location")
        if location:
            spot_info = self.tools.get_tool("knowledge").get_spot_info(location)
            if spot_info:
                knowledge["spot_info"] = spot_info
        
        return knowledge
    
    def _generate_advice(self) -> str:
        """生成钓鱼建议"""
        collected = self.state.collected_info
        
        # 格式化天气信息
        weather = collected.get("weather", {})
        weather_info = "暂无天气信息"
        if weather and "forecast" in weather:
            forecast_lines = []
            for f in weather["forecast"][:3]:
                forecast_lines.append(
                    f"- {f['date']}: {f['text_day']}, {f['temp_min']}-{f['temp_max']}°C, {f['wind_dir']} {f['wind_scale']}"
                )
            weather_info = "\n".join(forecast_lines)
            
            # 添加钓鱼适宜度
            if "fishing_suitability" in weather:
                suitability = weather["fishing_suitability"][0]
                weather_info += f"\n\n钓鱼适宜度: {suitability['level']} ({suitability['score']}分)"
        
        # 格式化知识库信息
        knowledge = collected.get("knowledge", {})
        knowledge_info = "暂无相关知识"
        if knowledge:
            lines = []
            if "fish_info" in knowledge:
                fish = knowledge["fish_info"]
                lines.append(f"目标鱼种: {fish['name']}")
                lines.append(f"习性: {fish['habits']}")
                lines.append(f"推荐饵: {', '.join(fish['lures'])}")
                lines.append(f"推荐钓法: {', '.join(fish['techniques'])}")
            if "spot_info" in knowledge:
                spot = knowledge["spot_info"]
                lines.append(f"钓点: {spot['name']}")
                lines.append(f"鱼种: {', '.join(spot['fish_types'])}")
                lines.append(f"建议: {spot['tips']}")
            knowledge_info = "\n".join(lines)
        
        # 生成建议
        prompt = FISHING_ADVICE_PROMPT.format(
            time=collected.get("time", "未指定"),
            location=collected.get("location", "未指定"),
            target_fish=collected.get("target_fish", "未指定"),
            equipment=collected.get("equipment", "未指定"),
            companions=collected.get("companions", "未指定"),
            weather_info=weather_info,
            knowledge_info=knowledge_info,
        )
        
        # 构建增强的系统提示
        enhanced_system = self.system_prompt + f"\n\n## 当前任务\n请根据用户提供的钓鱼计划生成专业建议。\n\n{prompt}"
        
        # 构建消息列表
        messages = [Message(role="system", content=enhanced_system)]
        
        # 添加对话历史（已包含当前用户消息）
        history = self.state.get_history(limit=10)
        for msg in history:
            messages.append(Message(role=msg["role"], content=msg["content"]))
        
        return self.llm.chat(messages)
    
    def _chat_with_llm(self, user_input: str) -> str:
        """与 LLM 进行普通对话"""
        # 构建消息列表
        messages = [Message(role="system", content=self.system_prompt)]
        
        # 添加对话历史（已包含当前用户消息）
        history = self.state.get_history(limit=10)
        for msg in history:
            messages.append(Message(role=msg["role"], content=msg["content"]))
        
        return self.llm.chat(messages)
    
    def _chat_with_context(self, user_input: str) -> str:
        """带上下文的对话，保留已收集的钓鱼计划信息"""
        # 构建增强的系统提示，包含已收集的信息
        collected = self.state.collected_info
        context_info = ""
        
        if collected:
            context_parts = ["\n\n## 当前钓鱼计划信息"]
            for key, value in collected.items():
                if value and key not in ["weather", "knowledge"]:
                    context_parts.append(f"- {key}: {value}")
            if len(context_parts) > 1:
                context_info = "\n".join(context_parts)
                context_info += "\n\n请在回答时参考以上钓鱼计划信息，保持对话连贯性。"
        
        enhanced_system_prompt = self.system_prompt + context_info
        
        # 构建消息列表
        messages = [Message(role="system", content=enhanced_system_prompt)]
        
        # 添加对话历史（已包含当前用户消息）
        history = self.state.get_history(limit=10)
        for msg in history:
            messages.append(Message(role=msg["role"], content=msg["content"]))
        
        return self.llm.chat(messages)
    
    def reset(self):
        """重置对话状态"""
        self.state = ConversationState()
    
    def get_summary(self) -> Dict[str, Any]:
        """获取对话摘要"""
        return {
            "stage": self.state.current_stage,
            "collected_info": self.state.collected_info,
            "message_count": len(self.state.messages),
        }
