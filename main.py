import os
import time
from dotenv import load_dotenv
from tools.jd_scraper import JdProductScraper
from tools.file_handler import FileHandler
from tools.dimension_manager import DimensionManager
from tools.workflow_manager import WorkflowManager

load_dotenv()


class ProductAnalysisWorkflow:
    """产品信息爬取和分析工作流"""

    def __init__(self, dimensions_config=None, login_timeout=300, model_name="qwen3.5-plus"):
        """
        初始化工作流

        Args:
            dimensions_config: 维度配置列表，默认使用洗碗机维度
            login_timeout: 登录等待超时时间（秒），默认 300 秒
            model_name: 模型名称
        """
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.products_dir = os.path.join(self.project_root, 'products_file')
        
        if not os.path.exists(self.products_dir):
            os.makedirs(self.products_dir)
            print(f'✅ 创建目录: {self.products_dir}')
        
        self.file_handler = FileHandler(base_path=self.products_dir)
        self.scraper = JdProductScraper(file_handler=self.file_handler)
        self.login_timeout = login_timeout

        if dimensions_config is None:
            dimension_mgr = DimensionManager()
            self.dimensions_config = dimension_mgr.get_dimensions_for_category('洗碗机')
        else:
            self.dimensions_config = dimensions_config
        
        self.workflow_mgr = WorkflowManager(
            dimensions_config=self.dimensions_config,
            model_name=model_name
        )
        
        self.images_csv_filename = 'all_product_images.csv'

    def step1_search_and_save_products(self, search_keyword, page=1, output_filename=None):
        """
        步骤1：搜索商品并保存SKUID到CSV（支持追加模式）

        Args:
            search_keyword: 搜索关键词
            page: 爬取页数
            output_filename: 输出文件名（只需文件名，不需要路径）

        Returns:
            filename: 保存的文件名
            products_count: 本次新增的商品数量
        """
        print("=" * 60)
        print(f"步骤1：搜索商品 '{search_keyword}' 并保存信息")
        print("=" * 60)

        products = self.scraper.search_jd_products(search_keyword, page, login_timeout=self.login_timeout)

        if output_filename:
            filename = output_filename
        else:
            filename = f'{search_keyword}.csv'

        print(f"\n✅ 步骤1完成！本次新增 {len(products)} 个商品，保存到 {os.path.join('products_file', filename)}")
        return filename, len(products)

    def step2_get_images_for_all_skuids(self, products_filename, skuid_column='sku'):
        """
        步骤2：从CSV读取所有SKUID并获取图片URL（统一存储，跳过已处理）

        Args:
            products_filename: 包含SKUID的CSV文件名
            skuid_column: SKUID列名

        Returns:
            skuid_image_map: {skuid: image_urls_list} 的映射字典
        """
        print("\n" + "=" * 60)
        print("步骤2：获取所有商品的图片URL")
        print("=" * 60)

        unprocessed_skus = self.file_handler.get_unprocessed_skus(
            products_filename, 
            self.images_csv_filename, 
            skuid_column
        )

        if not unprocessed_skus:
            print("✅ 所有商品均已处理，无需爬取图片")
            return {}

        skuid_image_map = {}

        for idx, skuid in enumerate(unprocessed_skus, 1):
            print(f"\n[{idx}/{len(unprocessed_skus)}] 正在获取 SKUID {skuid} 的图片...")
            try:
                img_urls, _ = self.scraper.get_jd_product_images(
                    skuid,
                    scroll_times=3,
                    save_to_csv=True,
                    csv_filename=self.images_csv_filename,
                    login_timeout=self.login_timeout
                )
                skuid_image_map[skuid] = img_urls
                print(f"✅ 获取到 {len(img_urls)} 张图片")

                # 增加等待时间，避免403错误
                if idx < len(unprocessed_skus):
                    wait_time = 5
                    print(f"⏳ 等待 {wait_time} 秒后继续...")
                    time.sleep(wait_time)

            except Exception as e:
                print(f"❌ 获取 SKUID {skuid} 的图片失败：{e}")
                skuid_image_map[skuid] = []
                
                # 失败后也等待，避免连续请求
                if idx < len(unprocessed_skus):
                    time.sleep(5)

        print(f"\n✅ 步骤2完成！共处理 {len(skuid_image_map)} 个新商品")
        print(f"所有图片URL已保存到：{os.path.join('products_file', self.images_csv_filename)}")
        return skuid_image_map

    def step3_and_4_analyze_and_save(self, products_filename, skuid_image_map):
        """
        步骤3 & 4：分析所有商品图片并将结果保存到CSV

        Args:
            products_filename: 原始产品CSV文件名
            skuid_image_map: SKUID到图片URL的映射
        
        Returns:
            bool: 是否成功完成所有分析
        """
        print("\n" + "=" * 60)
        print("步骤3 & 4：使用LLM分析图片并保存结果")
        print("=" * 60)

        products_filepath = os.path.join(self.products_dir, products_filename)
        
        success = self.workflow_mgr.batch_analyze_products(
            skuid_image_map=skuid_image_map,
            file_handler=self.file_handler,
            products_filepath=products_filepath,
            delay=3
        )
        
        if success:
            print(f"\n✅ 步骤3 & 4完成！所有结果已保存到 {os.path.join('products_file', products_filename)}")
        else:
            print(f"\n⚠️ 分析流程提前终止，部分结果已保存到 {os.path.join('products_file', products_filename)}")
        
        return success

    def run_full_workflow(self, search_keyword, page=1, output_filename=None):
        """
        运行完整工作流

        Args:
            search_keyword: 搜索关键词
            page: 爬取页数
            output_filename: 输出文件名
        """
        print("\n" + "🚀" * 30)
        print("开始执行完整的产品信息爬取和分析工作流")
        print("🚀" * 30 + "\n")

        products_filename, products_count = self.step1_search_and_save_products(
            search_keyword,
            page,
            output_filename
        )

        if products_count == 0:
            print("❌ 未找到任何商品，工作流终止")
            return

        skuid_image_map = self.step2_get_images_for_all_skuids(products_filename)

        if not skuid_image_map:
            print("❌ 未获取到任何图片URL，工作流终止")
            return

        success = self.step3_and_4_analyze_and_save(products_filename, skuid_image_map)

        if success:
            print("\n" + "✨" * 30)
            print("工作流全部完成！")
            print(f"最终结果文件：{os.path.join('products_file', products_filename)}")
            print("✨" * 30)
        else:
            print("\n" + "⚠️" * 30)
            print("工作流因API配额问题提前终止")
            print(f"部分结果已保存到：{os.path.join('products_file', products_filename)}")
            print("⚠️" * 30)


def main():
    """主函数"""
    workflow = ProductAnalysisWorkflow(
        login_timeout=300,
        model_name="qwen3.5-plus"
    )

    workflow.run_full_workflow(
        search_keyword="洗碗机",
        page=1,
        output_filename="洗碗机_分析结果.csv"
    )


if __name__ == '__main__':
    main()
