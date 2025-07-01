import requests
import time
import json
import re
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from colorama import Fore, Style, init

# 初始化colorama
init(autoreset=True)

def load_recaptcha_site_key() -> str:
    """从配置文件加载reCAPTCHA站点密钥"""
    try:
        config_path = 'config/recaptcha_config.txt'
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        print(f"{Fore.GREEN}成功从配置文件加载reCAPTCHA站点密钥: {line}")
                        return line
        # 如果配置文件不存在或读取失败，使用默认值
        default_key = "6LcPKnMrAAAAAEa2Zhf-5iVAWsWPobIO4QTnEUXp"
        print(f"{Fore.YELLOW}使用默认reCAPTCHA站点密钥: {default_key}")
        return default_key
    except Exception as e:
        print(f"{Fore.RED}读取reCAPTCHA配置文件时发生错误: {str(e)}")
        default_key = "6LcPKnMrAAAAAEa2Zhf-5iVAWsWPobIO4QTnEUXp"
        print(f"{Fore.YELLOW}使用默认reCAPTCHA站点密钥: {default_key}")
        return default_key

# 加载reCAPTCHA站点密钥
RECAPTCHA_SITE_KEY = load_recaptcha_site_key()

class WalletStatusManager:
    """钱包状态管理器"""
    
    def __init__(self, status_file: str = 'config/wallet_status.json'):
        self.status_file = status_file
        self.status_data = self.load_status()
    
    def load_status(self) -> Dict[str, Any]:
        """加载钱包状态"""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"{Fore.GREEN}成功加载钱包状态文件: {self.status_file}")
                    return data
            else:
                print(f"{Fore.YELLOW}钱包状态文件不存在，将创建新文件")
                return {}
        except Exception as e:
            print(f"{Fore.RED}加载钱包状态文件时发生错误: {str(e)}")
            return {}
    
    def save_status(self):
        """保存钱包状态"""
        try:
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(self.status_data, f, ensure_ascii=False, indent=2)
            print(f"{Fore.GREEN}钱包状态已保存到: {self.status_file}")
        except Exception as e:
            print(f"{Fore.RED}保存钱包状态时发生错误: {str(e)}")
    
    def is_wallet_available(self, address: str) -> bool:
        """检查钱包是否可用（不在冷却期）"""
        if address not in self.status_data:
            return True
        
        wallet_info = self.status_data[address]
        if 'cooldown_until' in wallet_info:
            cooldown_until = datetime.fromisoformat(wallet_info['cooldown_until'])
            if datetime.now() < cooldown_until:
                remaining = cooldown_until - datetime.now()
                print(f"{Fore.YELLOW}钱包 {address} 仍在冷却期，剩余时间: {remaining}")
                return False
        
        if 'success_until' in wallet_info:
            success_until = datetime.fromisoformat(wallet_info['success_until'])
            if datetime.now() < success_until:
                remaining = success_until - datetime.now()
                print(f"{Fore.YELLOW}钱包 {address} 成功申请后冷却中，剩余时间: {remaining}")
                return False
        
        return True
    
    def record_cooldown(self, address: str, hours: int):
        """记录冷却期"""
        cooldown_until = datetime.now() + timedelta(hours=hours)
        if address not in self.status_data:
            self.status_data[address] = {}
        
        self.status_data[address]['cooldown_until'] = cooldown_until.isoformat()
        self.status_data[address]['last_update'] = datetime.now().isoformat()
        self.status_data[address]['status'] = 'cooldown'
        print(f"{Fore.RED}钱包 {address} 已记录冷却期，{hours}小时后可重新申请")
        self.save_status()
    
    def record_success(self, address: str, amount: float, tx_hash: str, hours: int = 120):
        """记录成功申请"""
        success_until = datetime.now() + timedelta(hours=hours)
        if address not in self.status_data:
            self.status_data[address] = {}
        
        self.status_data[address]['success_until'] = success_until.isoformat()
        self.status_data[address]['last_update'] = datetime.now().isoformat()
        self.status_data[address]['status'] = 'success'
        self.status_data[address]['amount'] = amount
        self.status_data[address]['tx_hash'] = tx_hash
        print(f"{Fore.GREEN}钱包 {address} 申请成功，{hours}小时后可重新申请")
        self.save_status()
    
    def record_duplicate_transaction(self, address: str):
        """记录重复交易错误"""
        if address not in self.status_data:
            self.status_data[address] = {}
        
        self.status_data[address]['last_update'] = datetime.now().isoformat()
        self.status_data[address]['status'] = 'duplicate_transaction'
        self.status_data[address]['error_count'] = self.status_data[address].get('error_count', 0) + 1
        print(f"{Fore.RED}钱包 {address} 记录重复交易错误")
        self.save_status()

