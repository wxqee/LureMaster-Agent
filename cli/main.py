#!/usr/bin/env python3
"""
路亚钓鱼宗师 - CLI 命令行界面
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import print as rprint

from agents import LureMasterAgent
from llm import LLMFactory
from config.settings import get_settings
from skills import (
    KnowledgeCollector, 
    KnowledgeMerger, 
    AutoCollector, 
    format_collect_results,
    KnowledgeManager,
    VectorStore,
    check_vector_search_available
)
from skills.browser_collector import BrowserCollector, check_playwright_available, format_browser_results


console = Console()


def print_banner():
    """打印欢迎横幅"""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     🎣 欢迎来到【路亚钓鱼宗师】🎣                             ║
║                                                               ║
║     我是您的专属路亚钓鱼顾问，拥有30年实战经验               ║
║     让我们一起制定完美的钓鱼计划吧！                         ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
    console.print(banner, style="bold green")


def print_help():
    """打印帮助信息"""
    help_text = """
## 使用说明

直接告诉我您的钓鱼计划，例如：
- "明天打算早起钓鳜鱼"
- "周末想去太湖钓鱼"
- "后天下午去阳澄湖，想钓翘嘴"

我会帮您：
1. 确认钓鱼时间和地点
2. 查询当地天气情况
3. 推荐合适的装备和饵料
4. 指导最佳的钓法和时段

## 命令

- `help` - 显示帮助信息
- `status` - 查看当前对话状态
- `reset` - 重置对话，开始新的计划
- `/stats` - 查看知识库统计
- `/collect <类型>` - 手动收集新知识（类型: fish/lure/rig/spot_type）
- `/auto-collect <类型>` - 自动采集知识（纯 HTTP，可能被拦截）
- `/browser-collect <类型>` - 浏览器模式采集（推荐，需要安装 Playwright）
- `/save-knowledge <类型> <名称>` - 保存 AI 生成的知识到知识库
- `/feedback <类型> <名称> <good/bad>` - 对知识进行反馈
- `/search <关键词>` - 语义搜索知识库
- `/verify <类型> <名称>` - 验证知识（标记为已确认）
- `quit` / `exit` - 退出程序

## 智能知识生成

当您查询的鱼种不在知识库中时，我会：
1. 自动使用 AI 生成该鱼种的路亚钓鱼知识
2. 在回复中标记「[AI生成]」
3. 提示您可以使用 `/save-knowledge` 保存到知识库

## 知识质量

