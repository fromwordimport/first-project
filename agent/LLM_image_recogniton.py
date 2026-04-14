from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
import os
import shutil
from dotenv import load_dotenv
from tools.jd_scraper import JdProductScraper
from tools.image_processor import image_url_to_base64
from tools.dimension_manager import DimensionManager, query_dimensions_with_tavily, get_default_dimensions
from pydantic import BaseModel, Field, create_model
from typing import Optional

load_dotenv()


def create_dynamic_model(dimensions: list) -> type[BaseModel]:
    """
    根据维度列表动态创建 Pydantic 模型

    Args:
        dimensions: 维度列表，可以是字符串列表或字典列表

    Returns:
        动态创建的 Pydantic 模型类
    """
    field_definitions = {}

    for dim in dimensions:
        if isinstance(dim, str):
            field_definitions[dim] = (
                Optional[str],
                Field(default=None, description=f"{dim}")
            )
        elif isinstance(dim, dict):
            name = dim.get("name")
            desc = dim.get("description", name)
            field_type = dim.get("type", str)
            required = dim.get("required", False)

            if required:
                field_definitions[name] = (
                    field_type,
                    Field(description=desc)
                )
            else:
                field_definitions[name] = (
                    Optional[field_type],
                    Field(default=None, description=desc)
                )

    DynamicModel = create_model(
        "ProductDimensions",
        __doc__="产品信息提取结果（动态生成）",
        **field_definitions
    )

    return DynamicModel


def build_prompt(dimensions: list, category: str = "") -> str:
    """
    根据维度列表构建提示词

    Args:
        dimensions: 维度列表
        category: 品类名称

    Returns:
        格式化后的提示词
    """
    if isinstance(dimensions[0], dict):
        dim_names = [d["name"] for d in dimensions]
    else:
        dim_names = dimensions

    dim_str = ", ".join(dim_names)

    category_info = f"（品类：{category}）" if category else ""

    prompt_text = f"""
    **任务：产品信息提取{category_info}**
    请根据已提供的产品详情页图片数据（整体处理），提取以下指定维度的信息：{dim_str}。

    **输入说明：**
    - 图片数据已通过外部方式传入模型（无需路径，模型直接处理）。
    - 提取维度：{dim_names}

    **输出要求：**
    1. 返回一个**结构化字典**，包含每个指定维度的信息，键为维度名称，值为提取内容。
    2. 若某维度信息缺失，标记为 "未知"。
    3. 若维度存在多个值，用逗号分隔（如 "红色, 蓝色"）或列表形式返回。
    4. 仅基于图片中的**显式文本和视觉信息**提取，无需推理或假设。
    5. 忽略无关干扰，聚焦指定维度。

    **立即执行并返回结果：**
    {{维度1: 值1, 维度2: 值2, ...}}
    """
    return prompt_text


def initialize_model(model_name="qwen3.5-plus"):
    """
    初始化聊天模型

    Args:
        model_name: 模型名称

    Returns:
        model: 初始化的聊天模型
    """
    model = init_chat_model(
        model=model_name,
        model_provider="openai",
        base_url=os.getenv("DASHSCOPE_BASE_URL"),
        api_key=os.getenv("DASHSCOPE_API_KEY"),
    )

    return model


def create_agent_with_model(model, response_format=None):
    """
    创建 Agent

    Args:
        model: 聊天模型
        response_format: Pydantic 模型类，用于结构化输出

    Returns:
        agent: 创建的 Agent
    """
    if response_format:
        agent = create_agent(model=model, response_format=response_format)
    else:
        agent = create_agent(model=model)
    return agent


def select_dimensions(category: str = None) -> tuple:
    """
    智能选择分析维度

    Args:
        category: 用户输入的品类名称，如果为 None 则手动选择

    Returns:
        dimensions_config: 维度配置列表
        selected_category: 实际使用的品类名称
        source: 维度来源（builtin/tavily/default）
    """
    dimension_mgr = DimensionManager()

    if not category:
        print("\n可用品类模板：")
        available = dimension_mgr.list_available_categories()
        for i, cat in enumerate(available, 1):
            print(f"  {i}. {cat}")
        print(f"  {len(available) + 1}. 自定义品类（将使用 Tavily 查询）")

        choice = input(f"\n请选择品类（输入编号或品类名称）：").strip()

        if choice.isdigit():
            idx = int(choice) - 1
            if idx < len(available):
                category = available[idx]
            else:
                category = input("请输入品类名称：").strip()
        else:
            category = choice

    print(f"\n📋 分析品类：{category}")
    print('-' * 60)

    dimensions = dimension_mgr.get_dimensions_for_category(category)

    if dimensions:
        return dimensions, category, "builtin"

    print(f"⚠️ 未找到 '{category}' 的内置模板")
    use_tavily = input("是否使用 Tavily 查询该品类的维度？(y/n，默认y)：").strip().lower()

    if use_tavily != 'n':
        try:
            dimensions = query_dimensions_with_tavily(category)
            return dimensions, category, "tavily"
        except Exception as e:
            print(f"Tavily 查询失败：{e}")

    print("使用默认通用维度")
    dimensions = get_default_dimensions()
    return dimensions, category, "default"


