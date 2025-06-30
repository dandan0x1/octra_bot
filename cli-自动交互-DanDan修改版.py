#!/usr/bin/env python3
import json, base64, hashlib, time, sys, re, random, string, os, shutil, asyncio, aiohttp
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import nacl.signing
import itertools
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

priv, addr, rpc = None, None, None
sk, pub = None, None
b58 = re.compile(r"^oct[1-9A-HJ-NP-Za-km-z]{44}$")
μ = 1_000_000
h = []
cb, cn, lu, lh = None, None, 0, 0
session = None
executor = ThreadPoolExecutor(max_workers=1)
spinner_frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
spinner_idx = 0

def ld():
    global priv, addr, rpc, sk, pub
    try:
        with open('config/wallet.json', 'r') as f:
            d = json.load(f)
        priv = d.get('priv')
        addr = d.get('addr')
        rpc = d.get('rpc', 'https://octra.network')
        sk = nacl.signing.SigningKey(base64.b64decode(priv))
        pub = base64.b64encode(sk.verify_key.encode()).decode()
        return True
    except:
        return False

async def req(m, p, d=None, t=10, proxy=None):
    global session
    if not session:
        session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=t))
    try:
        url = f"{rpc}{p}"
        async with getattr(session, m.lower())(url, json=d if m == 'POST' else None, proxy=proxy) as resp:
            text = await resp.text()
            try:
                j = json.loads(text) if text else None
            except:
                j = None
            return resp.status, text, j
    except asyncio.TimeoutError:
        return 0, "timeout", None
    except Exception as e:
        return 0, str(e), None

async def st():
    global cb, cn, lu
    now = time.time()
    if cb is not None and (now - lu) < 30:
        return cn, cb
    
    results = await asyncio.gather(
        req('GET', f'/balance/{addr}'),
        req('GET', '/staging', 5),
        return_exceptions=True
    )
    
    s, t, j = results[0] if not isinstance(results[0], Exception) else (0, str(results[0]), None)
    s2, _, j2 = results[1] if not isinstance(results[1], Exception) else (0, None, None)
    
    if s == 200 and j:
        cn = int(j.get('nonce', 0))
        cb = float(j.get('balance', 0))
        lu = now
        if s2 == 200 and j2:
            our = [tx for tx in j2.get('staged_transactions', []) if tx.get('from') == addr]
            if our:
                cn = max(cn, max(int(tx.get('nonce', 0)) for tx in our))
    elif s == 404:
        cn, cb, lu = 0, 0.0, now
    elif s == 200 and t and not j:
        try:
            parts = t.strip().split()
            if len(parts) >= 2:
                cb = float(parts[0]) if parts[0].replace('.', '').isdigit() else 0.0
                cn = int(parts[1]) if parts[1].isdigit() else 0
                lu = now
            else:
                cn, cb = None, None
        except:
            cn, cb = None, None
    return cn, cb

async def gh():
    global h, lh
    now = time.time()
    if now - lh < 60 and h:
        return
    s, t, j = await req('GET', f'/address/{addr}?limit=20')
    if s != 200 or (not j and not t):
        return
    
    if j and 'recent_transactions' in j:
        tx_hashes = [ref["hash"] for ref in j.get('recent_transactions', [])]
        tx_results = await asyncio.gather(*[req('GET', f'/tx/{hash}', 5) for hash in tx_hashes], return_exceptions=True)
        
        existing_hashes = {tx['hash'] for tx in h}
        nh = []
        
        for i, (ref, result) in enumerate(zip(j.get('recent_transactions', []), tx_results)):
            if isinstance(result, Exception):
                continue
            s2, _, j2 = result
            if s2 == 200 and j2 and 'parsed_tx' in j2:
                p = j2['parsed_tx']
                tx_hash = ref['hash']
                
                if tx_hash in existing_hashes:
                    continue
                
                ii = p.get('to') == addr
                ar = p.get('amount_raw', p.get('amount', '0'))
                a = float(ar) if '.' in str(ar) else int(ar) / μ
                nh.append({
                    'time': datetime.fromtimestamp(p.get('timestamp', 0)),
                    'hash': tx_hash,
                    'amt': a,
                    'to': p.get('to') if not ii else p.get('from'),
                    'type': 'in' if ii else 'out',
                    'ok': True,
                    'nonce': p.get('nonce', 0),
                    'epoch': ref.get('epoch', 0)
                })
        
        oh = datetime.now() - timedelta(hours=1)
        h[:] = sorted(nh + [tx for tx in h if tx.get('time', datetime.now()) > oh], key=lambda x: x['time'], reverse=True)[:50]
        lh = now
    elif s == 404 or (s == 200 and t and 'no transactions' in t.lower()):
        h.clear()
        lh = now

