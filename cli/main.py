#!/usr/bin/env python3
"""
路亚钓鱼宗师 - CLI 命令行界面
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table
from rich import print as rprint

from agents import LureMasterAgent
from llm import LLMFactory
from config.settings import get_settings


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
- `quit` / `exit` - 退出程序
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
        console.print("  - 通义千问: https://dashscope.console.aliyun.com/apiKey")
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


def main():
    """主函数"""
    print_banner()
    check_environment()
    print_help()
    
    # 初始化 Agent
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
    
    # 主循环
    while True:
        try:
            user_input = Prompt.ask("[bold green]您[/bold green]").strip()
            
            if not user_input:
                continue
            
            # 处理命令
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
            
            # 与 Agent 对话
            console.print("")
            with console.status("[bold cyan]思考中...[/bold cyan]"):
                response = agent.chat(user_input)
            
            # 显示回复
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