def ensure_data_file(csv_filename='all_product_images.csv', products_dir='products_file', tools_dir='tools'):
    """
    确保数据文件存在，如不存在则从备份目录复制

    Args:
        csv_filename: CSV 文件名
        products_dir: 目标目录
        tools_dir: 源目录

    Returns:
        csv_filename: 文件名（不含路径）
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_file = os.path.join(project_root, products_dir, csv_filename)
    tools_csv_file = os.path.join(project_root, tools_dir, csv_filename)

    if not os.path.exists(os.path.join(project_root, products_dir)):
        os.makedirs(os.path.join(project_root, products_dir))
        print(f'✅ 创建目录: {os.path.join(project_root, products_dir)}')

    if not os.path.exists(csv_file):
        if os.path.exists(tools_csv_file):
            print(f"📋 从 {tools_csv_file} 复制到 {csv_file}")
            shutil.copy2(tools_csv_file, csv_file)
        else:
            raise FileNotFoundError(
                f"数据文件不存在\n"
                f"  目标位置: {csv_file}\n"
                f"  备份位置: {tools_csv_file}\n"
                f"请先运行 main.py 或 tools/jd_scraper.py 获取商品图片数据"
            )
    else:
        print(f"✅ 找到数据文件: {csv_file}")

    return csv_filename


def load_product_images(scraper, csv_filename='all_product_images.csv'):
    """
    加载商品图片数据

    Args:
        scraper: JdProductScraper 实例
        csv_filename: CSV 文件名

    Returns:
        all_products_images: 字典，key 为 SKU，value 为图片 URL 列表
    """
    csv_path = os.path.join('products_file', csv_filename)
    all_products_images = scraper.file_handler.load_product_images_from_csv(csv_path)

    if not all_products_images:
        raise ValueError(f"文件中没有图片数据: {csv_path}")

    print(f"✅ 成功加载 {len(all_products_images)} 个商品的图片数据")
    return all_products_images


def select_product_for_analysis(all_products_images, skuid=None):
    """
    选择要分析的商品

    Args:
        all_products_images: 所有商品图片数据
        skuid: 指定 SKU ID，如果为 None 则选择第一个

    Returns:
        selected_skuid: 选中的 SKU ID
        loaded_urls: 该商品的图片 URL 列表
        category: 商品品类（如果有）
    """
    if skuid and skuid in all_products_images:
        selected_skuid = skuid
    else:
        selected_skuid = list(all_products_images.keys())[0]

    loaded_urls = all_products_images[selected_skuid]

    category = None
    if hasattr(all_products_images, '_categories'):
        category = all_products_images._categories.get(selected_skuid)

    print(f"📦 使用商品 SKU: {selected_skuid}")
    if category:
        print(f"🏷️  品类: {category}")
    print(f"🖼️  该商品共有 {len(loaded_urls)} 张图片")

    return selected_skuid, loaded_urls, category


def build_message(prompt, loaded_urls, use_base64=False):
    """
    构建发送给模型的消息

    Args:
        prompt: 提示词文本
        loaded_urls: 图片 URL 列表
        use_base64: 是否使用 base64 编码

    Returns:
        message: HumanMessage 对象
    """
    if use_base64:
        base64_images = [image_url_to_base64(url) for url in loaded_urls]
        message = HumanMessage([
            {"type": "text", "text": prompt},
            *[{"type": "image_url", "image_url": {"url": base64_img}} for base64_img in base64_images],
        ])
    else:
        message = HumanMessage([
            {"type": "text", "text": prompt},
            *[{"type": "image", "url": url} for url in loaded_urls],
        ])

    return message


def invoke_agent(agent, message, debug=False):
    """
    调用 Agent 进行分析

    Args:
        agent: Agent 实例
        message: 消息对象
        debug: 是否开启调试模式，打印原始响应

    Returns:
        response: Agent 响应
    """
    try:
        print("🤖 正在调用 Agent 进行分析...")
        response = agent.invoke({"messages": [message]})
        print("✅ Agent 分析完成")

        if debug:
            print("\n【调试信息】完整响应结构:")
            print(f"响应 keys: {response.keys()}")
            if "messages" in response:
                for i, msg in enumerate(response["messages"]):
                    print(f"\n消息 {i + 1}:")
                    print(f"  类型: {type(msg).__name__}")
                    print(f"  内容预览: {str(msg.content)[:200]}...")

        return response
    except Exception as e:
        print(f"\n❌ 调用失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def extract_structured_response(response):
    """
    从 Agent 响应中提取结构化数据

    Args:
        response: Agent 响应

    Returns:
        result_dict: 结构化的结果字典，如果失败则返回 None
    """
    if not response:
        return None

    structured_response = response.get("structured_response")

    if structured_response:
        result_dict = structured_response.model_dump()
        return result_dict
    else:
        messages = response.get("messages", [])
        if messages:
            last_message = messages[-1]
            print(f"\n⚠️ 未获取到结构化响应，模型原始响应:")
            print(last_message.content)
        else:
            print("❌ 未获取到任何响应")
        return None


def display_results(result_dict):
    """
    显示分析结果

    Args:
        result_dict: 结果字典
    """
    if not result_dict:
        print("❌ 没有可显示的结果")
        return

    print("\n=== 结构化结果（字典格式）===")
    print(result_dict)

    print("\n=== 键值对格式 ===")
    for key, value in result_dict.items():
        print(f"{key}: {value}")

    result_list = [
        {"维度": key, "值": value}
        for key, value in result_dict.items()
    ]

    print("\n=== 列表格式（适合CSV）===")
    print(result_list)

    return result_list


if __name__ == '__main__':
    print('=' * 60)
    print('智能产品信息提取系统')
    print('=' * 60)

    print('\n【步骤1】初始化模型')
    print('-' * 60)
    model = initialize_model(model_name="qwen3.5-plus")

    print('\n【步骤2】智能选择分析维度')
    print('-' * 60)

    category_input = None
    dimensions_config, selected_category, dimension_source = select_dimensions(category_input)

    print(f"\n维度来源：{dimension_source}")
    print(f"配置了 {len(dimensions_config)} 个分析维度")

    print('\n【步骤3】创建分析模型')
    print('-' * 60)
    ProductDimensions = create_dynamic_model(dimensions_config)
    prompt = build_prompt(dimensions_config, selected_category)

    print('\n【步骤4】创建 Agent（启用结构化输出）')
    print('-' * 60)
    agent = create_agent_with_model(model, response_format=ProductDimensions)
    print('✅ Agent 已配置结构化输出格式')

    print('\n【步骤5】加载商品图片数据')
    print('-' * 60)
    from tools.file_handler import FileHandler
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    products_dir = os.path.join(project_root, 'products_file')
    file_handler = FileHandler(base_path=products_dir)
    scraper = JdProductScraper(file_handler=file_handler)
    
    csv_filename = ensure_data_file()
    all_products_images = load_product_images(scraper, csv_filename)

    print('\n【步骤6】选择要分析的商品')
    print('-' * 60)
    selected_skuid, loaded_urls, product_category = select_product_for_analysis(all_products_images)

    if not product_category and selected_category:
        print(f"\n⚠️  CSV 中未记录品类信息，正在更新...")
        scraper.file_handler.update_product_category(selected_skuid, selected_category)
        product_category = selected_category

    print('\n【步骤7】构建分析消息')
    print('-' * 60)
    message = build_message(prompt, loaded_urls, use_base64=False)
    print(loaded_urls)
    print(f'消息包含: 1 段文本 + {len(loaded_urls)} 张图片')

    print('\n【步骤8】调用 Agent 分析')
    print('-' * 60)
    response = invoke_agent(agent, message, debug=True)

    print('\n【步骤9】提取并显示结果')
    print('-' * 60)
    result_dict = extract_structured_response(response)
    result_list = display_results(result_dict)

    print('\n' + '=' * 60)
    print('分析完成')
    print('=' * 60)
