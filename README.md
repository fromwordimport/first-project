这是一个非常棒的项目，结合了爬虫、自动化和大模型技术。你提供的原始 Markdown 内容非常详尽，但在代码块的语法高亮、列表层级和部分排版上还有优化空间。

我为你重新梳理了格式，主要做了以下优化：
1.  **修复代码块**：为所有代码块添加了正确的语言标识（如 `python`, `bash`, `env`, `csv`），使其具有语法高亮。
2.  **统一缩进**：规范了列表项的缩进，使层级结构更清晰。
3.  **增强可读性**：对部分长段落和配置项进行了微调。

以下是优化后的 Markdown 文本：

```markdown
# ProductAndMarketing_Research

**京东商品爬取与智能分析系统 - 基于 LangChain 和 LLM 的产品信息提取工具**

---

## 📋 项目简介

本项目是一个自动化的京东商品信息爬取和分析系统，能够：

- 🕷️ **自动爬取**：京东商品列表和详情页图片
- 🖼️ **批量获取**：商品详情图片 URL
- 🤖 **智能识别**：使用 LLM（通义千问）智能识别图片中的产品参数
- 📊 **数据生成**：自动生成结构化的产品数据表格
- 🔄 **增量支持**：支持增量爬取和断点续传
- 🛡️ **异常处理**：自动处理登录、验证和页面异常

---

## ✨ 核心功能

### 1. 商品搜索与爬取
- 关键词搜索京东商品
- 自动翻页爬取多页数据
- SKUID 去重，避免重复采集
- 支持追加模式，累积历史数据

### 2. 图片批量获取
- 根据 SKU ID 批量获取商品详情页图片
- 自动滚动页面加载完整内容
- 统一存储到 `all_product_images.csv`
- 智能跳过已处理的 SKU

### 3. LLM 智能分析
- 基于品类自动选择分析维度（洗碗机、冰箱、洗衣机等）
- 使用 Tavily 动态查询新品类维度
- 结构化提取产品参数（颜色、尺寸、材质等）
- 支持自定义分析维度模板

### 4. 数据持久化
- 增量写入 CSV 文件
- 自动检测并跳过已处理商品
- 支持断点续传
- 文件存在性检查和自动创建

---

## 🏗️ 项目结构

```text
ProductAndMarketing_Research/
├── agent/
│   └── LLM_image_recogniton.py     # LLM 图像识别核心逻辑
├── tools/
│   ├── jd_scraper.py               # 京东爬虫核心类
│   ├── file_handler.py             # 文件操作统一管理
│   ├── dimension_manager.py        # 维度配置管理
│   ├── workflow_manager.py         # 工作流管理器
│   ├── image_processor.py          # 图片处理工具 
│   ├── path_tools.py               # 路径工具 
│   └── JDTools.py                 # 测试入口（可选） 
├── products_file/                  # 数据存储目录 
│   ├── all_product_images.csv      # 所有商品图片 URL 
│   ├── 洗碗机.csv                  # 商品基本信息 
│   └── 洗碗机_分析结果.csv         # LLM 分析结果 
├── prompts/ 
│   └── main_prompt                 # 提示词模板 
├── main.py                         # 主程序入口
├── pyproject.toml                  # 项目配置 
└── .env                            # 环境变量配置
```

---

## 🚀 快速开始

### 1. 环境要求
- Python 3.13+
- uv 包管理器（推荐）或 pip

### 2. 安装依赖

```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件并配置以下密钥：

```env
# 阿里云 DashScope API（通义千问）
DASHSCOPE_API_KEY=your_api_key_here
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# Tavily API（可选，用于动态查询维度）
TAVILY_API_KEY=your_tavily_api_key
```

