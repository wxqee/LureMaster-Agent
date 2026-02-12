"""
天气工具
使用和风天气 API 获取天气信息
"""
from typing import Optional
from .base import BaseTool, ToolResult
from config.settings import get_settings


class WeatherTool(BaseTool):
    """天气查询工具"""
    
    name = "weather"
    description = "获取指定地点的天气信息"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化天气工具
        
        Args:
            api_key: 和风天气 API Key
        """
        settings = get_settings()
        self.api_key = api_key or settings.qweather_api_key
        mock_mode = settings.mock_mode or not self._check_api_key()
        super().__init__(mock_mode=mock_mode)
        
        self.base_url = "https://devapi.qweather.com/v7"
    
    def _check_api_key(self) -> bool:
        """检查 API Key 是否有效"""
        return bool(self.api_key and self.api_key != "your_qweather_key_here")
    
    def run(self, location: str, days: int = 3) -> ToolResult:
        """
        获取天气信息
        
        Args:
            location: 地点名称或坐标
            days: 预报天数（1-7）
            
        Returns:
            天气信息
        """
        if self.mock_mode:
            return self._get_mock_weather(location, days)
        
        try:
            import requests
            
            # 先获取地点的 location_id
            location_id = self._get_location_id(location)
            if not location_id:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"无法找到地点: {location}"
                )
            
            # 获取天气预报
            url = f"{self.base_url}/weather/{days}d"
            params = {
                "location": location_id,
                "key": self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get("code") == "200":
                weather_data = self._parse_weather_data(data)
                return ToolResult(
                    success=True,
                    data=weather_data,
                    message=f"成功获取 {location} 的天气信息"
                )
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"API 返回错误: {data.get('code')}"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"获取天气信息失败: {str(e)}"
            )
    
    def _get_location_id(self, location: str) -> Optional[str]:
        """获取地点的 location_id"""
        import requests
        
        url = "https://geoapi.qweather.com/v2/city/lookup"
        params = {
            "location": location,
            "key": self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get("code") == "200" and data.get("location"):
                return data["location"][0].get("id")
        except:
            pass
        
        return None
    
    def _parse_weather_data(self, data: dict) -> dict:
        """解析天气数据"""
        daily = data.get("daily", [])
        result = {
            "forecast": [],
            "fishing_suitability": []
        }
        
        for day in daily:
            forecast = {
                "date": day.get("fxDate"),
                "temp_max": day.get("tempMax"),
                "temp_min": day.get("tempMin"),
                "text_day": day.get("textDay"),
                "text_night": day.get("textNight"),
                "wind_dir": day.get("windDirDay"),
                "wind_scale": day.get("windScaleDay"),
                "humidity": day.get("humidity"),
                "pressure": day.get("pressure"),
            }
            result["forecast"].append(forecast)
            
            # 评估钓鱼适宜度
            suitability = self._evaluate_fishing_suitability(forecast)
            result["fishing_suitability"].append(suitability)
        
        return result
    
    def _evaluate_fishing_suitability(self, forecast: dict) -> dict:
        """评估钓鱼适宜度"""
        score = 100
        reasons = []
        
        # 温度评估
        temp_max = int(forecast.get("temp_max", 20))
        temp_min = int(forecast.get("temp_min", 10))
        
        if temp_max > 35 or temp_min < 5:
            score -= 30
            reasons.append("温度极端，不太适合钓鱼")
        elif temp_max > 30 or temp_min < 10:
            score -= 10
            reasons.append("温度偏高/偏低，注意选择时段")
        
        # 天气评估
        text_day = forecast.get("text_day", "")
        bad_weather = ["雨", "雪", "雷", "暴", "台风"]
        for bw in bad_weather:
            if bw in text_day:
                score -= 20
                reasons.append(f"天气不佳：{text_day}")
                break
        
        # 风力评估
        wind_scale = forecast.get("wind_scale", "1")
        try:
            wind_level = int(wind_scale.replace("级", ""))
            if wind_level >= 5:
                score -= 15
                reasons.append(f"风力较大：{wind_scale}")
        except:
            pass
        
        # 气压评估
        pressure = forecast.get("pressure", "1010")
        try:
            p = int(pressure)
            if p < 1000:
                score -= 10
                reasons.append("气压偏低，鱼活性可能下降")
        except:
            pass
        
        if score >= 80:
            level = "极佳"
        elif score >= 60:
            level = "适宜"
        elif score >= 40:
            level = "一般"
        else:
            level = "不推荐"
        
        return {
            "date": forecast.get("date"),
            "score": score,
            "level": level,
            "reasons": reasons if reasons else ["天气条件良好"]
        }
    
    def _get_mock_weather(self, location: str, days: int) -> ToolResult:
        """获取模拟天气数据"""
        mock_data = {
            "forecast": [
                {
                    "date": "2024-01-15",
                    "temp_max": "18",
                    "temp_min": "8",
                    "text_day": "晴",
                    "text_night": "晴",
                    "wind_dir": "东南风",
                    "wind_scale": "3级",
                    "humidity": "65",
                    "pressure": "1015",
                },
                {
                    "date": "2024-01-16",
                    "temp_max": "20",
                    "temp_min": "10",
                    "text_day": "多云",
                    "text_night": "晴",
                    "wind_dir": "东风",
                    "wind_scale": "2级",
                    "humidity": "60",
                    "pressure": "1018",
                },
                {
                    "date": "2024-01-17",
                    "temp_max": "22",
                    "temp_min": "12",
                    "text_day": "晴",
                    "text_night": "多云",
                    "wind_dir": "东北风",
                    "wind_scale": "2级",
                    "humidity": "55",
                    "pressure": "1020",
                },
            ],
            "fishing_suitability": [
                {"date": "2024-01-15", "score": 85, "level": "极佳", "reasons": ["天气条件良好"]},
                {"date": "2024-01-16", "score": 90, "level": "极佳", "reasons": ["天气条件良好"]},
                {"date": "2024-01-17", "score": 88, "level": "极佳", "reasons": ["天气条件良好"]},
            ]
        }
        
        return ToolResult(
            success=True,
            data=mock_data,
            message=f"[模拟模式] 获取 {location} 的天气信息"
        )
