import requests,glob,re,json,time
from colorama import *

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

class WalletGenerator:
    def __init__(self, url, headers):
        self.url = url
        self.headers = headers

    def generate_wallets(self, num):
        for i in range(1, num + 1):
            response = requests.post(self.url, headers=self.headers)
            filename = f'config/output_{i}.txt'
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f'第{i}次响应内容已保存到{filename}')

    def extract_wallet_info(self):
        for txt_file in glob.glob('config/output_*.txt'):
            with open(txt_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            wallet_line = None
            for line in lines:
                if 'Wallet generation complete!' in line:
                    wallet_line = line
                    break
            if wallet_line:
                match = re.search(r'data: (\{.*\})', wallet_line)
                if match:
                    data = json.loads(match.group(1))
                    wallet = data.get('wallet', {})
                    result = {
                        'private_key_b64': wallet.get('private_key_b64'),
                        'public_key_b64': wallet.get('public_key_b64'),
                        'address': wallet.get('address')
                    }
                    json_file = txt_file.replace('.txt', '.json')
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    print(f'{txt_file} 已保存为 {json_file}')
                else:
                    print(f'{txt_file} 未找到JSON数据')
            else:
                print(f'{txt_file} 未找到钱包生成完成的数据行')

    def merge_json_files(self):
        all_results = []
        for json_file in glob.glob('config/output_*.json'):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_results.append(data)
        with open('config/all_outputs.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print('所有output_*.json已合并为all_outputs.json')

if __name__ == '__main__':
    show_copyright()
    time.sleep(5)
    url = 'http://localhost:8888/generate'
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7,ja;q=0.6,fr;q=0.5,ru;q=0.4,und;q=0.3',
        'Connection': 'keep-alive',
        'Content-Length': '0',
        'DNT': '1',
        'Origin': 'http://localhost:8888',
        'Referer': 'http://localhost:8888/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"'
    }
    num = int(input('请输入想要生成的次数: '))
    wg = WalletGenerator(url, headers)
    wg.generate_wallets(num)
    wg.extract_wallet_info()
    wg.merge_json_files()