def load_proxy() -> Optional[Dict[str, str]]:
    """从文件加载代理配置"""
    try:
        if os.path.exists('config/proxy.txt'):
            with open('config/proxy.txt', 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line in lines:
                line = line.strip()
                # 跳过注释和空行
                if line.startswith('#') or not line:
                    continue
                    
                # 解析代理配置
                if line.startswith(('http://', 'https://', 'socks5://')):
                    print(f"{Fore.GREEN}成功加载代理配置: {line}")
                    return {
                        'http': line,
                        'https': line
                    }
            
            print(f"{Fore.YELLOW}proxy.txt文件中没有找到有效的代理配置")
            return None
        else:
            print(f"{Fore.YELLOW}未找到proxy.txt文件，将不使用代理")
            return None
    except Exception as e:
        print(f"{Fore.RED}读取代理配置文件时发生错误: {str(e)}")
        return None

class TwoCaptchaSolver:
    """2captcha.com reCAPTCHA解决器"""
    
    def __init__(self, api_key: str, proxies: Optional[Dict[str, str]] = None):
        self.api_key = api_key
        self.base_url = "https://2captcha.com"  # 改为HTTPS
        self.session = requests.Session()
        if proxies:
            self.session.proxies.update(proxies)
            print(f"{Fore.CYAN}2captcha服务将使用代理: {proxies}")
        
    def solve_recaptcha(self, site_key: str, page_url: str) -> Optional[str]:
        """
        使用2captcha解决reCAPTCHA
        
        Args:
            site_key: reCAPTCHA站点密钥
            page_url: 包含reCAPTCHA的页面URL
            
        Returns:
            reCAPTCHA响应token或None
        """
        try:
            # 提交reCAPTCHA解决请求
            submit_url = f"{self.base_url}/in.php"
            submit_data = {
                'key': self.api_key,
                'method': 'userrecaptcha',
                'googlekey': site_key,
                'pageurl': page_url,
                'json': 1
            }
            
            print(f"{Fore.YELLOW}正在提交reCAPTCHA解决请求...")
            print(f"{Fore.CYAN}请求URL: {submit_url}")
            
            # 添加重试机制
            for attempt in range(3):
                try:
                    response = self.session.post(submit_url, data=submit_data, timeout=30)
                    response.raise_for_status()  # 检查HTTP错误
                    result = response.json()
                    
                    if result.get('status') == 1:
                        request_id = result.get('request')
                        print(f"{Fore.GREEN}reCAPTCHA解决请求已提交，ID: {request_id}")
                        
                        # 轮询获取结果
                        return self._get_recaptcha_result(request_id)
                    else:
                        print(f"{Fore.RED}提交reCAPTCHA解决请求失败: {result.get('error_text')}")
                        return None
                        
                except requests.exceptions.RequestException as e:
                    print(f"{Fore.RED}网络请求失败 (尝试 {attempt + 1}/3): {str(e)}")
                    if attempt < 2:  # 不是最后一次尝试
                        print(f"{Fore.YELLOW}等待5秒后重试...")
                        time.sleep(5)
                    else:
                        print(f"{Fore.RED}所有重试都失败了")
                        return None
                        
        except Exception as e:
            print(f"{Fore.RED}解决reCAPTCHA时发生错误: {str(e)}")
            return None
    
    def _get_recaptcha_result(self, request_id: str) -> Optional[str]:
        """轮询获取reCAPTCHA解决结果"""
        get_url = f"{self.base_url}/res.php"
        
        for attempt in range(30):  # 最多等待5分钟
            try:
                params = {
                    'key': self.api_key,
                    'action': 'get',
                    'id': request_id,
                    'json': 1
                }
                
                response = self.session.get(get_url, params=params, timeout=30)
                response.raise_for_status()
                result = response.json()
                
                if result.get('status') == 1:
                    print(f"{Fore.GREEN}reCAPTCHA解决成功!")
                    return result.get('request')
                elif result.get('request') == 'CAPCHA_NOT_READY':
                    print(f"{Fore.YELLOW}reCAPTCHA正在解决中... (尝试 {attempt + 1}/30)")
                    time.sleep(10)  # 等待10秒
                else:
                    print(f"{Fore.RED}获取reCAPTCHA结果失败: {result.get('error_text')}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                print(f"{Fore.RED}获取reCAPTCHA结果时网络错误 (尝试 {attempt + 1}/30): {str(e)}")
                if attempt < 29:  # 不是最后一次尝试
                    time.sleep(10)
                else:
                    print(f"{Fore.RED}获取reCAPTCHA结果超时")
                    return None
            except Exception as e:
                print(f"{Fore.RED}获取reCAPTCHA结果时发生错误: {str(e)}")
                return None
        
        print(f"{Fore.RED}reCAPTCHA解决超时")
        return None

class OctraFaucetBot:
    """Octra水龙头机器人"""
    
    def __init__(self, two_captcha_api_key: str, status_manager: WalletStatusManager):
        self.two_captcha_api_key = two_captcha_api_key
        self.status_manager = status_manager
        self.results = []  # 存储所有申请结果
        
    def claim_tokens(self, address: str, is_validator: bool = False, proxy: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        申请代币
        
        Args:
            address: Octra钱包地址
            is_validator: 是否为验证者
            
        Returns:
            响应结果字典
        """
        try:
            # 每次都新建会话和solver，使用当前代理
            two_captcha = TwoCaptchaSolver(self.two_captcha_api_key, proxy)
            session = requests.Session()
            if proxy:
                session.proxies.update(proxy)
                print(f"{Fore.CYAN}本次请求使用代理: {proxy}")
            session.headers.update({
                'accept': '*/*',
                'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7,ja;q=0.6,fr;q=0.5,ru;q=0.4,und;q=0.3',
                'content-type': 'application/x-www-form-urlencoded',
                'dnt': '1',
                'origin': 'https://faucet.octra.network',
                'priority': 'u=1, i',
                'referer': 'https://faucet.octra.network/',
                'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
            })
            # 使用硬编码的reCAPTCHA站点密钥
            site_key = RECAPTCHA_SITE_KEY
            print(f"{Fore.CYAN}使用硬编码的reCAPTCHA站点密钥: {site_key}")
            # 解决reCAPTCHA
            recaptcha_response = two_captcha.solve_recaptcha(
                site_key=site_key,
                page_url='https://faucet.octra.network/'
            )
            if not recaptcha_response:
                return {'success': False, 'error': 'reCAPTCHA解决失败'}
            # 准备表单数据 (URL编码格式)
            form_data = {
                'address': address,
                'is_validator': str(is_validator).lower(),
                'g-recaptcha-response': recaptcha_response
            }
            # 发送申请请求
            print(f"{Fore.CYAN}正在申请代币...")
            response = session.post(
                'https://faucet.octra.network/claim',
                data=form_data,  # 使用data而不是json，自动进行URL编码
                timeout=30
            )
            print(f"{Fore.CYAN}响应状态码: {response.status_code}")
            print(f"{Fore.CYAN}响应内容: {response.text}")
            
            # 处理响应
            if response.status_code == 200:
                try:
                    result = response.json()
                    
                    # 处理冷却期
                    if not result.get('success') and 'Cooldown active' in result.get('error', ''):
                        # 提取冷却时间
                        cooldown_match = re.search(r'Try again in (\d+) hours', result.get('error', ''))
                        if cooldown_match:
                            hours = int(cooldown_match.group(1))
                            self.status_manager.record_cooldown(address, hours)
                        else:
                            # 默认98小时
                            self.status_manager.record_cooldown(address, 98)
                        return {'success': False, 'error': result.get('error'), 'address': address, 'type': 'cooldown'}
                    
                    # 处理成功申请
                    elif result.get('success') and 'amount' in result and 'tx_hash' in result:
                        amount = result.get('amount', 0)
                        tx_hash = result.get('tx_hash', '')
                        self.status_manager.record_success(address, amount, tx_hash, 120)
                        return {'success': True, 'data': result, 'address': address, 'type': 'success'}
                    
                    # 处理重复交易
                    elif not result.get('success') and 'Duplicate transaction' in result.get('error', ''):
                        self.status_manager.record_duplicate_transaction(address)
                        return {'success': False, 'error': result.get('error'), 'address': address, 'type': 'duplicate'}
                    
                    # 其他成功情况
                    elif result.get('success'):
                        return {'success': True, 'data': result, 'address': address}
                    
                    # 其他错误
                    else:
                        return {'success': False, 'error': result.get('error', '未知错误'), 'address': address}
                        
                except json.JSONDecodeError:
                    return {'success': True, 'data': response.text, 'address': address}
            else:
                return {'success': False, 'error': f'HTTP错误: {response.status_code}', 'response': response.text, 'address': address}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'网络请求错误: {str(e)}', 'address': address}
        except Exception as e:
            return {'success': False, 'error': f'申请代币时发生错误: {str(e)}', 'address': address}

def load_api_key() -> Optional[str]:
    """从文件加载2captcha API密钥"""
    try:
        if os.path.exists('config/2captcha_api.txt'):
            with open('config/2captcha_api.txt', 'r', encoding='utf-8') as f:
                api_key = f.read().strip()
                if api_key:
                    print(f"{Fore.GREEN}成功从2captcha_api.txt加载API密钥")
                    return api_key
                else:
                    print(f"{Fore.RED}2captcha_api.txt文件为空")
                    return None
        else:
            print(f"{Fore.RED}未找到config/2captcha_api.txt文件")
            return None
    except Exception as e:
        print(f"{Fore.RED}读取API密钥文件时发生错误: {str(e)}")
        return None

def load_wallet_addresses() -> List[str]:
    """从all_outputs.json文件加载钱包地址"""
    try:
        if os.path.exists('config/all_outputs.json'):
            with open('config/all_outputs.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                addresses = [item.get('address') for item in data if item.get('address')]
                print(f"{Fore.GREEN}成功从all_outputs.json加载了{len(addresses)}个钱包地址")
                return addresses
        else:
            print(f"{Fore.RED}未找到config/all_outputs.json文件")
            return []
    except Exception as e:
        print(f"{Fore.RED}读取钱包地址文件时发生错误: {str(e)}")
        return []

def save_results(results: List[Dict[str, Any]], filename: str = 'faucet_results.json'):
    """保存申请结果到文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"{Fore.GREEN}申请结果已保存到 {filename}")
    except Exception as e:
        print(f"{Fore.RED}保存结果时发生错误: {str(e)}")

def test_network_connection(proxies: Optional[Dict[str, str]] = None):
    """测试网络连接"""
    print(f"{Fore.CYAN}正在测试网络连接...")
    try:
        # 测试2captcha.com连接
        session = requests.Session()
        if proxies:
            session.proxies.update(proxies)
            print(f"{Fore.CYAN}使用代理进行网络测试: {proxies}")
            
        response = session.get('https://2captcha.com', timeout=10)
        print(f"{Fore.GREEN}2captcha.com连接正常")
        return True
    except Exception as e:
        print(f"{Fore.RED}无法连接到2captcha.com: {str(e)}")
        if proxies:
            print(f"{Fore.YELLOW}代理连接可能有问题，请检查代理配置")
        else:
            print(f"{Fore.YELLOW}请检查网络连接或尝试使用VPN")
        return False

def show_copyright():
    """展示版权信息"""
    copyright_info = f"""{Fore.CYAN}
    *****************************************************
    *           X:https://x.com/ariel_sands_dan         *
    *           Tg:https://t.me/sands0x1                *
    *           Copyright (c) 2025                      *
    *           All Rights Reserved                     *
    *****************************************************
    {Style.RESET_ALL}
    """
    print(copyright_info)
    print('=' * 50)
    print(f"{Fore.GREEN}申请key: https://661100.xyz/ {Style.RESET_ALL}")
    print(f"{Fore.RED}联系Dandan: \n QQ:712987787 QQ群:1036105927 \n 电报:sands0x1 电报群:https://t.me/+fjDjBiKrzOw2NmJl \n 微信: dandan0x1{Style.RESET_ALL}")
    print('=' * 50)

def load_proxies() -> List[Optional[Dict[str, str]]]:
    """从文件加载所有代理配置，返回代理字典列表"""
    proxies = []
    try:
        proxy_path = 'config/proxy.txt'
        if os.path.exists(proxy_path):
            with open(proxy_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            for line in lines:
                line = line.strip()
                if line.startswith('#') or not line:
                    continue
                if line.startswith(('http://', 'https://', 'socks5://')):
                    proxies.append({'http': line, 'https': line})
            print(f"{Fore.GREEN}成功从proxy.txt加载{len(proxies)}个代理")
        else:
            print(f"{Fore.YELLOW}未找到config/proxy.txt文件，将不使用代理")
        return proxies
    except Exception as e:
        print(f"{Fore.RED}读取代理配置文件时发生错误: {str(e)}")
        return proxies

def main():
    """主函数"""
    show_copyright()
    
    # 初始化钱包状态管理器
    status_manager = WalletStatusManager()
    
    # 加载代理配置
    proxies_list = load_proxies()
    
    # 加载API密钥
    api_key = load_api_key()
    if not api_key:
        print(f"{Fore.RED}无法加载API密钥，程序退出!")
        return
    
    # 加载钱包地址
    addresses = load_wallet_addresses()
    if not addresses:
        print(f"{Fore.RED}无法加载钱包地址，程序退出!")
        return
    
    # 过滤可用钱包
    available_addresses = []
    for address in addresses:
        if status_manager.is_wallet_available(address):
            available_addresses.append(address)
        else:
            print(f"{Fore.YELLOW}跳过钱包 {address} (在冷却期)")
    
    if not available_addresses:
        print(f"{Fore.RED}没有可用的钱包地址，所有钱包都在冷却期!")
        return
    
    # 启动时提示
    print(f"{Fore.YELLOW}检测到 {len(addresses)} 个钱包地址，其中 {len(available_addresses)} 个可用。")
    print(f"{Fore.YELLOW}建议准备 {len(available_addresses)} 个代理（当前已加载 {len(proxies_list)} 个代理）。")
    if len(proxies_list) < len(available_addresses):
        print(f"{Fore.RED}警告：代理数量少于可用钱包数量，部分钱包将不使用代理或复用代理！")
    elif len(proxies_list) > len(available_addresses):
        print(f"{Fore.YELLOW}提示：代理数量多于可用钱包数量，多余的代理不会被使用。")
    
    # 测试网络连接
    test_proxy = proxies_list[0] if proxies_list else None
    if not test_network_connection(test_proxy):
        print(f"{Fore.RED}网络连接测试失败，程序退出!")
        return
    
    print(f"{Fore.YELLOW}是否为验证者? (y/n):")
    is_validator_input = input().strip().lower()
    is_validator = is_validator_input in ['y', 'yes', '是']
    
    # 询问是否继续
    print(f"{Fore.YELLOW}找到{len(available_addresses)}个可用钱包地址，是否开始批量申请? (y/n):")
    confirm = input().strip().lower()
    if confirm not in ['y', 'yes', '是']:
        print(f"{Fore.YELLOW}用户取消操作")
        return
    
    # 创建机器人实例
    bot = OctraFaucetBot(api_key, status_manager)
    # 批量申请代币
    print(f"{Fore.CYAN}开始批量申请代币...")
    successful_count = 0
    failed_count = 0
    for i, address in enumerate(available_addresses, 1):
        print(f"\n{Fore.CYAN}{'='*50}")
        print(f"{Fore.CYAN}正在处理第 {i}/{len(available_addresses)} 个钱包地址")
        print(f"{Fore.CYAN}钱包地址: {address}")
        # 取对应代理
        proxy = proxies_list[i-1] if i-1 < len(proxies_list) else None
        if proxy:
            proxy_str = list(proxy.values())[0]
            print(f"{Fore.CYAN}使用代理: {proxy_str}")
        else:
            print(f"{Fore.YELLOW}未使用代理")
        print(f"{Fore.CYAN}{'='*50}")
        # 申请代币
        result = bot.claim_tokens(address, is_validator, proxy)
        bot.results.append(result)
        # 显示结果
        if result['success']:
            print(f"{Fore.GREEN}申请成功!")
            successful_count += 1
        else:
            print(f"{Fore.RED}申请失败: {result['error']}")
            failed_count += 1
        # 添加延迟，避免请求过于频繁
        if i < len(available_addresses):
            print(f"{Fore.YELLOW}等待5秒后继续下一个...")
            time.sleep(5)
    # 显示最终统计
    print(f"\n{Fore.CYAN}{'='*50}")
    print(f"{Fore.CYAN}批量申请完成!")
    print(f"{Fore.GREEN}成功: {successful_count} 个")
    print(f"{Fore.RED}失败: {failed_count} 个")
    print(f"{Fore.CYAN}总计: {len(available_addresses)} 个")
    print(f"{Fore.CYAN}{'='*50}")
    # 保存结果
    save_results(bot.results)

if __name__ == '__main__':
    main()