知识库中的每条知识都有置信度和验证状态：
- 置信度：根据来源自动设置（专家录入 > 手动录入 > 网页采集 > AI 生成）
- 验证状态：可通过 `/verify` 命令标记为已验证
- 用户反馈：可通过 `/feedback` 命令提交反馈，帮助改进知识质量
"""
    console.print(Panel(Markdown(help_text), title="帮助", border_style="blue"))


def print_status(agent: LureMasterAgent):
    """打印当前状态"""
    summary = agent.get_summary()
    
    table = Table(title="当前状态", show_header=True, header_style="bold magenta")
    table.add_column("项目", style="cyan")
    table.add_column("内容", style="green")
    
    table.add_row("当前阶段", summary["stage"])
    
    collected = summary["collected_info"]
    if collected:
        for key, value in collected.items():
            if value and key not in ["weather", "knowledge"]:
                table.add_row(key, str(value))
    
    table.add_row("消息数量", str(summary["message_count"]))
    
    console.print(table)


def check_environment():
    """检查运行环境"""
    settings = get_settings()
    
    # 检查 LLM 可用性
    available_llms = LLMFactory.get_available_llms()
    
    if not available_llms:
        console.print("[yellow]⚠️  没有检测到可用的 LLM API Key[/yellow]")
        console.print("[yellow]   程序将以模拟模式运行，功能受限[/yellow]")
        console.print("")
        console.print("[cyan]请配置以下任一 API Key：[/cyan]")
        console.print("  - 通义千问: https://bailian.console.aliyun.com/")
        console.print("  - 智谱 GLM: https://open.bigmodel.cn/api-keys")
        console.print("  - DeepSeek: https://platform.deepseek.com/api_keys")
        console.print("")
        console.print("[cyan]配置方法：[/cyan]")
        console.print("  1. 复制 .env.example 为 .env")
        console.print("  2. 编辑 .env 填入您的 API Key")
        console.print("")
        return False
    
    console.print(f"[green]✓ 检测到可用 LLM: {', '.join(available_llms)}[/green]")
    
    # 检查工具 API
    if settings.mock_mode:
        console.print("[yellow]⚠️  工具 API 未配置，将使用模拟数据[/yellow]")
    else:
        console.print("[green]✓ 工具 API 已配置[/green]")
    
    return True


def handle_collect_command():
    """处理 /collect 命令"""
    console.print("\n[cyan]请输入要收集的知识类型：[/cyan]")
    console.print("  - fish: 鱼种")
    console.print("  - lure: 路亚饵")
    console.print("  - rig: 钓组")
    console.print("  - spot_type: 标点类型")
    
    data_type = Prompt.ask("[bold green]类型[/bold green]").strip().lower()
    
    if data_type not in KnowledgeCollector.SUPPORTED_TYPES:
        console.print(f"[red]不支持的类型: {data_type}[/red]")
        return
    
    console.print(f"\n[cyan]请粘贴要提取的{KnowledgeCollector.TYPE_NAMES.get(data_type, data_type)}相关文本：[/cyan]")
    console.print("[dim]（输入空行结束）[/dim]")
    
    lines = []
    while True:
        line = input()
        if not line:
            break
        lines.append(line)
    
    text = "\n".join(lines)
    if not text.strip():
        console.print("[yellow]未输入任何内容[/yellow]")
        return
    
    console.print("\n[cyan]正在提取知识...[/cyan]")
    
    try:
        collector = KnowledgeCollector()
        data = collector.collect(text, data_type)
        
        if not data:
            console.print("[yellow]未能提取到有效数据[/yellow]")
            return
        
        console.print(collector.format_output(data, data_type))
        
        if Confirm.ask("\n是否保存到知识库？"):
            merger = KnowledgeMerger()
            merger.backup()
            success, msg = merger.merge(data, data_type, strategy="merge")
            
            if success:
                console.print(f"[green]✓ {msg}[/green]")
            else:
                console.print(f"[yellow]{msg}[/yellow]")
    
    except Exception as e:
        console.print(f"[red]处理失败: {e}[/red]")


def handle_stats_command():
    """处理 /stats 命令"""
    try:
        manager = KnowledgeManager()
        console.print(manager.format_stats())
        
        low_confidence = manager.get_low_confidence_knowledge(threshold=0.8)
        if low_confidence:
            console.print(f"\n[yellow]⚠️  有 {len(low_confidence)} 条知识需要审核：[/yellow]")
            for item in low_confidence[:5]:
                console.print(f"  - {item['type']}/{item['name']} (置信度: {item['confidence']:.0%})")
    except Exception as e:
        console.print(f"[red]获取统计失败: {e}[/red]")


def handle_auto_collect_command(args: str = ""):
    """处理 /auto-collect 命令"""
    parts = args.strip().split(maxsplit=1) if args else []
    
    if not parts:
        console.print("\n[cyan]请输入要采集的知识类型：[/cyan]")
        console.print("  - fish: 鱼种")
        console.print("  - lure: 路亚饵")
        console.print("  - rig: 钓组")
        console.print("  - spot_type: 标点类型")
        data_type = Prompt.ask("[bold green]类型[/bold green]").strip().lower()
        keyword = ""
    else:
        data_type = parts[0].lower()
        keyword = parts[1] if len(parts) > 1 else ""
    
    if data_type not in KnowledgeCollector.SUPPORTED_TYPES:
        console.print(f"[red]不支持的类型: {data_type}[/red]")
        return
    
    console.print("\n[cyan]请选择数据源：[/cyan]")
    console.print("  - tieba: 百度贴吧（推荐，反爬较松）")
    console.print("  - zhihu: 知乎（需要登录态，可能失败）")
    console.print("  - fishing_home: 钓鱼之家")
    source_name = Prompt.ask("[bold green]数据源[/bold green]", default="tieba").strip().lower()
    
    auto_save = Confirm.ask("\n是否自动保存到知识库？", default=False)
    
    debug_mode = Confirm.ask("是否开启调试模式？", default=False)
    
    console.print("\n[cyan]开始自动采集...[/cyan]")
    console.print("[dim]这可能需要一些时间，请耐心等待...[/dim]")
    console.print("[dim]已启用反爬措施：随机延迟、UA轮换、Cookie管理[/dim]")
    
    try:
        collector = AutoCollector(debug=debug_mode)
        
        if keyword:
            results, messages = collector.quick_collect(keyword, data_type, auto_save)
        else:
            results, messages = collector.collect_from_source(source_name, data_type, max_pages=2, auto_save=auto_save)
        
        console.print(format_collect_results(results, messages))
        
        stats = collector.get_stats()
        console.print(f"\n[dim]请求统计: 总计 {stats['total']} 次, 成功 {stats['success']} 次, 失败 {stats['failed']} 次[/dim]")
        
        if results and not auto_save:
            if Confirm.ask(f"\n发现 {len(results)} 条数据，是否保存到知识库？"):
                merger = KnowledgeMerger()
                merger.backup()
                for data in results:
                    success, msg = merger.merge(data, data_type, strategy="merge")
                    console.print(f"  {msg}")
    
    except Exception as e:
        console.print(f"[red]采集失败: {e}[/red]")


def handle_browser_collect_command(args: str = ""):
    """处理 /browser-collect 命令"""
    available, message = check_playwright_available()
    if not available:
        console.print(f"\n[red]{message}[/red]")
        return
    
    parts = args.strip().split(maxsplit=1) if args else []
    
    if not parts:
        console.print("\n[cyan]请输入要采集的知识类型：[/cyan]")
        console.print("  - fish: 鱼种")
        console.print("  - lure: 路亚饵")
        console.print("  - rig: 钓组")
        console.print("  - spot_type: 标点类型")
        data_type = Prompt.ask("[bold green]类型[/bold green]").strip().lower()
        keyword = ""
    else:
        data_type = parts[0].lower()
        keyword = parts[1] if len(parts) > 1 else ""
    
    if data_type not in KnowledgeCollector.SUPPORTED_TYPES:
        console.print(f"[red]不支持的类型: {data_type}[/red]")
        return
    
    console.print("\n[cyan]请选择数据源：[/cyan]")
    console.print("  - tieba: 百度贴吧")
    console.print("  - zhihu: 知乎")
    console.print("  - fishing_home: 钓鱼之家")
    source_name = Prompt.ask("[bold green]数据源[/bold green]", default="zhihu").strip().lower()
    
    headless = not Confirm.ask("\n是否显示浏览器窗口？", default=False)
    auto_save = Confirm.ask("是否自动保存到知识库？", default=False)
    debug_mode = Confirm.ask("是否开启调试模式？", default=False)
    
    console.print("\n[cyan]启动浏览器采集...[/cyan]")
    console.print("[dim]这可能需要一些时间，请耐心等待...[/dim]")
    if headless:
        console.print("[dim]无头模式运行（后台）[/dim]")
    else:
        console.print("[dim]有头模式运行（可见浏览器窗口）[/dim]")
    
    try:
        collector = BrowserCollector(headless=headless, debug=debug_mode)
        
        if keyword:
            console.print("[yellow]浏览器模式暂不支持关键词搜索，将使用默认关键词[/yellow]")
        
        results, messages = collector.search_and_collect(source_name, data_type, max_pages=2, auto_save=auto_save)
        
        console.print(format_browser_results(results, messages))
        
        stats = collector.get_stats()
        console.print(f"\n[dim]请求统计: 总计 {stats['total']} 次, 成功 {stats['success']} 次, 失败 {stats['failed']} 次[/dim]")
        
        if results and not auto_save:
            if Confirm.ask(f"\n发现 {len(results)} 条数据，是否保存到知识库？"):
                merger = KnowledgeMerger()
                merger.backup()
                for data in results:
                    success, msg = merger.merge(data, data_type, strategy="merge")
                    console.print(f"  {msg}")
    
    except Exception as e:
        console.print(f"[red]浏览器采集失败: {e}[/red]")


def handle_save_knowledge_command(agent: LureMasterAgent, data_type: str = "", name: str = ""):
    """处理 /save-knowledge 命令 - 保存 LLM 生成的知识到知识库"""
    if not data_type:
        console.print("\n[cyan]请输入要保存的知识类型：[/cyan]")
        console.print("  - fish: 鱼种")
        console.print("  - lure: 路亚饵")
        console.print("  - spot_type: 标点类型")
        data_type = Prompt.ask("[bold green]类型[/bold green]").strip().lower()
    
    if data_type not in ["fish", "lure", "spot_type"]:
        console.print(f"[red]不支持的类型: {data_type}[/red]")
        return
    
    generated_knowledge = agent.state.generated_knowledge
    
    matching_items = []
    for key, item in generated_knowledge.items():
        if item["type"] == data_type:
            matching_items.append(item)
    
    if not matching_items:
        console.print(f"[yellow]当前会话中没有 AI 生成的 {data_type} 知识[/yellow]")
        console.print("[dim]提示：当您查询知识库中不存在的鱼种时，AI 会自动生成相关知识[/dim]")
        return
    
    if not name:
        console.print(f"\n[cyan]当前会话中 AI 生成的 {data_type} 知识：[/cyan]")
        for i, item in enumerate(matching_items, 1):
            console.print(f"  {i}. {item['name']}")
        
        name = Prompt.ask("[bold green]请输入要保存的名称[/bold green]").strip()
    
    target_item = None
    for item in matching_items:
        if item["name"] == name or name in item["name"]:
            target_item = item
            break
    
    if not target_item:
        console.print(f"[yellow]未找到「{name}」的生成知识[/yellow]")
        return
    
    data = target_item["data"]
    
    console.print(f"\n[cyan]即将保存的知识：[/cyan]")
    from skills import KnowledgeGenerator
    generator = KnowledgeGenerator()
    console.print(generator.format_output(data, data_type))
    
    if not Confirm.ask("\n确认保存到知识库？"):
        console.print("[yellow]已取消[/yellow]")
        return
    
    try:
        manager = KnowledgeManager()
        manager.backup()
        success, msg = manager.add_knowledge(
            data, data_type, 
            source="llm_generated",
            verified=False
        )
        
        if success:
            console.print(f"[green]✓ {msg}[/green]")
        else:
            console.print(f"[red]✗ {msg}[/red]")
    except Exception as e:
        console.print(f"[red]保存失败: {e}[/red]")


def handle_feedback_command(data_type: str = "", name: str = "", feedback_type: str = ""):
    """处理 /feedback 命令 - 提交知识反馈"""
    if not data_type:
        console.print("\n[cyan]请输入要反馈的知识类型：[/cyan]")
        console.print("  - fish: 鱼种")
        console.print("  - lure: 路亚饵")
        console.print("  - spot_type: 标点类型")
        data_type = Prompt.ask("[bold green]类型[/bold green]").strip().lower()
    
    if data_type not in ["fish", "lure", "spot_type"]:
        console.print(f"[red]不支持的类型: {data_type}[/red]")
        return
    
    if not name:
        name = Prompt.ask("[bold green]请输入知识名称[/bold green]").strip()
    
    if not feedback_type:
        console.print("\n[cyan]请选择反馈类型：[/cyan]")
        console.print("  - good: 正面反馈（知识准确有用）")
        console.print("  - bad: 负面反馈（知识有误或无用）")
        feedback_type = Prompt.ask("[bold green]反馈类型[/bold green]", choices=["good", "bad"]).strip().lower()
    
    try:
        manager = KnowledgeManager()
        success, msg = manager.add_feedback(data_type, name, feedback_type == "good")
        
        if success:
            console.print(f"[green]✓ {msg}[/green]")
            console.print("[dim]感谢您的反馈，这将帮助我们改进知识质量！[/dim]")
        else:
            console.print(f"[red]✗ {msg}[/red]")
    except Exception as e:
        console.print(f"[red]反馈失败: {e}[/red]")


def handle_search_command(query: str = ""):
    """处理 /search 命令 - 语义搜索知识库"""
    if not query:
        query = Prompt.ask("[bold green]请输入搜索关键词[/bold green]").strip()
    
    if not query:
        console.print("[yellow]请输入搜索关键词[/yellow]")
        return
    
    available, msg = check_vector_search_available()
    
    if not available:
        console.print(f"[yellow]{msg}[/yellow]")
        console.print("[cyan]使用关键词搜索...[/cyan]")
        
        from tools import ToolManager
        tools = ToolManager()
        result = tools.run_tool("knowledge", query=query)
        
        if result.success and result.data:
            console.print(f"\n[cyan]找到 {len(result.data)} 条相关知识：[/cyan]")
            for item in result.data[:5]:
                data = item.get("data", {})
                console.print(f"  - {data.get('name', '未知')} ({item.get('category', '')})")
        else:
            console.print("[yellow]未找到相关知识[/yellow]")
        return
    
    try:
        vector_store = VectorStore()
        results = vector_store.hybrid_search(query, top_k=5)
        
        if results:
            console.print(f"\n[cyan]找到 {len(results)} 条相关知识：[/cyan]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("名称", style="cyan")
            table.add_column("类型", style="green")
            table.add_column("相关度", style="yellow")
            table.add_column("来源", style="dim")
            
            for result in results:
                meta = result.data.get("_meta", {})
                source_map = {
                    "expert": "专家录入",
                    "manual": "手动录入",
                    "collected": "网页采集",
                    "llm_generated": "AI生成",
                }
                source = source_map.get(meta.get("source", ""), "未知")
                score = f"{result.score:.0%}"
                
                table.add_row(
                    result.data.get("name", "未知"),
                    result.data_type,
                    score,
                    source
                )
            
            console.print(table)
        else:
            console.print("[yellow]未找到相关知识[/yellow]")
    except Exception as e:
        console.print(f"[red]搜索失败: {e}[/red]")


def handle_verify_command(data_type: str = "", name: str = ""):
    """处理 /verify 命令 - 验证知识"""
    if not data_type:
        console.print("\n[cyan]请输入要验证的知识类型：[/cyan]")
        console.print("  - fish: 鱼种")
        console.print("  - lure: 路亚饵")
        console.print("  - spot_type: 标点类型")
        data_type = Prompt.ask("[bold green]类型[/bold green]").strip().lower()
    
    if data_type not in ["fish", "lure", "spot_type"]:
        console.print(f"[red]不支持的类型: {data_type}[/red]")
        return
    
    if not name:
        name = Prompt.ask("[bold green]请输入知识名称[/bold green]").strip()
    
    try:
        manager = KnowledgeManager()
        success, msg = manager.verify_knowledge(data_type, name, verified_by="user")
        
        if success:
            console.print(f"[green]✓ {msg}[/green]")
            console.print("[dim]该知识已标记为已验证，置信度提升至 100%[/dim]")
        else:
            console.print(f"[red]✗ {msg}[/red]")
    except Exception as e:
        console.print(f"[red]验证失败: {e}[/red]")


def main():
    """主函数"""
    print_banner()
    check_environment()
    print_help()
    
    try:
        agent = LureMasterAgent()
        console.print("[green]✓ Agent 初始化成功[/green]")
    except Exception as e:
        console.print(f"[red]✗ Agent 初始化失败: {e}[/red]")
        console.print("[yellow]请检查 API Key 配置[/yellow]")
        return
    
    console.print("")
    console.print("[bold cyan]请告诉我您的钓鱼计划，我来帮您分析！[/bold cyan]")
    console.print("[dim]（输入 help 查看帮助，quit 退出）[/dim]")
    console.print("")
    
    while True:
        try:
            user_input = Prompt.ask("[bold green]您[/bold green]").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["quit", "exit", "q"]:
                console.print("")
                console.print("[bold cyan]感谢使用路亚钓鱼宗师！祝您爆护！🎣[/bold cyan]")
                break
            
            elif user_input.lower() == "help":
                print_help()
                continue
            
            elif user_input.lower() == "status":
                print_status(agent)
                continue
            
            elif user_input.lower() == "reset":
                agent.reset()
                console.print("[green]✓ 对话已重置，请开始新的钓鱼计划[/green]")
                continue
            
            elif user_input.lower() == "/stats":
                handle_stats_command()
                continue
            
            elif user_input.lower().startswith("/collect"):
                parts = user_input.split(maxsplit=1)
                if len(parts) > 1:
                    data_type = parts[1].strip().lower()
                    os.environ["COLLECT_TYPE"] = data_type
                handle_collect_command()
                continue
            
            elif user_input.lower().startswith("/auto-collect"):
                parts = user_input.split(maxsplit=2)
                args = parts[1] if len(parts) > 1 else ""
                if len(parts) > 2:
                    args += " " + parts[2]
                handle_auto_collect_command(args)
                continue
            
            elif user_input.lower().startswith("/browser-collect"):
                parts = user_input.split(maxsplit=2)
                args = parts[1] if len(parts) > 1 else ""
                if len(parts) > 2:
                    args += " " + parts[2]
                handle_browser_collect_command(args)
                continue
            
            elif user_input.lower().startswith("/save-knowledge"):
                parts = user_input.split(maxsplit=2)
                data_type = parts[1] if len(parts) > 1 else ""
                name = parts[2] if len(parts) > 2 else ""
                handle_save_knowledge_command(agent, data_type, name)
                continue
            
            elif user_input.lower().startswith("/feedback"):
                parts = user_input.split(maxsplit=3)
                data_type = parts[1] if len(parts) > 1 else ""
                name = parts[2] if len(parts) > 2 else ""
                feedback_type = parts[3] if len(parts) > 3 else ""
                handle_feedback_command(data_type, name, feedback_type)
                continue
            
            elif user_input.lower().startswith("/search"):
                parts = user_input.split(maxsplit=1)
                query = parts[1] if len(parts) > 1 else ""
                handle_search_command(query)
                continue
            
            elif user_input.lower().startswith("/verify"):
                parts = user_input.split(maxsplit=2)
                data_type = parts[1] if len(parts) > 1 else ""
                name = parts[2] if len(parts) > 2 else ""
                handle_verify_command(data_type, name)
                continue
            
            console.print("")
            with console.status("[bold cyan]思考中...[/bold cyan]"):
                response = agent.chat(user_input)
            
            console.print(Panel(response, title="[bold yellow]路亚宗师[/bold yellow]", border_style="yellow"))
            console.print("")
            
        except KeyboardInterrupt:
            console.print("")
            console.print("[bold cyan]感谢使用路亚钓鱼宗师！祝您爆护！🎣[/bold cyan]")
            break
        except Exception as e:
            console.print(f"[red]发生错误: {e}[/red]")
            console.print("[yellow]请重试或输入 reset 重置对话[/yellow]")


if __name__ == "__main__":
    main()
