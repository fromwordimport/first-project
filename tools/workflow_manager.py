import os
import time
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from dotenv import load_dotenv

load_dotenv()


class WorkflowManager:
    """工作流管理器 - 负责模型初始化、Agent创建和LLM分析"""

    def __init__(self, dimensions_config, model_name="qwen3.5-plus"):
        """
        初始化工作流管理器

        Args:
            dimensions_config: 维度配置列表
            model_name: 模型名称
        """
        self.dimensions_config = dimensions_config
        self.model_name = model_name

        # 导入动态模型和提示词构建函数
        from agent.LLM_image_recogniton import create_dynamic_model, build_prompt

        # 初始化模型
        self.model = init_chat_model(
            model=model_name,
            model_provider="openai",
            base_url=os.getenv("DASHSCOPE_BASE_URL"),
            api_key=os.getenv("DASHSCOPE_API_KEY"),
        )

        # 动态创建模型和提示词
        self.ProductDimensions = create_dynamic_model(dimensions_config)
        self.prompt = build_prompt(dimensions_config)

        # 创建 Agent
        self.agent = create_agent(
            model=self.model,
            response_format=self.ProductDimensions,
        )

    def analyze_product_images(self, skuid, image_urls):
        """
        使用LLM分析商品图片

        Args:
            skuid: 商品SKU ID
            image_urls: 图片URL列表

        Returns:
            result_dict: 分析结果字典
            'QUOTA_EXHAUSTED': API配额耗尽标记
            None: 分析失败
        """
        if not image_urls:
            print(f"⚠️ SKUID {skuid} 没有图片，跳过分析")
            return None

        print(f"🤖 正在使用LLM分析 SKUID {skuid} 的 {len(image_urls)} 张图片...")

        try:
            # 构建消息
            message = HumanMessage([
                {"type": "text", "text": self.prompt},
                *[{"type": "image", "url": url} for url in image_urls],
            ])

            # 调用Agent
            response = self.agent.invoke({"messages": [message]})

            # 提取结构化数据
            structured_response = response.get("structured_response")

            if structured_response:
                result_dict = structured_response.model_dump()
                print(f"✅ SKUID {skuid} 分析完成")
                return result_dict
            else:
                print(f"❌ SKUID {skuid} 未获取到结构化响应")
                return None

        except Exception as e:
            error_msg = str(e)
            # 检测 API 配额耗尽错误
            if 'AllocationQuota.FreeTierOnly' in error_msg or 'free tier' in error_msg.lower():
                print("\n" + "!" * 60)
                print("⚠️  模型用量已达上限！")
                print("!" * 60)
                print("免费额度已用尽，请选择以下方案：")
                print("1. 登录阿里云 DashScope 控制台开通付费服务")
                print("2. 更换为其他有免费额度的模型（如 qwen-turbo）")
                print("3. 等待下一个计费周期重置免费额度")
                print("!" * 60)
                return 'QUOTA_EXHAUSTED'
            else:
                print(f"❌ SKUID {skuid} 分析失败：{e}")
                return None

    def batch_analyze_products(self, skuid_image_map, file_handler, products_filepath, delay=3):
        """
        批量分析商品图片并保存结果

        Args:
            skuid_image_map: SKUID到图片URL的映射
            file_handler: FileHandler实例
            products_filepath: 产品CSV文件完整路径
            delay: 每次API调用后的延迟时间（秒）

        Returns:
            bool: 是否成功完成所有分析
        """
        total = len(skuid_image_map)

        for idx, (skuid, image_urls) in enumerate(skuid_image_map.items(), 1):
            print(f"\n[{idx}/{total}] 处理 SKUID {skuid}")

            # 分析图片
            result_dict = self.analyze_product_images(skuid, image_urls)

            # 检查是否配额耗尽
            if result_dict == 'QUOTA_EXHAUSTED':
                print("\n❌ 由于API配额耗尽，终止分析流程")
                return False

            if result_dict:
                # 更新CSV
                file_handler.update_csv_with_llm_results(
                    products_filepath,
                    skuid,
                    result_dict
                )

            # 避免API请求过快
            time.sleep(delay)

        return True