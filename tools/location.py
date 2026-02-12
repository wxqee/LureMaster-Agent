"""
地理工具
使用高德地图 API 获取地理信息
"""
from typing import Optional
from .base import BaseTool, ToolResult
from config.settings import get_settings


class LocationTool(BaseTool):
    """地理查询工具"""
    
    name = "location"
    description = "获取地点的地理信息"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化地理工具
        
        Args:
            api_key: 高德地图 API Key
        """
        settings = get_settings()
        self.api_key = api_key or settings.amap_api_key
        mock_mode = settings.mock_mode or not self._check_api_key()
        super().__init__(mock_mode=mock_mode)
        
        self.base_url = "https://restapi.amap.com/v3"
    
    def _check_api_key(self) -> bool:
        """检查 API Key 是否有效"""
        return bool(self.api_key and self.api_key != "your_amap_key_here")
    
    def run(self, address: str) -> ToolResult:
        """
        地址解析
        
        Args:
            address: 地址字符串
            
        Returns:
            地理信息
        """
        if self.mock_mode:
            return self._get_mock_location(address)
        
        try:
            import requests
            
            url = f"{self.base_url}/geocode/geo"
            params = {
                "address": address,
                "key": self.api_key,
                "output": "json"
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get("status") == "1" and data.get("geocodes"):
                geocode = data["geocodes"][0]
                location = geocode.get("location", "").split(",")
                
                result = {
                    "name": address,
                    "province": geocode.get("province"),
                    "city": geocode.get("city"),
                    "district": geocode.get("district"),
                    "longitude": float(location[0]) if len(location) == 2 else None,
                    "latitude": float(location[1]) if len(location) == 2 else None,
                    "level": geocode.get("level"),
                    "formatted_address": geocode.get("formatted_address"),
                }
                
                return ToolResult(
                    success=True,
                    data=result,
                    message=f"成功解析地址: {address}"
                )
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"无法解析地址: {address}"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"地理解析失败: {str(e)}"
            )
    
    def search_poi(self, keywords: str, city: Optional[str] = None) -> ToolResult:
        """
        搜索兴趣点（钓点）
        
        Args:
            keywords: 搜索关键词
            city: 城市名称
            
        Returns:
            POI 列表
        """
        if self.mock_mode:
            return self._get_mock_poi(keywords)
        
        try:
            import requests
            
            url = f"{self.base_url}/place/text"
            params = {
                "keywords": keywords,
                "city": city or "",
                "key": self.api_key,
                "output": "json",
                "offset": 10,
                "page": 1,
                "extensions": "all"
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get("status") == "1":
                pois = data.get("pois", [])
                result = []
                
                for poi in pois:
                    location = poi.get("location", "").split(",")
                    result.append({
                        "name": poi.get("name"),
                        "address": poi.get("address"),
                        "type": poi.get("type"),
                        "longitude": float(location[0]) if len(location) == 2 else None,
                        "latitude": float(location[1]) if len(location) == 2 else None,
                        "distance": poi.get("distance"),
                    })
                
                return ToolResult(
                    success=True,
                    data=result,
                    message=f"找到 {len(result)} 个相关地点"
                )
            else:
                return ToolResult(
                    success=False,
                    data=[],
                    error="搜索失败"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data=[],
                error=f"POI 搜索失败: {str(e)}"
            )
    
    def _get_mock_location(self, address: str) -> ToolResult:
        """获取模拟地理数据"""
        mock_data = {
            "name": address,
            "province": "江苏省",
            "city": "苏州市",
            "district": "吴中区",
            "longitude": 120.619585,
            "latitude": 31.299379,
            "level": "风景名胜",
            "formatted_address": f"江苏省苏州市吴中区{address}",
        }
        
        return ToolResult(
            success=True,
            data=mock_data,
            message=f"[模拟模式] 解析地址: {address}"
        )
    
    def _get_mock_poi(self, keywords: str) -> ToolResult:
        """获取模拟 POI 数据"""
        mock_pois = [
            {
                "name": "太湖国家湿地公园",
                "address": "江苏省苏州市吴中区太湖大道",
                "type": "风景名胜;公园",
                "longitude": 120.456,
                "latitude": 31.234,
                "distance": None,
            },
            {
                "name": "金鸡湖",
                "address": "江苏省苏州市工业园区金鸡湖大道",
                "type": "风景名胜;湖泊",
                "longitude": 120.678,
                "latitude": 31.312,
                "distance": None,
            },
            {
                "name": "阳澄湖",
                "address": "江苏省苏州市相城区阳澄湖镇",
                "type": "风景名胜;湖泊",
                "longitude": 120.789,
                "latitude": 31.456,
                "distance": None,
            },
        ]
        
        return ToolResult(
            success=True,
            data=mock_pois,
            message=f"[模拟模式] 找到 {len(mock_pois)} 个相关钓点"
        )
