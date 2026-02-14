"""
浏览器采集 Skill

使用 Playwright 模拟浏览器进行知识采集
支持反爬应对：模拟人类操作、随机延迟、无头模式
"""
import re
import os
import time
import random
import platform
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from llm import LLMFactory, BaseLLM
from config.sources import DATA_SOURCES, get_search_keywords, DataSource
from skills.knowledge_collector import KnowledgeCollector
from skills.knowledge_merger import KnowledgeMerger


PLAYWRIGHT_AVAILABLE = False
BROWSER_TYPE = None

try:
    from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
    BROWSER_TYPE = "playwright"
except ImportError:
    pass


def find_chrome_executable() -> Optional[str]:
    """查找系统 Chrome 可执行文件"""
    system = platform.system()
    
    if system == "Darwin":
        paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ]
    elif system == "Windows":
        paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
    else:
        paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
        ]
    
    for path in paths:
        if Path(path).exists():
            return path
    
    return None


class BrowserCollector:
    """浏览器采集器（使用 Playwright）"""
    
    def __init__(
        self,
        llm: Optional[BaseLLM] = None,
        headless: bool = True,
        slow_mo: int = 100,
        timeout: int = 30000,
        debug: bool = False
    ):
        """
        初始化浏览器采集器
        
        Args:
            llm: LLM 实例
            headless: 是否无头模式（True=后台运行，False=显示浏览器窗口）
            slow_mo: 操作延迟（毫秒），模拟人类操作速度
            timeout: 页面加载超时（毫秒）
            debug: 是否开启调试模式
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright 未安装！\n"
                "请执行以下命令安装：\n"
                "  pip install playwright -i https://pypi.tuna.tsinghua.edu.cn/simple\n"
                "或者使用 /collect 命令手动粘贴内容"
            )
        
        if llm:
            self.llm = llm
        else:
            self.llm = LLMFactory.get_first_available()
        self.collector = KnowledgeCollector(self.llm)
        self.merger = KnowledgeMerger()
        
        self.headless = headless
        self.slow_mo = slow_mo
        self.timeout = timeout
        self.debug = debug
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
        self.request_count = 0
        self.success_count = 0
        self.fail_count = 0
    
    def _init_browser(self):
        """初始化浏览器"""
        if self.browser:
            return
        
        if self.debug:
            print("[DEBUG] 启动浏览器...")
        
        self.playwright = sync_playwright().start()
        
        chrome_path = find_chrome_executable()
        
        launch_options = {
            "headless": self.headless,
            "slow_mo": self.slow_mo,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--no-first-run",
                "--no-default-browser-check",
            ]
        }
        
        if chrome_path:
            if self.debug:
                print(f"[DEBUG] 使用系统 Chrome: {chrome_path}")
            launch_options["executable_path"] = chrome_path
            launch_options["channel"] = None
        else:
            if self.debug:
                print("[DEBUG] 使用 Playwright 内置 Chromium")
        
        try:
            self.browser = self.playwright.chromium.launch(**launch_options)
        except Exception as e:
            if "doesn't exist" in str(e) or "not installed" in str(e):
                raise ImportError(
                    "浏览器未安装！\n"
                    "请执行以下命令安装 Chromium：\n"
                    "  python3 -m playwright install chromium\n"
                    "或者安装 Google Chrome 浏览器\n"
                    "或者使用 /collect 命令手动粘贴内容"
                )
            raise
        
        self.context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="zh-CN",
            ignore_https_errors=True,
        )
        
        self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        if self.debug:
            print("[DEBUG] 浏览器启动成功")
    
    def _close_browser(self):
        """关闭浏览器"""
        if self.context:
            self.context.close()
            self.context = None
        if self.browser:
            self.browser.close()
            self.browser = None
        if self.playwright:
            self.playwright.stop()
            self.playwright = None
        
        if self.debug:
            print("[DEBUG] 浏览器已关闭")
    
    def _random_delay(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """随机延迟"""
        delay = random.uniform(min_sec, max_sec)
        if self.debug:
            print(f"[DEBUG] 延迟 {delay:.2f} 秒...")
        time.sleep(delay)
    
    def _human_like_scroll(self, page):
        """模拟人类滚动"""
        scroll_times = random.randint(2, 5)
        for _ in range(scroll_times):
            scroll_distance = random.randint(200, 500)
            page.mouse.wheel(0, scroll_distance)
            time.sleep(random.uniform(0.3, 0.8))
    
    def _human_like_mouse_move(self, page, x: int, y: int):
        """模拟人类鼠标移动"""
        current = page.evaluate("() => ({ x: window.mouseX || 0, y: window.mouseY || 0 })")
        steps = random.randint(10, 20)
        
        for i in range(steps):
            progress = (i + 1) / steps
            intermediate_x = int(current["x"] + (x - current["x"]) * progress)
            intermediate_y = int(current["y"] + (y - current["y"]) * progress)
            page.mouse.move(intermediate_x, intermediate_y)
            time.sleep(random.uniform(0.01, 0.03))
        
        page.mouse.move(x, y)
    
    def fetch_page(self, url: str, wait_selector: str = None) -> str:
        """
        获取页面内容
        
        Args:
            url: 页面 URL
            wait_selector: 等待的元素选择器
            
        Returns:
            页面文本内容
        """
        self._init_browser()
        self.request_count += 1
        
        page = self.context.new_page()
        
        try:
            if self.debug:
                print(f"[DEBUG] 访问: {url}")
            
            page.goto(url, timeout=self.timeout, wait_until="networkidle")
            
            self._random_delay(0.5, 1.5)
            
            if wait_selector:
                page.wait_for_selector(wait_selector, timeout=self.timeout)
            
            self._human_like_scroll(page)
            
            content = page.content()
            text = self._extract_text(content)
            
            self.success_count += 1
            
            if self.debug:
                print(f"[DEBUG] 获取成功，内容长度: {len(text)} 字符")
            
            return text
            
        except Exception as e:
            self.fail_count += 1
            if self.debug:
                print(f"[DEBUG] 获取失败: {e}")
            return f"获取失败: {e}"
            
        finally:
            page.close()
    
    def _extract_text(self, html: str) -> str:
        """从 HTML 中提取纯文本"""
        text = html
        
        script_pattern = re.compile(r'<script[^>]*>[\s\S]*?</script>', re.IGNORECASE)
        style_pattern = re.compile(r'<style[^>]*>[\s\S]*?</style>', re.IGNORECASE)
        text = script_pattern.sub('', text)
        text = style_pattern.sub('', text)
        
        text = re.sub(r'<br[^>]*>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</div>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&gt;', '>', text)
        text = re.sub(r'&quot;', '"', text)
        
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    def search_and_collect(
        self,
        source_name: str,
        data_type: str,
        max_pages: int = 3,
        auto_save: bool = False
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        搜索并采集知识
        
        Args:
            source_name: 数据源名称
            data_type: 数据类型
            max_pages: 最大页面数
            auto_save: 是否自动保存
            
        Returns:
            (提取的数据列表, 消息列表)
        """
        messages = []
        results = []
        
        source = DATA_SOURCES.get(source_name)
        if not source:
            messages.append(f"未知数据源: {source_name}")
            return results, messages
        
        keywords = get_search_keywords(data_type)
        if not keywords:
            messages.append(f"未定义 {data_type} 的搜索关键词")
            return results, messages
        
        messages.append(f"从 {source.name} 采集 {data_type} 知识（浏览器模式）")
        messages.append(f"搜索关键词: {keywords[:3]}...")
        
        try:
            self._init_browser()
            
            for keyword in keywords[:max_pages]:
                search_url = source.get_search_url(keyword)
                if not search_url:
                    continue
                
                messages.append(f"\n搜索: {keyword}")
                messages.append(f"URL: {search_url}")
                
                page = self.context.new_page()
                
                try:
                    page.goto(search_url, timeout=self.timeout, wait_until="networkidle")
                    self._random_delay(1.0, 2.0)
                    
                    self._human_like_scroll(page)
                    
                    links = self._extract_links(page, source.base_url)
                    messages.append(f"  找到 {len(links)} 个链接")
                    
                    for link in links[:2]:
                        messages.append(f"\n  访问: {link}")
                        
                        page_result = self._collect_from_page(page, link, data_type, auto_save)
                        results.extend(page_result["data"])
                        messages.extend([f"    {m}" for m in page_result["messages"]])
                        
                        self._random_delay(2.0, 4.0)
                        
                except Exception as e:
                    messages.append(f"  页面处理失败: {e}")
                    
                finally:
                    page.close()
                    
        except Exception as e:
            messages.append(f"浏览器错误: {e}")
            
        finally:
            self._close_browser()
        
        messages.append(f"\n采集完成，共提取 {len(results)} 条数据")
        messages.append(f"统计: 请求 {self.request_count} 次，成功 {self.success_count} 次，失败 {self.fail_count} 次")
        return results, messages
    
    def _extract_links(self, page, base_url: str) -> List[str]:
        """从页面中提取链接"""
        links = []
        
        try:
            elements = page.query_selector_all("a[href]")
            
            base_domain = base_url.replace("https://", "").replace("http://", "").split("/")[0]
            
            article_patterns = ["/jiqiao/", "/yuhuo/", "/article/", "/post/", "/p/", "/detail/"]
            
            for elem in elements[:100]:
                href = elem.get_attribute("href")
                if not href:
                    continue
                
                if href.startswith("//"):
                    href = "https:" + href
                elif href.startswith("/"):
                    href = base_url.rstrip("/") + href
                elif not href.startswith("http"):
                    continue
                
                if any(x in href.lower() for x in ["javascript:", "#", ".jpg", ".png", ".gif", ".css", ".js", ".pdf"]):
                    continue
                
                if any(x in href.lower() for x in ["baidu.com", "google.com", "bing.com"]):
                    continue
                
                if base_domain not in href:
                    continue
                
                skip_patterns = ["/member/", "/login", "/register", "/about/", "/citys", "/search"]
                if any(x in href.lower() for x in skip_patterns):
                    continue
                
                if href == base_url or href == base_url.rstrip("/"):
                    continue
                
                if href not in links:
                    links.append(href)
                    
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] 提取链接失败: {e}")
        
        return links[:10]
    
    def _collect_from_page(
        self,
        parent_page,
        url: str,
        data_type: str,
        auto_save: bool
    ) -> Dict[str, Any]:
        """从单个页面采集知识"""
        result = {"data": [], "messages": []}
        
        page = self.context.new_page()
        
        try:
            page.goto(url, timeout=self.timeout, wait_until="networkidle")
            self._random_delay(0.5, 1.5)
            
            self._human_like_scroll(page)
            
            content = page.content()
            text = self._extract_text(content)
            
            result["messages"].append(f"获取成功，内容长度: {len(text)} 字符")
            
            chunks = self._split_text(text)
            result["messages"].append(f"分割为 {len(chunks)} 个内容块")
            
            for i, chunk in enumerate(chunks):
                result["messages"].append(f"处理第 {i+1}/{len(chunks)} 块...")
                
                try:
                    data = self.collector.collect(chunk, data_type)
                    
                    if data and data.get("name"):
                        result["data"].append(data)
                        result["messages"].append(f"✓ 提取到: {data.get('name')}")
                        
                        if auto_save:
                            success, msg = self.merger.merge(data, data_type, strategy="merge")
                            result["messages"].append(f"  {msg}")
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    result["messages"].append(f"✗ 处理失败: {e}")
            
            self.success_count += 1
                    
        except Exception as e:
            self.fail_count += 1
            result["messages"].append(f"获取失败: {e}")
            
        finally:
            page.close()
        
        return result
    
    def _split_text(self, text: str, min_length: int = 200) -> List[str]:
        """分割文本"""
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(current_chunk) + len(para) < 2000:
                current_chunk += "\n\n" + para if current_chunk else para
            else:
                if len(current_chunk) >= min_length:
                    chunks.append(current_chunk)
                current_chunk = para
        
        if len(current_chunk) >= min_length:
            chunks.append(current_chunk)
        
        return chunks
    
    def get_stats(self) -> Dict[str, int]:
        """获取请求统计"""
        return {
            "total": self.request_count,
            "success": self.success_count,
            "failed": self.fail_count
        }


def check_playwright_available() -> Tuple[bool, str]:
    """检查 Playwright 是否可用"""
    if PLAYWRIGHT_AVAILABLE:
        return True, "Playwright 已安装"
    else:
        return False, (
            "Playwright 未安装！\n"
            "请执行以下命令安装：\n"
            "  pip install playwright\n"
            "  playwright install chromium\n"
            "或者使用 /collect 命令手动粘贴内容"
        )


def format_browser_results(results: List[Dict[str, Any]], messages: List[str]) -> str:
    """格式化浏览器采集结果"""
    lines = ["\n🌐 浏览器采集结果", "═" * 50]
    
    for msg in messages:
        lines.append(msg)
    
    lines.append("─" * 50)
    lines.append(f"共提取 {len(results)} 条数据:")
    
    for i, data in enumerate(results, 1):
        lines.append(f"  {i}. {data.get('name', '未知')}")
    
    lines.append("═" * 50)
    
    return "\n".join(lines)