def mk(to, a, n):
    tx = {
        "from": addr,
        "to_": to,
        "amount": str(int(a * μ)),
        "nonce": int(n),
        "ou": "1" if a < 1000 else "3",
        "timestamp": time.time() + random.random() * 0.01
    }
    bl = json.dumps(tx, separators=(",", ":"))
    sig = base64.b64encode(sk.sign(bl.encode()).signature).decode()
    tx.update(signature=sig, public_key=pub)
    return tx, hashlib.sha256(bl.encode()).hexdigest()

async def snd(tx):
    t0 = time.time()
    s, t, j = await req('POST', '/send-tx', tx)
    dt = time.time() - t0
    if s == 200:
        if j and j.get('status') == 'accepted':
            return True, j.get('tx_hash', ''), dt, j
        elif t.lower().startswith('ok'):
            return True, t.split()[-1], dt, None
    return False, json.dumps(j) if j else t, dt, j

async def expl():
    print("\n=== 导出密钥 (export keys) ===")
    print("当前钱包信息:")
    print(f"地址: {addr}")
    n, b = await st()
    print(f"余额: {b:.6f} oct" if b is not None else "余额: ---")
    print("\n导出选项:")
    print("1. 显示私钥 (show private key)")
    print("2. 保存钱包到文件 (save wallet to file)")
    print("3. 复制地址到剪贴板 (copy address to clipboard)")
    print("0. 取消 (cancel)")
    choice = input("请选择 (choice): ").strip()
    if choice == '1':
        print("\n私钥 (请妥善保管！):")
        print(priv)
        print("公钥:")
        print(pub)
        input("按回车继续 (press enter to continue)...")
    elif choice == '2':
        fn = f"octra_wallet_{int(time.time())}.json"
        wallet_data = {
            'priv': priv,
            'addr': addr,
            'rpc': rpc
        }
        with open(fn, 'w') as f:
            json.dump(wallet_data, f, indent=2)
        print(f"已保存到 {fn}")
        print("文件包含私钥，请妥善保管！")
        input("按回车继续 (press enter to continue)...")
    elif choice == '3':
        try:
            import pyperclip
            if addr is not None:
                pyperclip.copy(str(addr))
                print("地址已复制到剪贴板！")
            else:
                print("未配置地址，无法复制。")
        except:
            print("剪贴板不可用 (clipboard not available)")
        input("按回车继续 (press enter to continue)...")
    else:
        print("已取消 (cancelled)")

