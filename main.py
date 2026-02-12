#!/usr/bin/env python3
"""
路亚钓鱼宗师 - 快速启动脚本
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="路亚钓鱼宗师 - AI 钓鱼指导助手"
    )
    parser.add_argument(
        "command",
        choices=["cli", "api", "version"],
        help="运行模式: cli=命令行, api=API服务, version=版本信息"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="API 服务监听地址（默认 0.0.0.0）"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="API 服务端口（默认 8000）"
    )
    
    args = parser.parse_args()
    
    if args.command == "version":
        from . import __version__
        print(f"路亚钓鱼宗师 v{__version__}")
        return
    
    if args.command == "cli":
        from cli.main import main as cli_main
        cli_main()
    
    elif args.command == "api":
        import uvicorn
        print(f"🚀 启动 API 服务: http://{args.host}:{args.port}")
        print(f"📚 API 文档: http://{args.host}:{args.port}/docs")
        uvicorn.run(
            "api.main:app",
            host=args.host,
            port=args.port,
            reload=True
        )


if __name__ == "__main__":
    main()