**获取 API Key:**
- **DashScope**: [https://dashscope.console.aliyun.com/](https://dashscope.console.aliyun.com/)
- **Tavily**: [https://app.tavily.com/](https://app.tavily.com/)

### 4. 运行程序

```bash
python main.py
```

程序将自动执行以下步骤：
1.  搜索"洗碗机"商品并保存到 `products_file/洗碗机.csv`
2.  获取所有商品的图片 URL 到 `products_file/all_product_images.csv`
3.  使用 LLM 分析图片并提取产品参数
4.  保存分析结果到 `products_file/洗碗机_分析结果.csv`

---

## 📖 使用指南

### 修改搜索关键词
编辑 `main.py` 第 204-208 行：

```python
workflow.run_full_workflow(
    search_keyword="冰箱",      # 修改为你需要的品类
    page=1,                    # 爬取页数
    output_filename="冰箱_分析结果.csv"
)
```

### 自定义分析维度
编辑 `tools/dimension_manager.py`，在 `_load_builtin_templates` 中添加新品类：

```python
'空调': [
    {"name": "匹数", "description": "空调匹数", "type": str, "required": False}, 
    {"name": "能效等级", "description": "能效等级", "type": str, "required": False},
    # ... 更多维度 
]
```

### 单独运行各步骤

#### 步骤1: 仅爬取商品列表
```python
from tools.jd_scraper import JdProductScraper
from tools.file_handler import FileHandler
import os

products_dir = 'products_file'
file_handler = FileHandler(base_path=products_dir)
scraper = JdProductScraper(file_handler=file_handler)

products = scraper.search_jd_products('洗碗机', page=1)
print(f'获取到 {len(products)} 个商品')
```

#### 步骤2: 仅获取图片 URL
```python
# 从 CSV 读取 SKU
skuids = file_handler.read_skuids_from_csv('洗碗机.csv', skuid_column='sku')

# 批量获取图片
results = scraper.batch_get_product_images(
    skuids[:5],               # 前5个商品
    csv_filename='all_product_images.csv',
    delay=5                   # 每个商品间隔5秒
)
```

#### 步骤3: 仅进行 LLM 分析
```python
from agent.LLM_image_recogniton import initialize_model, create_dynamic_model
from tools.dimension_manager import DimensionManager

# 初始化模型
model = initialize_model(model_name="qwen3.5-plus")

# 获取维度配置
dimension_mgr = DimensionManager()
dimensions = dimension_mgr.get_dimensions_for_category('洗碗机')

# 创建动态模型
ProductDimensions = create_dynamic_model(dimensions)
```

---

## ⚙️ 高级配置

### 爬取速度控制
在 `main.py` 中调整等待时间：

```python
# step2_get_images_for_all_skuids 方法中
wait_time = 5 # 建议增加到 8-10 秒可避免 403 错误
time.sleep(wait_time)
```

### 登录超时设置
```python
workflow = ProductAnalysisWorkflow(
    login_timeout=300,          # 登录等待时间（秒）
    model_name="qwen3.5-plus"
)
```

### 模型切换
支持切换不同的通义千问模型：

```python
workflow = ProductAnalysisWorkflow(
    model_name="qwen-turbo"     # 更快的模型
)
```

---

## 🔧 技术栈

- **爬虫框架**: DrissionPage - 自动化浏览器控制
- **AI 框架**: LangChain - LLM 应用开发
- **大语言模型**: 阿里云通义千问 (Qwen)
- **图像处理**: requests + base64
- **数据处理**: CSV, Pydantic
- **包管理**: uv
- **搜索引擎**: Tavily API（可选）

---

## 📝 数据文件格式

### all_product_images.csv
```csv
sku,品类,序号,图片 URL
100130777668,洗碗机,1,https://img...
100130777668,洗碗机,2,https://img...
```

### 洗碗机.csv
```csv
标题,原价,最终价,历史价,销售店铺,店铺 ID,sku
XX品牌洗碗机,5999,4999,5999,XX旗舰店,10001,100130777668
```

### 洗碗机_分析结果.csv
```csv
标题,...,喷淋臂类型,喷淋臂数量,颜色,内胆材质,...
XX品牌洗碗机,...,双喷淋臂,2,白色,不锈钢,...
```

---

## ⚠️ 注意事项

1. **API 配额**：免费额度用尽后会停止分析，需开通付费服务。
2. **爬取频率**：默认 5 秒/SKU，过快可能触发 403 错误。
3. **登录验证**：首次运行需手动完成登录和安全验证。
4. **网络环境**：需要稳定的网络连接访问京东和 API 服务。
5. **浏览器依赖**：需要安装 Chrome/Chromium 浏览器。

---

## 🐛 常见问题

**Q: 出现 403 错误怎么办？**
> **A:** 增加 `main.py` 中的 `wait_time` 到 8-10 秒，降低爬取频率。

**Q: LLM 分析失败？**
> **A:** 检查 `.env` 中的 `DASHSCOPE_API_KEY` 是否正确配置，确认 API 配额充足。

**Q: 如何跳过已处理的商品？**
> **A:** 程序自动检测 `all_product_images.csv`，有图片 URL 的 SKU 会自动跳过。

**Q: 文件保存在哪里？**
> **A:** 所有数据文件保存在 `products_file/` 目录下。

**Q: 如何添加新品类？**
> **A:** 在 `tools/dimension_manager.py` 中添加品类模板，或使用 Tavily 自动查询。

---

## 📄 许可证

本项目仅供学习和研究使用。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
```