async def tx():
    print("\n=== 发送交易 (send transaction) ===")
    to = input("请输入收款地址 (to address, 输入esc取消): ").strip()
    if not to or to.lower() == 'esc':
        return
    if not b58.match(to):
        print("地址无效！(invalid address)")
        input("按回车返回 (press enter to go back)...")
        return
    print(f"收款地址: {to}")
    a = input("请输入金额 (amount, 输入esc取消): ").strip()
    if not a or a.lower() == 'esc':
        return
    if not re.match(r"^\d+(\.\d+)?$", a) or float(a) <= 0:
        print("金额无效！(invalid amount)")
        input("按回车返回 (press enter to go back)...")
        return
    a = float(a)
    global lu
    lu = 0
    n, b = await st()
    if n is None:
        print("获取nonce失败！(failed to get nonce)")
        input("按回车返回 (press enter to go back)...")
        return
    if not b or b < a:
        print(f"余额不足！(insufficient balance {b:.6f} < {a})")
        input("按回车返回 (press enter to go back)...")
        return
    print(f"将发送 {a:.6f} oct 到 {to}")
    print(f"手续费: {'0.001' if a < 1000 else '0.003'} oct (nonce: {n + 1})")
    confirm = input("确认发送？[y/n]: ").strip().lower()
    if confirm != 'y':
        return
    print("正在发送交易，请稍候...")
    t, _ = mk(to, a, n + 1)
    ok, hs, dt, r = await snd(t)
    if ok:
        print("✓ 交易已接受！(transaction accepted)")
        print(f"hash: {hs}")
        print(f"用时: {dt:.2f}s")
        if r and 'pool_info' in r:
            print(f"池中待处理交易数: {r['pool_info'].get('total_pool_size', 0)}")
        h.append({
            'time': datetime.now(),
            'hash': hs,
            'amt': a,
            'to': to,
            'type': 'out',
            'ok': True
        })
        lu = 0
    else:
        print("✗ 交易失败！(transaction failed)")
        print(f"错误信息: {str(hs)}")
    input("按回车继续 (press enter to continue)...")

def load_proxies():
    with open('config/proxy.txt', 'r') as f:
        proxies = [line.strip() for line in f if line.strip()]
    return proxies

async def multi():
    import logging
    global addr, lu
    print("\n=== 多地址发送 (multi send) ===")
    with open('config/all_outputs.json', 'r') as f:
        wallets = json.load(f)
    proxies = load_proxies()
    proxy_cycle = itertools.cycle(proxies)
    amount = float(input("请输入每个地址要发送的金额: ").strip())
    batch_size = 10
    max_proxy_retries = 3

    for idx, sender in enumerate(wallets):
        proxy_tried = set()
        proxy_success = False
        for _ in range(len(proxies)):
            proxy = next(proxy_cycle)
            if proxy in proxy_tried:
                continue
            proxy_tried.add(proxy)
            print(f"\n--- 当前发送方: {sender['address']} 使用代理: {proxy} ---")
            candidates = [w['address'] for i, w in enumerate(wallets) if i != idx]
            if len(candidates) < batch_size:
                print("收款地址数量不足10个，跳过。")
                break
            recipients = random.sample(candidates, batch_size)
            rcp = [(addr, amount) for addr in recipients]
            tot = amount * len(recipients)
            print(f"将从 {sender['address']} 向以下10个地址各发送 {amount} oct：")
            for addr_ in recipients:
                print(f"  {addr_}")
            # 同步切换全局钱包变量
            global priv, sk, pub, addr
            priv = sender.get('private_key_b64')
            sk = nacl.signing.SigningKey(base64.b64decode(priv))
            pub = base64.b64encode(sk.verify_key.encode()).decode()
            addr = sender['address']
            lu = 0
            # 获取nonce和余额，带代理，失败重试
            for retry in range(1, max_proxy_retries + 1):
                try:
                    n, b = await st_with_proxy(proxy)
                    if n is None or not b or b < tot:
                        print(f"[代理{proxy}] 第{retry}次尝试：余额不足或获取nonce失败。")
                        if retry == max_proxy_retries:
                            print(f"[代理{proxy}] 连续{max_proxy_retries}次失败，切换下一个代理。")
                        continue
                    # 发送
                    for i, (to, a) in enumerate(rcp):
                        for send_retry in range(1, max_proxy_retries + 1):
                            t, _ = mk(to, a, n + 1 + i)
                            ok, hs, dt, r = await snd_with_proxy(t, proxy)
                            if ok:
                                print(f"✓ 成功: {to} hash: {hs}")
                                break
                            else:
                                print(f"✗ 失败: {to} 错误: {hs} (第{send_retry}次尝试)")
                                if send_retry == max_proxy_retries:
                                    print(f"[代理{proxy}] 对{to}连续{max_proxy_retries}次发送失败，跳过该地址。")
                    print("本轮发送完成。")
                    print("5秒后自动切换到下一个钱包...")
                    time.sleep(5)
                    proxy_success = True
                    break
                except Exception as e:
                    print(f"[代理{proxy}] 第{retry}次尝试发生异常: {e}")
                    if retry == max_proxy_retries:
                        print(f"[代理{proxy}] 连续{max_proxy_retries}次异常，切换下一个代理。")
            if proxy_success:
                break
        if not proxy_success:
            print(f"发送方 {sender['address']} 所有代理均失败，跳过该发送方。")

