"""
自动采集 Skill

从网络自动采集钓鱼知识
支持反爬应对机制
"""
import re
import time
import json
import random
import gzip
import io
from typing import Dict, Any, List, Optional, Tuple
from urllib.request import Request, urlopen, build_opener, HTTPCookieProcessor, ProxyHandler
from urllib.error import URLError, HTTPError
from urllib.parse import quote
from http.cookiejar import CookieJar

from llm import LLMFactory, BaseLLM, Message
from config.sources import DATA_SOURCES, get_search_keywords, DataSource
from skills.knowledge_collector import KnowledgeCollector
from skills.knowledge_merger import KnowledgeMerger


USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}


class AutoCollector:
    """自动采集器（带反爬应对机制）"""
    
    def __init__(
        self, 
        llm: Optional[BaseLLM] = None,
        min_delay: float = 2.0,
        max_delay: float = 5.0,
        max_retries: int = 3,
        proxy: Optional[str] = None,
        debug: bool = False
    ):
        """
        初始化自动采集器
        
        Args:
            llm: LLM 实例
            min_delay: 最小延迟（秒）
            max_delay: 最大延迟（秒）
            max_retries: 最大重试次数
            proxy: 代理地址，如 "http://127.0.0.1:7890"
            debug: 是否开启调试模式
        """
        if llm:
            self.llm = llm
        else:
            self.llm = LLMFactory.get_first_available()
        self.collector = KnowledgeCollector(self.llm)
        self.merger = KnowledgeMerger()
        
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.debug = debug
        
        self.cookie_jar = CookieJar()
        
        self.opener = self._build_opener(proxy)
        
        self.request_count = 0
        self.success_count = 0
        self.fail_count = 0
    
    def _build_opener(self, proxy: Optional[str] = None):
        """构建 URL opener"""
        handlers = [HTTPCookieProcessor(self.cookie_jar)]
        
        if proxy:
            proxy_handler = ProxyHandler({
                "http": proxy,
                "https": proxy
            })
            handlers.append(proxy_handler)
        
        return build_opener(*handlers)
    
    def _random_delay(self):
        """随机延迟，模拟人类操作"""
        delay = random.uniform(self.min_delay, self.max_delay)
        if self.debug:
            print(f"[DEBUG] 延迟 {delay:.2f} 秒...")
        time.sleep(delay)
    
    def _get_random_ua(self) -> str:
        """获取随机 User-Agent"""
        return random.choice(USER_AGENTS)
    
    def _decompress_content(self, response, content: bytes) -> bytes:
        """解压缩内容"""
        encoding = response.headers.get("Content-Encoding", "")
        if "gzip" in encoding:
            try:
                return gzip.decompress(content)
            except Exception:
                return content
        return content
    
    def fetch_url(
        self, 
        url: str, 
        headers: Optional[Dict[str, str]] = None,
        retry_count: int = 0
    ) -> str:
        """
        获取网页内容（带反爬措施）
        
        Args:
            url: 网页 URL
            headers: 额外请求头
            retry_count: 当前重试次数
            
        Returns:
            网页文本内容
        """
        self.request_count += 1
        
        request_headers = DEFAULT_HEADERS.copy()
        request_headers["User-Agent"] = self._get_random_ua()
        
        if headers:
            request_headers.update(headers)
        
        if self.debug:
            print(f"[DEBUG] 请求: {url}")
            print(f"[DEBUG] UA: {request_headers['User-Agent'][:50]}...")
        
        try:
            request = Request(url, headers=request_headers)
            
            with self.opener.open(request, timeout=15) as response:
                content = response.read()
                
                content = self._decompress_content(response, content)
                
                text = content.decode("utf-8", errors="ignore")
                
                self.success_count += 1
                
                if self.debug:
                    print(f"[DEBUG] 成功，内容长度: {len(text)} 字符")
                
                return text
                
        except HTTPError as e:
            self.fail_count += 1
            
            if e.code == 403:
                if retry_count < self.max_retries:
                    wait_time = 2 ** (retry_count + 1)
                    if self.debug:
                        print(f"[DEBUG] 403 错误，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    return self.fetch_url(url, headers, retry_count + 1)
                return f"获取失败: HTTP {e.code} (已重试 {self.max_retries} 次)"
            
            return f"获取失败: HTTP {e.code}"
            
        except URLError as e:
            self.fail_count += 1
            
            if retry_count < self.max_retries:
                wait_time = 2 ** (retry_count + 1)
                if self.debug:
                    print(f"[DEBUG] 网络错误，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
                return self.fetch_url(url, headers, retry_count + 1)
            
            return f"获取失败: {e.reason}"
            
        except Exception as e:
            self.fail_count += 1
            return f"获取失败: {e}"
    
    def extract_text_from_html(self, html: str) -> str:
        """
        从 HTML 中提取纯文本
        
        Args:
            html: HTML 内容
            
        Returns:
            纯文本
        """
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
    
    def extract_content_chunks(self, text: str, min_length: int = 200) -> List[str]:
        """
        将长文本分割成内容块
        
        Args:
            text: 长文本
            min_length: 最小块长度
            
        Returns:
            内容块列表
        """
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
    
    def collect_from_url(
        self, 
        url: str, 
        data_type: str,
        auto_save: bool = False
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        从 URL 采集知识
        
        Args:
            url: 网页 URL
            data_type: 数据类型
            auto_save: 是否自动保存
            
        Returns:
            (提取的数据列表, 消息列表)
        """
        messages = []
        results = []
        
        self._random_delay()
        
        messages.append(f"正在获取: {url}")
        html = self.fetch_url(url)
        
        if html.startswith("获取失败"):
            messages.append(f"  {html}")
            return results, messages
        
        messages.append(f"  获取成功，内容长度: {len(html)} 字符")
        
        text = self.extract_text_from_html(html)
        messages.append(f"  提取文本长度: {len(text)} 字符")
        
        chunks = self.extract_content_chunks(text)
        messages.append(f"  分割为 {len(chunks)} 个内容块")
        
        for i, chunk in enumerate(chunks):
            messages.append(f"\n  处理第 {i+1}/{len(chunks)} 块...")
            
            try:
                data = self.collector.collect(chunk, data_type)
                
                if data and data.get("name"):
                    results.append(data)
                    messages.append(f"    ✓ 提取到: {data.get('name')}")
                    
                    if auto_save:
                        success, msg = self.merger.merge(data, data_type, strategy="merge")
                        messages.append(f"      {msg}")
                
                time.sleep(0.5)
                
            except Exception as e:
                messages.append(f"    ✗ 处理失败: {e}")
        
        return results, messages
    
    def collect_from_source(
        self,
        source_name: str,
        data_type: str,
        max_pages: int = 3,
        auto_save: bool = False
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        从数据源采集知识
        
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
        
        messages.append(f"从 {source.name} 采集 {data_type} 知识")
        messages.append(f"搜索关键词: {keywords[:3]}...")
        
        for keyword in keywords[:max_pages]:
            search_url = source.get_search_url(keyword)
            if not search_url:
                continue
            
            messages.append(f"\n搜索: {keyword}")
            messages.append(f"URL: {search_url}")
            
            self._random_delay()
            html = self.fetch_url(search_url, source.headers)
            
            if html.startswith("获取失败"):
                messages.append(f"  {html}")
                continue
            
            links = self.extract_links(html, source.base_url)
            messages.append(f"  找到 {len(links)} 个链接")
            
            for j, link in enumerate(links[:2]):
                messages.append(f"\n  访问: {link}")
                page_results, page_messages = self.collect_from_url(link, data_type, auto_save)
                results.extend(page_results)
                messages.extend(page_messages)
        
        messages.append(f"\n采集完成，共提取 {len(results)} 条数据")
        messages.append(f"统计: 请求 {self.request_count} 次，成功 {self.success_count} 次，失败 {self.fail_count} 次")
        return results, messages
    
    def extract_links(self, html: str, base_url: str) -> List[str]:
        """
        从 HTML 中提取链接
        
        Args:
            html: HTML 内容
            base_url: 基础 URL
            
        Returns:
            链接列表
        """
        links = []
        
        link_pattern = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
        
        for match in link_pattern.finditer(html):
            href = match.group(1)
            
            if href.startswith("//"):
                href = "https:" + href
            elif href.startswith("/"):
                href = base_url.rstrip("/") + href
            elif not href.startswith("http"):
                continue
            
            if any(x in href.lower() for x in ["javascript:", "#", ".jpg", ".png", ".gif", ".css", ".js"]):
                continue
            
            if href not in links:
                links.append(href)
        
        return links[:10]
    
    def quick_collect(
        self,
        keyword: str,
        data_type: str,
        auto_save: bool = False
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        快速采集（使用搜索引擎风格的关键词搜索）
        
        Args:
            keyword: 搜索关键词
            data_type: 数据类型
            auto_save: 是否自动保存
            
        Returns:
            (提取的数据列表, 消息列表)
        """
        messages = []
        results = []
        
        messages.append(f"快速采集: {keyword}")
        
        for source_name, source in DATA_SOURCES.items():
            search_url = source.get_search_url(keyword)
            if not search_url:
                continue
            
            messages.append(f"\n尝试 {source.name}...")
            
            self._random_delay()
            html = self.fetch_url(search_url, source.headers)
            
            if html.startswith("获取失败"):
                messages.append(f"  {html}")
                continue
            
            links = self.extract_links(html, source.base_url)
            messages.append(f"  找到 {len(links)} 个链接")
            
            for link in links[:2]:
                try:
                    page_results, page_messages = self.collect_from_url(link, data_type, auto_save)
                    if page_results:
                        results.extend(page_results)
                        messages.extend(page_messages)
                        break
                except Exception as e:
                    messages.append(f"  错误: {e}")
            
            if results:
                break
        
        messages.append(f"\n统计: 请求 {self.request_count} 次，成功 {self.success_count} 次，失败 {self.fail_count} 次")
        return results, messages
    
    def get_stats(self) -> Dict[str, int]:
        """获取请求统计"""
        return {
            "total": self.request_count,
            "success": self.success_count,
            "failed": self.fail_count
        }


def format_collect_results(results: List[Dict[str, Any]], messages: List[str]) -> str:
    """格式化采集结果"""
    lines = ["\n📡 自动采集结果", "═" * 50]
    
    for msg in messages:
        lines.append(msg)
    
    lines.append("─" * 50)
    lines.append(f"共提取 {len(results)} 条数据:")
    
    for i, data in enumerate(results, 1):
        lines.append(f"  {i}. {data.get('name', '未知')}")
    
    lines.append("═" * 50)
    
    return "\n".join(lines)
