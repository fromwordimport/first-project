from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class DimensionManager:
    """维度管理器：负责维度的选择和管理"""

    def __init__(self):
        self.templates = self._load_builtin_templates()

    def _load_builtin_templates(self) -> dict:
        """
        加载内置的品类维度模板

        Returns:
            templates: 字典，key 为品类名称，value 为维度列表
        """
        return {
            '洗碗机': [
                {"name": "喷淋臂类型", "description": "喷淋臂的类型", "type": str, "required": False},
                {"name": "喷淋臂数量", "description": "喷淋臂的数量", "type": str, "required": False},
                {"name": "颜色", "description": "产品颜色", "type": str, "required": False},
                {"name": "内胆材质", "description": "内胆材质", "type": str, "required": False},
                {"name": "机身高度", "description": "机身高度", "type": str, "required": False},
                {"name": "套数", "description": "洗碗机套数", "type": str, "required": False},
                {"name": "碗篮层数", "description": "碗篮的层数", "type": str, "required": False},
                {"name": "洗涤程序", "description": "洗涤程序", "type": str, "required": False},
                {"name": "烘干方式", "description": "烘干方式", "type": str, "required": False},
                {"name": "清洁指数", "description": "清洁指数", "type": str, "required": False},
                {"name": "干燥指数", "description": "干燥指数", "type": str, "required": False},
                {"name": "水效等级", "description": "水效等级", "type": str, "required": False},
                {"name": "产品尺寸", "description": "产品尺寸（长x宽x高）", "type": str, "required": False},
                {"name": "智能投放", "description": "是否支持智能投放", "type": str, "required": False},
                {"name": "水压", "description": "工作水压", "type": str, "required": False},
                {"name": "消杀等级", "description": "消杀等级", "type": str, "required": False},
                {"name": "存储时长", "description": "餐具存储时长", "type": str, "required": False},
            ],
            '冰箱': [
                {"name": "容量", "description": "总容量（升）", "type": str, "required": False},
                {"name": "制冷方式", "description": "制冷方式（直冷/风冷/混冷）", "type": str, "required": False},
                {"name": "能效等级", "description": "能效等级", "type": str, "required": False},
                {"name": "压缩机类型", "description": "压缩机类型（定频/变频）", "type": str, "required": False},
                {"name": "颜色", "description": "产品颜色", "type": str, "required": False},
                {"name": "产品尺寸", "description": "产品尺寸（长x宽x高）", "type": str, "required": False},
                {"name": "门款式", "description": "门款式（单门/双门/三门/对开门等）", "type": str, "required": False},
                {"name": "冷冻能力", "description": "冷冻能力（kg/12h）", "type": str, "required": False},
                {"name": "噪音值", "description": "运行噪音（dB）", "type": str, "required": False},
            ],
            '洗衣机': [
                {"name": "洗涤容量", "description": "洗涤容量（kg）", "type": str, "required": False},
                {"name": "脱水容量", "description": "脱水容量（kg）", "type": str, "required": False},
                {"name": "电机类型", "description": "电机类型（BLDC/DD直驱等）", "type": str, "required": False},
                {"name": "能效等级", "description": "能效等级", "type": str, "required": False},
                {"name": "洗涤程序", "description": "洗涤程序数量及类型", "type": str, "required": False},
                {"name": "转速", "description": "脱水转速（转/分钟）", "type": str, "required": False},
                {"name": "颜色", "description": "产品颜色", "type": str, "required": False},
                {"name": "产品尺寸", "description": "产品尺寸（长x宽x高）", "type": str, "required": False},
                {"name": "烘干功能", "description": "是否支持烘干", "type": str, "required": False},
                {"name": "智能控制", "description": "是否支持智能控制（WiFi/APP）", "type": str, "required": False},
            ],
            '空调': [
                {"name": "匹数", "description": "空调匹数", "type": str, "required": False},
                {"name": "能效等级", "description": "能效等级", "type": str, "required": False},
                {"name": "制冷量", "description": "制冷量（W）", "type": str, "required": False},
                {"name": "制热量", "description": "制热量（W）", "type": str, "required": False},
                {"name": "适用面积", "description": "适用面积（平方米）", "type": str, "required": False},
                {"name": "变频类型", "description": "是否变频", "type": str, "required": False},
                {"name": "颜色", "description": "产品颜色", "type": str, "required": False},
                {"name": "产品尺寸", "description": "产品尺寸（长x宽x高）", "type": str, "required": False},
                {"name": "噪音值", "description": "运行噪音（dB）", "type": str, "required": False},
                {"name": "智能控制", "description": "是否支持智能控制", "type": str, "required": False},
            ],
            '电视': [
                {"name": "屏幕尺寸", "description": "屏幕尺寸（英寸）", "type": str, "required": False},
                {"name": "分辨率", "description": "屏幕分辨率", "type": str, "required": False},
                {"name": "显示技术", "description": "显示技术（LED/OLED/QLED等）", "type": str, "required": False},
                {"name": "刷新率", "description": "屏幕刷新率（Hz）", "type": str, "required": False},
                {"name": "HDR支持", "description": "支持的HDR格式", "type": str, "required": False},
                {"name": "操作系统", "description": "智能系统", "type": str, "required": False},
                {"name": "内存配置", "description": "运行内存+存储内存", "type": str, "required": False},
                {"name": "接口类型", "description": "接口类型及数量", "type": str, "required": False},
                {"name": "产品尺寸", "description": "产品尺寸（含底座）", "type": str, "required": False},
            ],
        }

    def get_dimensions_for_category(self, category: str) -> Optional[list]:
        """
        根据品类获取对应的维度配置

        Args:
            category: 品类名称

        Returns:
            dimensions: 维度列表，如果未找到则返回 None
        """
        # 精确匹配
        if category in self.templates:
            print(f"✅ 找到内置模板：{category}")
            return self.templates[category]

        # 模糊匹配
        for template_category in self.templates.keys():
            if category in template_category or template_category in category:
                print(f"✅ 匹配到内置模板：{template_category}（基于：{category}）")
                return self.templates[template_category]

        return None

    def list_available_categories(self) -> list:
        """
        列出所有可用的内置品类

        Returns:
            categories: 品类名称列表
        """
        return list(self.templates.keys())


