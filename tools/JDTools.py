from tools.jd_scraper import JdProductScraper
from tools.image_processor import image_url_to_base64, batch_convert_urls_to_base64

__all__ = ['JdProductScraper', 'image_url_to_base64', 'batch_convert_urls_to_base64']


if __name__ == '__main__':
    from tools.file_handler import FileHandler
    import os
    
    print('=' * 60)
    print('京东商品爬虫测试')
    print('=' * 60)
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    products_dir = os.path.join(project_root, 'products_file')
    
    if not os.path.exists(products_dir):
        os.makedirs(products_dir)
    
    file_handler = FileHandler(base_path=products_dir)
    scraper = JdProductScraper(file_handler=file_handler)
    
    print('\n【测试1】搜索商品')
    print('-' * 60)
    products = scraper.search_jd_products('洗碗机', page=1)
    print(f'获取到 {len(products)} 个商品')
    if products:
        print(f'示例商品：{products[0]["标题"]}')
    
    print('\n【测试2】获取单个商品图片')
    print('-' * 60)
    if products:
        test_skuid = products[0]['sku']
        print(f'测试 SKU: {test_skuid}')
        img_urls, saved_file = scraper.get_jd_product_images(
            test_skuid,
            save_to_csv=True,
            csv_filename='all_product_images.csv',
            scroll_times=3
        )
        print(f'获取到 {len(img_urls)} 张图片')
        print(f'保存到文件: {saved_file}')
    else:
        print('跳过：未获取到商品数据')
    
    print('\n【测试3】批量获取商品图片')
    print('-' * 60)
    skuids = scraper.file_handler.read_skuids_from_csv('洗碗机.csv', skuid_column='sku')
    if skuids:
        print(f'从 CSV 读取到 {len(skuids)} 个 SKU')
        batch_results = scraper.batch_get_product_images(
            skuids[:2],
            csv_filename='all_product_images.csv',
            scroll_times=3
        )
        for skuid, urls in batch_results.items():
            print(f'  SKU {skuid}: {len(urls)} 张图片')
    else:
        print('跳过：未找到洗碗机.csv 文件或文件中无数据')
    
    print('\n【测试4】从统一文件读取图片数据')
    print('-' * 60)
    try:
        all_products_images = scraper.file_handler.load_product_images_from_csv('all_product_images.csv')
        if all_products_images:
            print(f'共读取到 {len(all_products_images)} 个商品的图片数据')
            for skuid, urls in list(all_products_images.items())[:3]:
                print(f'  SKU {skuid}: {len(urls)} 张图片')
        else:
            print('未找到图片数据文件')
    except FileNotFoundError:
        print('跳过：all_product_images.csv 文件不存在')
    
    print('\n【测试5】图片 URL 转 base64')
    print('-' * 60)
    try:
        all_products_images = scraper.file_handler.load_product_images_from_csv('all_product_images.csv')
        if all_products_images:
            first_skuid = list(all_products_images.keys())[0]
            first_url = all_products_images[first_skuid][0]
            print(f'转换图片: {first_url[:50]}...')
            base64_str = image_url_to_base64(first_url)
            print(f'转换成功，base64 长度: {len(base64_str)} 字符')
        else:
            print('跳过：无可用图片数据')
    except Exception as e:
        print(f'跳过：{e}')
    
    print('\n' + '=' * 60)
    print('测试完成')
    print('=' * 60)

