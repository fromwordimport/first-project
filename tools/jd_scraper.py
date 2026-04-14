from DrissionPage import ChromiumPage, ChromiumOptions
from tools.file_handler import FileHandler
import os
import re
import time
import csv


class JdProductScraper:
    """京东商品爬虫类"""

    def __init__(self, file_handler=None, base_path=None):
        """
        初始化爬虫
        
        Args:
            file_handler: FileHandler 实例（可选）
            base_path: 基础路径，如果未提供 file_handler 则使用此路径创建
        """
        if file_handler:
            self.file_handler = file_handler
        else:
            project_root = base_path or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.file_handler = FileHandler(base_path=project_root)
        
        self.fieldnames = ['标题', '原价', '最终价', '历史价', '销售店铺', '店铺 ID', 'sku']

    def _get_browser_options(self):
        """
        获取浏览器配置选项

        Returns:
            co: ChromiumOptions 对象
        """
        return ChromiumOptions()

    def wait_for_login(self, dp, timeout=300):
        """
        检测并等待用户完成登录

        Args:
            dp: ChromiumPage 页面对象
            timeout: 最大等待时间（秒），默认 300 秒（5分钟）

        Returns:
            bool: 登录成功返回 True，超时返回 False
        """
        print('\n⚠️  检测到需要登录')
        print('请在浏览器中完成登录操作...')

        start_time = time.time()
        check_interval = 2

        while time.time() - start_time < timeout:
            current_url = dp.url

            if 'passport.jd.com' not in current_url and 'login.aspx' not in current_url:
                print('✅ 登录成功！')
                dp.wait(2)
                return True

            elapsed = int(time.time() - start_time)
            remaining = timeout - elapsed
            print(f'⏳ 等待登录中... (已等待 {elapsed} 秒，剩余 {remaining} 秒)', end='\r')

            time.sleep(check_interval)

        print('\n❌ 登录超时！请检查网络连接或手动登录后重试')
        return False

    def wait_for_risk_verification(self, dp, timeout=600):
        """
        检测并等待用户完成风险验证

        Args:
            dp: ChromiumPage 页面对象
            timeout: 最大等待时间（秒），默认 600 秒（10分钟）

        Returns:
            bool: 验证成功返回 True，超时返回 False
        """
        print('\n⚠️  检测到需要安全验证')
        print('请在浏览器中完成验证操作（滑块验证/短信验证等）...')

        start_time = time.time()
        check_interval = 2

        while time.time() - start_time < timeout:
            current_url = dp.url

            if 'cfe.m.jd.com/privatedomain/risk_handler' not in current_url:
                print('✅ 验证成功！')
                dp.wait(2)
                return True

            elapsed = int(time.time() - start_time)
            remaining = timeout - elapsed
            print(f'⏳ 等待验证中... (已等待 {elapsed} 秒，剩余 {remaining} 秒)', end='\r')

            time.sleep(check_interval)

        print('\n❌ 验证超时！请检查网络连接或手动验证后重试')
        return False

    def wait_for_page_recovery(self, dp, expected_url_pattern='https://item.jd.com/', timeout=120):
        """
        等待页面恢复到正常状态（监听到目标URL模式）
        
        Args:
            dp: ChromiumPage 页面对象
            expected_url_pattern: 期望的URL模式，默认为商品详情页
            timeout: 最大等待时间（秒），默认 120 秒
        
        Returns:
            bool: 页面恢复返回 True，超时返回 False
        """
        print(f'\n⚠️  检测到异常中断，等待页面恢复...')
        print(f'   期望恢复至: {expected_url_pattern}')
        
        start_time = time.time()
        check_interval = 1
        
        while time.time() - start_time < timeout:
            current_url = dp.url
            
            # 检查是否恢复到目标页面
            if expected_url_pattern in current_url:
                print(f'✅ 页面已恢复正常: {current_url[:80]}...')
                dp.wait(2)
                return True
            
            # 检查是否需要登录或验证
            if 'passport.jd.com' in current_url or 'login.aspx' in current_url:
                print('🔐 检测到登录页面，请先完成登录')
                if not self.wait_for_login(dp, timeout - int(time.time() - start_time)):
                    return False
                continue
            
            if 'aq.jd.com' in current_url or 'cfe.m.jd.com/privatedomain/risk_handler' in current_url:
                print('🛡️  检测到安全验证，请完成验证')
                if not self.wait_for_risk_verification(dp, timeout - int(time.time() - start_time)):
                    return False
                continue
            
            elapsed = int(time.time() - start_time)
            remaining = timeout - elapsed
            print(f'⏳ 等待页面恢复... (当前: {current_url[:60]}, 已等待 {elapsed} 秒)', end='\r')
            
            time.sleep(check_interval)
        
        print(f'\n❌ 页面恢复超时！当前URL: {dp.url}')
        return False

    def check_and_handle_security(self, dp, login_timeout=300):
        """
        检查当前页面是否需要登录或安全验证，如果是则等待完成
        
        Args:
            dp: ChromiumPage 页面对象
            login_timeout: 登录/验证最大等待时间（秒）
        
        Returns:
            bool: 如果需要登录/验证且成功返回 True，不需要也返回 True，失败返回 False
        """
        current_url = dp.url
        
        # 检测登录页面
        if 'passport.jd.com' in current_url or 'login.aspx' in current_url:
            return self.wait_for_login(dp, login_timeout)
        
        # 检测安全验证页面
        if 'aq.jd.com' in current_url or 'cfe.m.jd.com/privatedomain/risk_handler' in current_url:
            return self.wait_for_risk_verification(dp, login_timeout * 2)
        
        # 不需要登录或验证
        return True

    def scroll_page(self, dp, scroll_times=3, scroll_ratio=0.5):
        """
        控制页面滚动

        Args:
            dp: ChromiumPage 页面对象
            scroll_times: 页面翻动次数，None 表示只滚动一次，0 表示直接滚动到底部
            scroll_ratio: 单次滚动时的比例（0-1），默认 0.5 表示滚动到一半
        """
        if scroll_times is None:
            dp.run_js(f'window.scrollTo(0, document.body.scrollHeight * {scroll_ratio})')
        elif scroll_times == 0:
            dp.run_js('window.scrollTo(0, document.body.scrollHeight)')
        else:
            total_height = dp.run_js('return document.body.scrollHeight')
            step_height = total_height / (scroll_times + 1)

            print(f'开始翻动页面，共翻动 {scroll_times} 次，每次滚动 {step_height:.2f}px')

            for i in range(1, scroll_times + 1):
                scroll_position = int(step_height * i)
                dp.run_js(f'window.scrollTo(0, {scroll_position})')
                print(f'第 {i} 次翻动：滚动到 {scroll_position}px')
                dp.wait(1.5)
                dp.listen.wait_silent(timeout=2, targets_only=True)

            dp.run_js('window.scrollTo(0, document.body.scrollHeight)')
            print('已滚动到底部')

    def get_jd_product_images(self, skuid, scroll_ratio=0.5, step=1, timeout=3,
                              save_to_csv=False, csv_filename=None,
                              scroll_times=3, category=None, login_timeout=300):
        """
        获取京东商品详情页图片 URL

        Args:
            skuid: 商品 SKU ID
            scroll_ratio: 页面滚动比例（0-1）
            step: steps() 方法的步长参数
            timeout: steps() 方法监听超时时间（秒）
            save_to_csv: 是否保存到 CSV 文件
            csv_filename: CSV 文件名（由调用方通过 file_handler 管理路径）
            scroll_times: 页面翻动次数
            category: 商品品类（可选）
            login_timeout: 登录等待超时时间（秒），默认 300 秒

        Returns:
            图片 URL 列表，如果保存则返回 (img_urls, filename) 元组
        """
        co = self._get_browser_options()
        dp = ChromiumPage(addr_or_opts=co)

        try:
            dp.listen.start('https://api.m.jd.com/?functionId=pc_item_getWareGraphic&body=%7B%22skuId%22:')

            dp.get(f'https://item.jd.com/{skuid}.html')
            dp.wait(2)

            # 检查并处理登录和安全验证
            if not self.check_and_handle_security(dp, login_timeout):
                print('❌ 登录或验证失败，无法获取商品图片')
                return [] if not save_to_csv else ([], csv_filename)

            # 等待页面完全加载到商品详情页
            if not self.wait_for_page_recovery(dp, 'https://item.jd.com/', timeout=60):
                print('❌ 页面未恢复到商品详情页，跳过此商品')
                return [] if not save_to_csv else ([], csv_filename)

            self.scroll_page(dp, scroll_times, scroll_ratio)

            dp.listen.wait_silent(timeout=3, targets_only=True)
            resp = list(dp.listen.steps(gap=step, timeout=timeout))
            
            img_urls = []
            for packet in resp:
                body = packet.response.body
                
                if not isinstance(body, dict):
                    continue
                    
                graphicContent = body.get("data", {}).get("graphicContent")
                
                if not graphicContent:
                    continue
                
                if 'background-image:url(' in graphicContent:
                    pattern = r'background-image:\s*url\(([^)]+)\)'
                    urls = re.findall(pattern, graphicContent)
                    for url in urls:
                        clean_url = url.strip()
                        if not clean_url.startswith('http'):
                            clean_url = f"https:{clean_url}"
                        img_urls.append(clean_url)

                elif 'data-lazyload=' in graphicContent:
                    pattern = r'data-lazyload="([^"]+)"'
                    urls = re.findall(pattern, graphicContent)
                    for url in urls:
                        clean_url = url.strip()
                        if not clean_url.startswith('http'):
                            clean_url = f"https:{clean_url}"
                        img_urls.append(clean_url)

            print(img_urls)
            print(f'共获取到了{len(img_urls)}张图片的 url')

            if save_to_csv:
                self.file_handler.append_product_images_to_csv(skuid, img_urls, csv_filename, category)
                return img_urls, csv_filename

            return img_urls
        finally:
            dp.quit()

    def batch_get_product_images(self, skuids, scroll_ratio=0.5, step=1, timeout=3,
                                 csv_filename='all_product_images.csv', scroll_times=3,
                                 category=None, login_timeout=300, delay=5):
        """
        批量获取多个商品的图片 URL 并保存到统一文件

        Args:
            skuids: SKU ID 列表
            scroll_ratio: 页面滚动比例
            step: steps() 步长参数
            timeout: 监听超时时间
            csv_filename: CSV 文件名
            scroll_times: 页面翻动次数
            category: 商品品类（可选，所有商品使用同一种品类）
            login_timeout: 登录等待超时时间（秒），默认 300 秒
            delay: 每个商品之间的延迟时间（秒），默认 5 秒

        Returns:
            results: 字典，key 为 skuid，value 为图片 URL 列表
        """
        results = {}

        for i, skuid in enumerate(skuids, 1):
            print(f'\n正在处理第 {i}/{len(skuids)} 个商品 (SKU: {skuid})...')
            try:
                img_urls = self.get_jd_product_images(
                    skuid=skuid,
                    scroll_ratio=scroll_ratio,
                    step=step,
                    timeout=timeout,
                    save_to_csv=True,
                    csv_filename=csv_filename,
                    scroll_times=scroll_times,
                    category=category,
                    login_timeout=login_timeout
                )
                results[skuid] = img_urls
                
                # 如果不是最后一个，等待指定时间
                if i < len(skuids):
                    print(f'⏳ 等待 {delay} 秒后继续...')
                    time.sleep(delay)
            except Exception as e:
                print(f'商品 {skuid} 处理失败：{e}')
                results[skuid] = []
                
                # 失败后也等待
                if i < len(skuids):
                    time.sleep(delay)

        print(f'\n批量处理完成！共处理 {len(skuids)} 个商品')
        print(f'所有图片 URL 已保存到：{csv_filename}')

        return results

    def search_jd_products(self, search_product, page=1, login_timeout=300, skip_processed=True):
        """
        搜索京东商品并导出数据到 CSV（支持追加模式、去重和跳过已处理）

        Args:
            search_product: 搜索关键词
            page: 爬取页数
            login_timeout: 登录等待超时时间（秒），默认 300 秒
            skip_processed: 是否跳过已处理的SKU（在all_product_images.csv中有图片的）

        Returns:
            products: 新增的商品列表数据（不包含已存在的）
        """
        self.file_handler.filename, self.file_handler.f, self.file_handler.csv_write = \
            self.file_handler.init_csv_file(search_product, self.fieldnames)

        products = []
        dp = None

        try:
            co = self._get_browser_options()
            dp = ChromiumPage(addr_or_opts=co)
            dp.listen.start('https://api.m.jd.com/api?appid=search-pc-java&t')
            dp.get(f'https://search.jd.com/Search?keyword={search_product}&enc=utf-8')
            dp.wait(2)

            # 检查并处理登录和安全验证
            if not self.check_and_handle_security(dp, login_timeout):
                print('❌ 登录或验证失败，无法搜索商品')
                return []

            # 等待页面恢复到搜索结果页
            if not self.wait_for_page_recovery(dp, 'https://search.jd.com/Search', timeout=60):
                print('❌ 页面未恢复到搜索结果页，终止爬取')
                return []

            existing_skus = set()
            filepath = self.file_handler.filename
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        sku = row.get('sku', '').strip()
                        if sku:
                            existing_skus.add(sku)
                print(f'🔍 检测到已有 {len(existing_skus)} 个商品记录，将跳过重复项')

            processed_skus = set()
            if skip_processed:
                images_csv = 'all_product_images.csv'
                images_path = self.file_handler._get_full_path(images_csv)
                if os.path.exists(images_path):
                    with open(images_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            sku = row.get('sku', '').strip()
                            img_url = row.get('图片 URL', '').strip()
                            if sku and img_url:
                                processed_skus.add(sku)
                    print(f'✅ 检测到 {len(processed_skus)} 个已处理SKU（有图片），将跳过')

            for page_num in range(page):
                print(f'\n正在爬取第 {page_num + 1} 页...')
                
                # 每页开始前检查页面状态
                if not self.wait_for_page_recovery(dp, 'https://search.jd.com/Search', timeout=30):
                    print('⚠️  页面未恢复，尝试重新加载...')
                    dp.get(f'https://search.jd.com/Search?keyword={search_product}&enc=utf-8&page={page_num * 2 + 1}')
                    dp.wait(3)
                    if not self.check_and_handle_security(dp, login_timeout):
                        print('❌ 重新加载后仍需登录/验证，终止爬取')
                        break
                
                dp.wait.ele_displayed('.search-condition', timeout=5)
                self.scroll_page(dp, scroll_times=0)
                dp.wait.ele_displayed('._wrapper_1v6qy_3 plugin_goodsCardWrapper _row_6_1v6qy_13', timeout=5)

                dp.listen.wait_silent(timeout=3, targets_only=True)
                resps = list(dp.listen.steps(gap=1, timeout=5))

                page_products = self.parse_products(resps, existing_skus, processed_skus if skip_processed else None)
                new_count = len(page_products)
                products.extend(page_products)
                
                for p in page_products:
                    existing_skus.add(p['sku'])
                
                print(f'第 {page_num + 1} 页获取 {new_count} 个新商品')

                if page_num < page - 1:
                    try:
                        dp.ele('css:._pagination_next_1jczn_8').click()
                        dp.wait.load_start()
                        
                        # 翻页后检查页面状态
                        if not self.wait_for_page_recovery(dp, 'https://search.jd.com/Search', timeout=30):
                            print('⚠️  翻页后页面异常，尝试重新检查...')
                            if not self.check_and_handle_security(dp, login_timeout):
                                print('❌ 翻页后需要重新登录或验证，终止爬取')
                                break
                    except Exception as e:
                        print(f'无法翻页：{e}')
                        break

            print(f'\n本次共获取 {len(products)} 个新商品')
            return products
        finally:
            self.file_handler.close_file()
            if dp:
                dp.quit()

    def parse_products(self, resps, existing_skus=None, processed_skus=None):
        """
        解析商品数据包并写入 CSV（支持去重和跳过已处理）

        Args:
            resps: 数据包列表
            existing_skus: 已存在于商品CSV的SKU集合，用于去重
            processed_skus: 已处理（有图片）的SKU集合，用于跳过

        Returns:
            products: 解析后的新商品列表
        """
        products = []

        for resp in resps:
            json_data = resp.response.body

            if not isinstance(json_data, dict) or 'abBuriedTagMap' not in json_data:
                continue

            wareList = json_data.get('data', {}).get('wareList', [])

            for item in wareList:
                product = self.extract_product_info(item)
                if product:
                    sku = product['sku']
                    
                    if existing_skus and sku in existing_skus:
                        continue
                    
                    if processed_skus and sku in processed_skus:
                        print(f'⏭️  跳过已处理 SKU: {sku}')
                        continue
                    
                    self.file_handler.write_products_to_csv(self.file_handler.csv_write, [product])
                    products.append(product)

        return products

    def extract_product_info(self, item):
        """
        从单个商品项中提取信息

        Args:
            item: 商品数据字典

        Returns:
            product: 商品信息字典，如果无效则返回 None
        """
        title = item.get('wareName', '')
        title = title.replace('<font class=\"skcolor_ljg\">', '').replace('</font>', '')

        if len(title) <= 1:
            return None

        final_price = item.get('finalPrice')
        estimated_price = final_price.get('estimatedPrice') if final_price else None

        return {
            '标题': title,
            '原价': item.get('jdPrice', ''),
            '最终价': estimated_price if estimated_price else item.get('jdPrice', ''),
            '历史价': item.get('oriPrice', ''),
            '销售店铺': item.get('shopName', ''),
            '店铺 ID': item.get('shopId', ''),
            'sku': item.get('skuId', ''),
        }


if __name__ == '__main__':
    from DrissionPage import ChromiumPage

    scraper = JdProductScraper()
    scraper.get_jd_product_images(100130777668)