def query_dimensions_with_tavily(category: str) -> list:
    """
    使用 Tavily 查询品类的分析维度

    Args:
        category: 品类名称

    Returns:
        dimensions: 查询到的维度列表
    """
    try:
        from langchain_community.tools.tavily_search import TavilySearchResults

        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not tavily_api_key:
            print("⚠️ 警告：未配置 TAVILY_API_KEY 环境变量")
            print("   如需使用 Tavily 查询功能，请在 .env 文件中添加：")
            print("   TAVILY_API_KEY=your_api_key_here")
            print("   获取地址：https://app.tavily.com/")
            print("\n⚠️ 降级使用默认通用维度")
            return get_default_dimensions()

        search_tool = TavilySearchResults(
            max_results=3,
            include_raw_content=True
        )

        query = f"{category}产品的关键参数和规格维度有哪些？请列出最重要的8-15个技术参数。"

        print(f"🔍 正在使用 Tavily 查询 {category} 的分析维度...")
        search_results = search_tool.invoke(query)

        dimensions = parse_tavily_results_to_dimensions(search_results, category)

        print(f"✅ 通过 Tavily 查询到 {len(dimensions)} 个维度")
        return dimensions

    except ImportError:
        print("⚠️ 警告：未安装 langchain-community 包")
        print("   请运行：pip install langchain-community")
        print("   降级使用默认通用维度")
        return get_default_dimensions()
    except Exception as e:
        print(f"❌ Tavily 查询失败：{e}")
        print("⚠️ 使用默认通用维度")
        return get_default_dimensions()


def parse_tavily_results_to_dimensions(search_results: list, category: str) -> list:
    """
    将 Tavily 搜索结果解析为维度列表

    Args:
        search_results: Tavily 搜索结果
        category: 品类名称

    Returns:
        dimensions: 维度列表
    """
    # 从搜索结果中提取关键信息
    content_text = ""
    for result in search_results:
        if isinstance(result, dict):
            content_text += result.get('content', '') + "\n"
            content_text += result.get('raw_content', '')[:500] + "\n"

    # 这里可以进一步优化，使用 LLM 从文本中提取结构化维度
    # 暂时返回基于常见参数的通用维度
    return generate_dimensions_from_text(content_text, category)


def generate_dimensions_from_text(text: str, category: str) -> list:
    """
    从文本中生成维度列表（简化版）

    Args:
        text: 包含维度信息的文本
        category: 品类名称

    Returns:
        dimensions: 维度列表
    """
    # 通用的产品维度
    common_dimensions = [
        {"name": "品牌", "description": "产品品牌", "type": str, "required": False},
        {"name": "型号", "description": "产品型号", "type": str, "required": False},
        {"name": "颜色", "description": "产品颜色", "type": str, "required": False},
        {"name": "产品尺寸", "description": "产品尺寸（长x宽x高）", "type": str, "required": False},
        {"name": "重量", "description": "产品重量", "type": str, "required": False},
        {"name": "功率", "description": "额定功率", "type": str, "required": False},
        {"name": "能效等级", "description": "能效等级", "type": str, "required": False},
        {"name": "材质", "description": "主要材质", "type": str, "required": False},
        {"name": "保修期", "description": "保修期限", "type": str, "required": False},
        {"name": "产地", "description": "生产产地", "type": str, "required": False},
    ]

    # 根据品类添加特定维度
    category_specific = {
        '电器': [
            {"name": "电压", "description": "工作电压", "type": str, "required": False},
            {"name": "频率", "description": "工作频率", "type": str, "required": False},
            {"name": "智能功能", "description": "智能功能特性", "type": str, "required": False},
        ],
    }

    # 简单关键词匹配
    for keyword, dims in category_specific.items():
        if keyword in category:
            common_dimensions.extend(dims)
            break

    return common_dimensions[:15]  # 限制最多15个维度


def get_default_dimensions() -> list:
    """
    获取默认通用维度

    Returns:
        dimensions: 默认维度列表
    """
    return [
        {"name": "品牌", "description": "产品品牌", "type": str, "required": False},
        {"name": "型号", "description": "产品型号", "type": str, "required": False},
        {"name": "颜色", "description": "产品颜色", "type": str, "required": False},
        {"name": "产品尺寸", "description": "产品尺寸", "type": str, "required": False},
        {"name": "重量", "description": "产品重量", "type": str, "required": False},
        {"name": "材质", "description": "主要材质", "type": str, "required": False},
        {"name": "功率", "description": "额定功率", "type": str, "required": False},
        {"name": "能效等级", "description": "能效等级", "type": str, "required": False},
        {"name": "保修期", "description": "保修期限", "type": str, "required": False},
    ]