import re

def to_https_url(input_str):
    """
    将输入字符串规范化为HTTPS URL格式
    
    参数:
    input_str (str): 输入字符串，可能是纯IP地址或HTTPS URL
    
    返回:
    str: 规范化的HTTPS URL，如果输入无效则返回原字符串
    """
    # 定义IP地址的正则表达式（0-255，四个部分）
    ip_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
    # 定义HTTPS URL的正则表达式
    https_pattern = r'^https?://'
    
    # 检查是否已经是HTTPS URL
    if re.match(https_pattern, input_str):
        return input_str
    
    # 检查是否是有效的IP地址
    match = re.match(ip_pattern, input_str)
    if match:
        # 验证每个部分是否在0-255范围内
        valid = True
        for group in match.groups():
            num = int(group)
            if num < 0 or num > 255:
                valid = False
                break
        
        if valid:
            return f'https://{input_str}'
    
    # 如果不是有效IP或HTTPS URL，返回原字符串
    return input_str

def is_https_url(input_str):
    """
    检查输入字符串是否为HTTPS URL格式
    
    参数:
    input_str (str): 输入字符串
    
    返回:
    bool: 如果是HTTPS URL则返回True，否则返回False
    """
    https_pattern = r'^https?://'
    return bool(re.match(https_pattern, input_str))

def is_ip_address(input_str):
    """
    检查输入字符串是否为有效的IPv4地址格式
    
    参数:
    input_str (str): 输入字符串
    
    返回:
    bool: 如果是有效IPv4地址则返回True，否则返回False
    """
    ip_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
    match = re.match(ip_pattern, input_str)
    if match:
        for group in match.groups():
            num = int(group)
            if num < 0 or num > 255:
                return False
        return True
    return False


def to_ipv4_address(input_str):
    """
    从字符串中提取 IPv4 地址（如 "https://192.168.1.1/" → "192.168.1.1"）
    参数：
        input_str (str): 输入字符串
    返回：
        str: 提取的 IPv4 地址字符串，若未找到则返回 None
    """
    ipv4_pattern = r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
    match = re.search(ipv4_pattern, input_str)
    return match.group(0) if match else None

def convert_policy_string_to_dict(input_str):
    """
    将策略配置字符串转换为字典
    支持格式示例：
        Policy.Policy.Mirroring.numberOfMirrors: 2
        Policy.Policy.rebuildPriority: 5

    参数:
        input_str (str): 多行配置字符串

    返回:
        dict: 转换后的字典，键为点分隔的路径，值为整数
    """
    result_dict = {}

    # 按行分割字符串并处理每行
    for line in input_str.split('\n'):
        # 跳过空行和注释
        if not line.strip() or line.strip().startswith('#'):
            continue

        # 分割键和值
        if ':' not in line:
            continue

        key, value = line.split(':', 1)  # 只分割第一个冒号

        # 清理键和值
        key = key.strip()
        value = value.strip()

        # 转换值为整数
        try:
            result_dict[key] = int(value)
        except (ValueError, TypeError):
            # 无法转换为整数时尝试处理其他类型
            try:
                result_dict[key] = float(value)
            except (ValueError, TypeError):
                # 无法转换时保留原始字符串
                result_dict[key] = value

    return result_dict


if __name__ == '__main__':
    ip = "https://192.168.1.1"
    print(to_ipv4_address(ip))  