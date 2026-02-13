"""
数据源配置

定义可自动采集的数据源
"""
from typing import Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import quote


class SourceType(Enum):
    """数据源类型"""
    WEB = "web"
    ZHIHU = "zhihu"
    TIEBA = "tieba"
    FORUM = "forum"


@dataclass
class DataSource:
    """数据源定义"""
    name: str
    source_type: SourceType
    base_url: str
    search_url: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    requires_auth: bool = False
    auth_info: str = ""
    
    def get_search_url(self, keyword: str) -> str:
        """获取搜索 URL"""
        if self.search_url:
            encoded_keyword = quote(keyword, safe='')
            return self.search_url.format(keyword=encoded_keyword)
        return ""


DATA_SOURCES: Dict[str, DataSource] = {
    "zhihu": DataSource(
        name="知乎",
        source_type=SourceType.ZHIHU,
        base_url="https://www.zhihu.com",
        search_url="https://www.zhihu.com/search?type=content&q={keyword}",
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
    ),
    "tieba": DataSource(
        name="百度贴吧",
        source_type=SourceType.TIEBA,
        base_url="https://tieba.baidu.com",
        search_url="https://tieba.baidu.com/f/search/res?ie=utf-8&qw={keyword}",
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
    ),
    "fishing_home": DataSource(
        name="钓鱼之家",
        source_type=SourceType.FORUM,
        base_url="https://www.diaoyu.com",
        search_url="https://so.diaoyu.com/cse/search?s=1682567125356849292&q={keyword}",
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
    ),
}


SEARCH_KEYWORDS: Dict[str, List[str]] = {
    "fish": [
        "路亚 鱼种 习性",
        "路亚 目标鱼",
        "路亚 鳜鱼 钓法",
        "路亚 鲈鱼 技巧",
        "路亚 翘嘴 饵料",
    ],
    "lure": [
        "路亚饵 种类 使用",
        "路亚 软虫 钓法",
        "路亚 米诺 技巧",
        "路亚 铁板 远投",
        "路亚 VIB 跳底",
    ],
    "rig": [
        "路亚钓组 组装",
        "德州钓组 防挂",
        "倒钓钓组 精细",
        "卡罗钓组 搜索",
    ],
    "spot_type": [
        "路亚 标点 寻找",
        "路亚 桥墩 钓点",
        "路亚 水草 黑鱼",
        "路亚 障碍区 鳜鱼",
    ],
}


def get_source(source_name: str) -> DataSource:
    """获取数据源"""
    return DATA_SOURCES.get(source_name)


def get_all_sources() -> List[DataSource]:
    """获取所有数据源"""
    return list(DATA_SOURCES.values())


def get_search_keywords(data_type: str) -> List[str]:
    """获取搜索关键词"""
    return SEARCH_KEYWORDS.get(data_type, [])
