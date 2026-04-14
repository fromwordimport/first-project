import csv
import os


class DictWithAttributes(dict):
    """支持自定义属性的字典类"""
    pass


class FileHandler:
    def __init__(self, base_path=None):
        self.base_path = base_path or os.getcwd()
        self.f = None
        self.csv_writer = None

    def _get_full_path(self, filename):
        return os.path.join(self.base_path, filename)

    def init_csv_file(self, search_product, fieldnames):
        filename = f'{search_product}.csv'
        full_path = self._get_full_path(filename)
        
        file_exists = os.path.exists(full_path)
        
        if file_exists:
            file_handle = open(full_path, 'a', encoding='utf-8', newline='')
            csv_writer = csv.DictWriter(file_handle, fieldnames=fieldnames)
            print(f'📂 检测到已存在文件 {filename}，将追加写入')
        else:
            file_handle = open(full_path, 'w', encoding='utf-8', newline='')
            csv_writer = csv.DictWriter(file_handle, fieldnames=fieldnames)
            csv_writer.writeheader()
            print(f'🆕 创建新文件 {filename}')

        return full_path, file_handle, csv_writer

    def write_products_to_csv(self, csv_writer, products):
        for product in products:
            csv_writer.writerow(product)

    def save_image_urls_to_csv(self, skuid, img_urls, filename=None):
        if filename is None:
            filename = f'images_{skuid}.csv'
        
        full_path = self._get_full_path(filename)

        with open(full_path, 'w', encoding='utf-8', newline='') as f:
            csv_writer = csv.DictWriter(f, fieldnames=['序号', '图片 URL'])
            csv_writer.writeheader()

            for idx, img_url in enumerate(img_urls, start=1):
                csv_writer.writerow({'序号': idx, '图片 URL': img_url})

        print(f'图片 URL 已保存到 {full_path}')
        return full_path

    def load_image_urls_from_csv(self, filename):
        full_path = self._get_full_path(filename)
        img_urls = []

        with open(full_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            # 按序号排序后读取（确保顺序正确）
            rows = sorted(csv_reader, key=lambda x: int(x['序号']))
            for row in rows:
                img_urls.append(row['图片 URL'])

        print(f'从 {full_path} 读取了 {len(img_urls)} 个图片 URL')
        return img_urls

    def save_multiple_products_images_to_csv(self, products_images_data, filename='all_product_images.csv'):
        full_path = self._get_full_path(filename)
        
        with open(full_path, 'w', encoding='utf-8', newline='') as f:
            csv_writer = csv.DictWriter(f, fieldnames=['sku', '序号', '图片 URL'])
            csv_writer.writeheader()

            total_count = 0
            for product_data in products_images_data:
                skuid = product_data['sku']
                img_urls = product_data['img_urls']

                for idx, img_url in enumerate(img_urls, start=1):
                    csv_writer.writerow({
                        'sku': skuid,
                        '序号': idx,
                        '图片 URL': img_url
                    })
                    total_count += 1

        print(f'共 {len(products_images_data)} 个商品的图片 URL 已保存到 {full_path}')
        print(f'总计 {total_count} 张图片')
        return full_path

    def load_product_images_from_csv(self, filename='all_product_images.csv'):
        """
        从 CSV 文件中加载商品图片 URL（按 SKU 分组）

        Args:
            filename: CSV 文件名

        Returns:
            products_images: 字典，key 为 SKU，value 为图片 URL 列表
        """
        full_path = self._get_full_path(filename)

        if not os.path.exists(full_path):
            print(f'文件 {full_path} 不存在')
            return {}

        # 使用支持属性的字典类
        products_images = DictWithAttributes()
        products_categories = {}

        with open(full_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                skuid = row.get('sku', '').strip()
                img_url = row.get('图片 URL', '').strip()
                category = row.get('品类', '').strip()

                if not skuid or not img_url:
                    continue

                # 保存品类信息
                if category:
                    products_categories[skuid] = category

                # 如果该 SKU 还不存在，创建空列表
                if skuid not in products_images:
                    products_images[skuid] = []

                # 获取当前 SKU 的图片列表
                url_list = products_images[skuid]
                
                # 检查是否已存在相同的 URL
                if img_url not in url_list:
                    url_list.append(img_url)

        # 将品类信息附加到返回结果中
        if products_categories:
            print(f'从 {full_path} 读取了 {len(products_images)} 个商品的图片 URL')
            print(f'其中 {len(products_categories)} 个商品有品类信息')
            # 在返回的字典中添加元数据
            products_images._categories = products_categories
        else:
            print(f'从 {full_path} 读取了 {len(products_images)} 个商品的图片 URL')
        
        return products_images

    def append_product_images_to_csv(self, skuid, img_urls, filename='all_product_images.csv', category=None):
        """
        追加单个商品的图片 URL 到现有 CSV 文件

        Args:
            skuid: 商品 SKU ID
            img_urls: 图片 URL 列表
            filename: CSV 文件名
            category: 商品品类（可选）

        Returns:
            None
        """
        full_path = self._get_full_path(filename)

        # 如果文件不存在，创建新文件（包含品类字段）
        if not os.path.exists(full_path):
            with open(full_path, 'w', encoding='utf-8', newline='') as f:
                csv_writer = csv.DictWriter(f, fieldnames=['sku', '品类', '序号', '图片 URL'])
                csv_writer.writeheader()

        # 读取现有数据，检查该 SKU 是否已存在
        existing_data = []
        sku_exists = False
        max_seq = 0
        
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                csv_reader = csv.DictReader(f)
                for row in csv_reader:
                    if row.get('sku', '').strip() == skuid:
                        sku_exists = True
                        try:
                            seq = int(row.get('序号', 0))
                            max_seq = max(max_seq, seq)
                        except ValueError:
                            pass
                    existing_data.append(row)
        
        # 如果 SKU 已存在，先删除旧数据
        if sku_exists:
            existing_data = [row for row in existing_data if row.get('sku', '').strip() != skuid]
            # 重写文件
            with open(full_path, 'w', encoding='utf-8', newline='') as f:
                csv_writer = csv.DictWriter(f, fieldnames=['sku', '品类', '序号', '图片 URL'])
                csv_writer.writeheader()
                csv_writer.writerows(existing_data)
        
        # 追加新数据（序号从1开始连续）
        with open(full_path, 'a', encoding='utf-8', newline='') as f:
            csv_writer = csv.DictWriter(f, fieldnames=['sku', '品类', '序号', '图片 URL'])
            for idx, img_url in enumerate(img_urls, start=1):
                csv_writer.writerow({
                    'sku': skuid,
                    '品类': category if category else '',
                    '序号': idx,
                    '图片 URL': img_url
                })

        print(f'SKUID {skuid} 的 {len(img_urls)} 张图片 URL 已追加到 {full_path}' + 
              (f' (品类: {category})' if category else ''))

    def get_product_category(self, skuid, filename='all_product_images.csv'):
        """
        获取指定 SKU 的品类信息
        
        Args:
            skuid: 商品 SKU ID
            filename: CSV 文件名
            
        Returns:
            category: 品类名称，如果未找到则返回 None
        """
        full_path = self._get_full_path(filename)
        
        if not os.path.exists(full_path):
            return None
        
        with open(full_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                if row.get('sku', '').strip() == skuid:
                    category = row.get('品类', '').strip()
                    return category if category else None
        
        return None
    
    def update_product_category(self, skuid, category, filename='all_product_images.csv'):
        """
        更新指定 SKU 的品类信息
        
        Args:
            skuid: 商品 SKU ID
            category: 品类名称
            filename: CSV 文件名
        """
        full_path = self._get_full_path(filename)
        
        if not os.path.exists(full_path):
            print(f'文件 {full_path} 不存在')
            return
        
        import tempfile
        import shutil
        
        temp_filename = full_path + '.tmp'
        updated = False
        
        with open(full_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            fieldnames = csv_reader.fieldnames
            
            # 确保有品类字段
            if '品类' not in fieldnames:
                fieldnames = list(fieldnames) + ['品类']
            
            rows = []
            for row in csv_reader:
                if row.get('sku', '').strip() == skuid:
                    row['品类'] = category
                    updated = True
                rows.append(row)
        
        with open(temp_filename, 'w', encoding='utf-8', newline='') as f:
            csv_writer = csv.DictWriter(f, fieldnames=fieldnames)
            csv_writer.writeheader()
            csv_writer.writerows(rows)
        
        shutil.move(temp_filename, full_path)
        
        if updated:
            print(f'✅ 已更新 SKU {skuid} 的品类为: {category}')
        else:
            print(f'⚠️  未找到 SKU {skuid}')

    def close_file(self):
        """关闭文件句柄"""
        if self.f:
            self.f.close()
            self.f = None

    def read_skuids_from_csv(self, filename, skuid_column='sku'):
        """
        从 CSV 文件中读取 SKUID 列表

        Args:
            filename: CSV 文件名
            skuid_column: SKUID 列名，默认为 'sku'

        Returns:
            skuids: SKUID 列表
        """
        full_path = self._get_full_path(filename)
        skuids = []

        with open(full_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                skuid = row.get(skuid_column, '').strip()
                if skuid:
                    skuids.append(skuid)

        print(f'从 {full_path} 读取了 {len(skuids)} 个 SKUID')
        return skuids

    def check_sku_processed_status(self, skuid, images_csv_filename='all_product_images.csv'):
        """
        检查指定 SKU 是否已在图片文件中处理过
        
        Args:
            skuid: 商品 SKU ID
            images_csv_filename: 图片 CSV 文件名
            
        Returns:
            bool: True 表示已处理（有图片URL），False 表示未处理
        """
        full_path = self._get_full_path(images_csv_filename)
        
        if not os.path.exists(full_path):
            return False
        
        with open(full_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                if row.get('sku', '').strip() == skuid:
                    img_url = row.get('图片 URL', '').strip()
                    if img_url:
                        return True
        
        return False

    def get_unprocessed_skus(self, products_csv_filename, images_csv_filename='all_product_images.csv', skuid_column='sku'):
        """
        获取尚未处理的 SKU 列表（在商品CSV中存在但在图片CSV中无记录或无URL）
        
        Args:
            products_csv_filename: 商品 CSV 文件名
            images_csv_filename: 图片 CSV 文件名
            skuid_column: SKU 列名
            
        Returns:
            unprocessed_skus: 未处理的 SKU 列表
        """
        products_path = self._get_full_path(products_csv_filename)
        images_path = self._get_full_path(images_csv_filename)
        
        if not os.path.exists(products_path):
            print(f'⚠️  商品文件不存在: {products_path}')
            return []
        
        all_skus = set()
        with open(products_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                skuid = row.get(skuid_column, '').strip()
                if skuid:
                    all_skus.add(skuid)
        
        if not os.path.exists(images_path):
            print(f'ℹ️  图片文件不存在，所有 {len(all_skus)} 个 SKU 均未处理')
            return list(all_skus)
        
        processed_skus = set()
        with open(images_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                skuid = row.get('sku', '').strip()
                img_url = row.get('图片 URL', '').strip()
                if skuid and img_url:
                    processed_skus.add(skuid)
        
        unprocessed_skus = list(all_skus - processed_skus)
        
        print(f'📊 统计信息:')
        print(f'   总 SKU 数: {len(all_skus)}')
        print(f'   已处理: {len(processed_skus)}')
        print(f'   未处理: {len(unprocessed_skus)}')
        
        return unprocessed_skus

    def update_csv_with_llm_results(self, filename, skuid, llm_results, fieldnames=None):
        """
        将 LLM 分析结果更新到 CSV 文件中对应的 SKUID 行

        Args:
            filename: CSV 文件名
            skuid: 商品 SKU ID
            llm_results: LLM 分析结果字典
            fieldnames: 需要更新的字段名列表，如果为 None 则使用 llm_results 的所有键
        """
        import tempfile
        import shutil

        if not fieldnames:
            fieldnames = list(llm_results.keys())

        full_path = self._get_full_path(filename)
        
        # 创建临时文件
        temp_filename = full_path + '.tmp'

        # 读取原始 CSV
        rows = []
        with open(full_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            original_fieldnames = csv_reader.fieldnames.copy()

            # 检查是否需要添加新字段
            new_fieldnames = [field for field in fieldnames if field not in original_fieldnames]
            all_fieldnames = original_fieldnames + new_fieldnames

            for row in csv_reader:
                # 找到对应的 SKUID 行并更新
                if row.get('sku') == skuid:
                    row.update(llm_results)
                rows.append(row)

        # 写入更新后的数据（包括新字段）
        with open(temp_filename, 'w', encoding='utf-8', newline='') as f:
            csv_writer = csv.DictWriter(f, fieldnames=all_fieldnames)
            csv_writer.writeheader()
            csv_writer.writerows(rows)

        # 替换原文件
        shutil.move(temp_filename, full_path)
        print(f'已更新 SKUID {skuid} 的 LLM 分析结果到 {full_path}')
