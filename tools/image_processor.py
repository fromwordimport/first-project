def image_url_to_base64(url, timeout=30):
    """
    将图片 URL 转换为带 MIME 类型的 base64 编码

    Args:
        url: 图片 URL
        timeout: 请求超时时间（秒），默认 30 秒

    Returns:
        base64 编码字符串，格式为 "data:{mime_type};base64,{data}"
    """
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()

    content_type = response.headers.get('content-type', 'image/jpeg')

    if 'png' in content_type:
        mime_type = 'image/png'
    elif 'gif' in content_type:
        mime_type = 'image/gif'
    else:
        mime_type = 'image/jpeg'

    base64_data = base64.b64encode(response.content).decode('utf-8')
    return f"data:{mime_type};base64,{base64_data}"


def batch_convert_urls_to_base64(urls, timeout=30):
    """
    批量将图片 URL 转换为 base64 编码

    Args:
        urls: 图片 URL 列表
        timeout: 单个请求超时时间（秒），默认 30 秒

    Returns:
        base64 编码列表
    """
    base64_images = []
    for i, url in enumerate(urls, 1):
        try:
            print(f'转换第 {i}/{len(urls)} 张图片...')
            base64_img = image_url_to_base64(url, timeout=timeout)
            base64_images.append(base64_img)
        except Exception as e:
            print(f'转换失败 {url}: {e}')
            base64_images.append(None)

    return base64_images