async def st_with_proxy(proxy):
    global cb, cn, lu
    now = time.time()
    if cb is not None and (now - lu) < 30:
        return cn, cb
    results = await asyncio.gather(
        req('GET', f'/balance/{addr}', proxy=proxy),
        req('GET', '/staging', 5, proxy=proxy),
        return_exceptions=True
    )
    s, t, j = results[0] if not isinstance(results[0], Exception) else (0, str(results[0]), None)
    s2, _, j2 = results[1] if not isinstance(results[1], Exception) else (0, None, None)
    if s == 200 and j:
        cn = int(j.get('nonce', 0))
        cb = float(j.get('balance', 0))
        lu = now
        if s2 == 200 and j2:
            our = [tx for tx in j2.get('staged_transactions', []) if tx.get('from') == addr]
            if our:
                cn = max(cn, max(int(tx.get('nonce', 0)) for tx in our))
    elif s == 404:
        cn, cb, lu = 0, 0.0, now
    elif s == 200 and t and not j:
        try:
            parts = t.strip().split()
            if len(parts) >= 2:
                cb = float(parts[0]) if parts[0].replace('.', '').isdigit() else 0.0
                cn = int(parts[1]) if parts[1].isdigit() else 0
                lu = now
            else:
                cn, cb = None, None
        except:
            cn, cb = None, None
    return cn, cb

async def snd_with_proxy(tx, proxy):
    t0 = time.time()
    s, t, j = await req('POST', '/send-tx', tx, proxy=proxy)
    dt = time.time() - t0
    if s == 200:
        if j and j.get('status') == 'accepted':
            return True, j.get('tx_hash', ''), dt, j
        elif t.lower().startswith('ok'):
            return True, t.split()[-1], dt, None
    return False, json.dumps(j) if j else t, dt, j

async def main():
    show_copyright()
    time.sleep(5)
    global session
    
    # if not ld():
    #     sys.exit("[!] wallet.json error")
    # if not addr:
    #     sys.exit("[!] wallet.json not configured")
    
    try:
        await st()
        await gh()
        
        while True:
            print(f"{Fore.CYAN} ==== DanDan Octra client 1.0 修改版 ==== {Style.RESET_ALL}")
            print(f"{Fore.GREEN} 1. 多地址发送 (multi send) {Style.RESET_ALL}")
            print(f"{Fore.WHITE} 2. 刷新余额 (refresh balance) {Style.RESET_ALL}")
            print(f"{Fore.CYAN} 0. 退出 (exit) {Style.RESET_ALL}")
            cmd = input("请输入命令编号 (command): ").strip()
            if cmd == '2':
                global lu, lh
                lu = lh = 0
                await st()
                await gh()
                print("余额已刷新。")
            elif cmd == '1':
                await multi()
            elif cmd in ['0', 'q', '']:
                print("已退出。")
                break
            else:
                print("无效命令，请重新输入。")
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        if session:
            await session.close()
        executor.shutdown(wait=False)

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore", category=ResourceWarning)
    
    try:
        asyncio.run(main())
    except:
        pass
    finally:
        os._exit(0)
