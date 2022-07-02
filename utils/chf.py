

import requests, re, yaml
from re import Pattern
from typing import Any, Dict, List

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

rss_url:str = 'https://www.cfmem.com/feeds/posts/default?alt=rss'
clash_reg:Pattern = re.compile(r'clash订阅链接：(https?.+?)(?:&lt;|<)/span(?:&gt;|>)')


clash_output_file:str = './subs/chf.yaml'
clash_output_tpl:str = './utils/clash.config.template.yaml'
    
clash_extra:List[str] = ['https://free886.herokuapp.com/clash/proxies']

blacklist:List[str] = list(map(lambda l:l.replace('\r', '').replace('\n', '').split(':'),
        ['game.tcpbbr.net:5228','213.183.53.177:9037','jp.tcpbbr.net:443','tw.tcpbbr.net:443']))

def clash_urls(html:str) -> List[str]:
    '''
    Fetch URLs For Clash
    '''
    return clash_reg.findall(html) + clash_extra

def fetch_html(url:str) -> str:
    '''
    Fetch The Content Of url
    '''
    try:
        resp:requests.Response = requests.get(url, verify=False, timeout=10)
        if resp.status_code != 200:
            print(f'[!] Got HTTP Status Code {resp.status_code}')
            return None 
        return resp.text
    except Exception as e:
        print(f'[-] Error Occurs When Fetching Content Of {url}')
        return None

def merge_clash(configs:List[str]) -> str:
    '''
    Merge Multiple Clash Configurations
    '''
    config_template:Dict[str, Any] = yaml.safe_load(open(clash_output_tpl).read())
    proxies:List[Dict[str, Any]] = []
    for i in range(len(configs)):
        tmp_config:Dict[str, Any] = yaml.safe_load(configs[i])
        if 'proxies' not in tmp_config: continue
        for j in range(len(tmp_config['proxies'])):
            proxy:Dict[str, Any] = tmp_config['proxies'][j]
            if any(filter(lambda p:p[0] == proxy['server'] and str(p[1]) == str(proxy['port']), blacklist)): continue
            if any(filter(lambda p:p['server'] == proxy['server'] and p['port'] == proxy['port'], proxies)): continue
            proxy['name'] = proxy['name'] + f'_{i}@{j}'
            proxies.append(proxy)
    node_names:List[str] = list(map(lambda n: n['name'], proxies))
    config_template['proxies'] = proxies
    for grp in config_template['proxy-groups']:
        if 'xxx' in grp['proxies']:
            grp['proxies'].remove('xxx')
            grp['proxies'].extend(node_names)

    return yaml.safe_dump(config_template, indent=2, allow_unicode=True)


def main():
    rss_text:str = fetch_html(rss_url)
    if rss_text is None or len(rss_text) <= 0: 
        print('[-] Failed To Fetch Content Of RSS')
        return
    clash_url_list:List[str] = clash_urls(rss_text)

    print(f'[+] Got {len(clash_url_list)} Clash URLs')

    clash_configs:List[str] = list(filter(lambda h: h is not None and len(h) > 0, map(lambda u: fetch_html(u), clash_url_list)))

    clash_merged:str = merge_clash(clash_configs)

    with open(clash_output_file, 'w') as f: f.write(clash_merged)

if __name__ == '__main__':
    main()
