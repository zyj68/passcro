#!/usr/bin/env python3

import os, re, yaml, json, base64
import requests, socket, urllib.parse
from requests.adapters import HTTPAdapter




class sub_convert():

    """
    将订阅链接或者订阅内容输入 convert 函数中, 第一步将内容转化为 Clash 节点配置字典, 第二步对节点进行去重和重命名等修饰处理, 第三步输出指定格式. 
    第一步堆栈: 
        YAML To Dict:
            raw_yaml
            convert --> transfer --> format
            dict
        URL To Dict:
            raw_url
            convert --> transfer --> format --> yaml_encode --> format
            dict
        Base64 To Dict:
            raw_base64
            convert --> transfer --> base64_decode --> format --> yaml_encode --> format
            dict
    第二步堆栈:
        dict
        convert --> makeup --> format
        yaml_final
    第三步堆栈:
        YAML To YAML:
            yaml_final
            makeup --> convert
            yaml_final
        YAML To URL:
            yaml_final
            makeup --> yaml_decode --> convert
            url_final
        YAML To Base64:
            yaml_final
            makeup --> yaml_decode --> base64_encode --> convert
            base64_final
    """

    def convert(raw_input, input_type='url', output_type='url'): # {'input_type': ['url', 'content'],'output_type': ['url', 'YAML', 'Base64']}
        # convert Url to YAML or Base64
        if input_type == 'url': # 获取 URL 订阅链接内容
            sub_content = ''
            if isinstance(raw_input, list):
                a_content = []
                for url in raw_input:
                    s = requests.Session()
                    s.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36"}
                    s.mount('http://', HTTPAdapter(max_retries=5))
                    s.mount('https://', HTTPAdapter(max_retries=5))
                    try:
                        print('Downloading from:' + url)
                        resp = s.get(url, timeout=5)
                        s_content = sub_convert.yaml_decode(sub_convert.transfer(resp.content.decode('utf-8')))
                        a_content.append(s_content)
                    except Exception as err:
                        print(err)
                        return 'Url 解析错误'
                sub_content = sub_convert.transfer(''.join(a_content))
            else:
                s = requests.Session()
                s.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36"}
                s.mount('http://', HTTPAdapter(max_retries=5))
                s.mount('https://', HTTPAdapter(max_retries=5))
                try:
                    print('Downloading from:' + raw_input)
                    resp = s.get(raw_input, timeout=5)
                    sub_content = sub_convert.transfer(resp.content.decode('utf-8'))
                except Exception as err:
                    print(err)
                    return 'Url 解析错误'
        elif input_type == 'content': # 解析订阅内容
            sub_content = sub_convert.transfer(raw_input)

        if sub_content != '订阅内容解析错误': # 输出

            final_content = sub_convert.makeup(sub_content)
            if output_type == 'YAML':
                return final_content
            elif output_type == 'Base64':
                return sub_convert.base64_encode(sub_convert.yaml_decode(final_content))
            elif output_type == 'url':
                return sub_convert.yaml_decode(final_content)
            else:
                print('Please define right output type.')
                return '订阅内容解析错误'
        else:
            return '订阅内容解析错误'
    def transfer(sub_content): # 将 URLnode 内容转换为 YAML 格式

        if 'proxies:' in sub_content: # 判断字符串是否在文本中，是，判断为YAML。https://cloud.tencent.com/developer/article/1699719
            url_content = sub_convert.format(sub_content)
            return url_content
            #return self.url_content.replace('\r','') # 去除‘回车\r符’ https://blog.csdn.net/jerrygaoling/article/details/81051447
        elif '://'  in sub_content: # 同上，是，判断为 Urlnode 链接内容。
            url_content = sub_convert.yaml_encode(sub_convert.format(sub_content))
            return url_content
        else: # 判断 Base64.
            try:
                url_content = sub_convert.base64_decode(sub_content)
                url_content = sub_convert.yaml_encode(sub_convert.format(url_content))
                return url_content
            except Exception: # 万能异常 https://blog.csdn.net/Candance_star/article/details/94135515
                print('订阅内容解析错误')
                return '订阅内容解析错误'



    def format(sub_content, output=False): # 对节点 Url 进行格式化处理, 输出节点的//分行,或者字典格式与YAML文本格式互换

        if 'proxies:' not in sub_content: # 对 URL 内容进行格式化处理
            url_list = []
            try:
                if '://' not in sub_content:
                    sub_content = sub_convert.base64_encode(sub_content)
                raw_url_list = re.split(r'\n+', sub_content)

                for url in raw_url_list:
                    if len(re.findall(r'[^e]ss://|ssr://|vmess://|trojan://|vless://', url)) > 1:
                        url_line = re.sub(r'((?<!vme|vle)ss://|ssr://|vmess://|trojan://|vless://)',r'\n\1',url)
                        url_list.extend(re.split(r'\n',url_line.strip()))
                    elif len(url)>0:
                        url_list.append(url)
  

                url_content = '\n'.join(url_list)

                return url_content
            except:
                print('Sub_content 格式错误')
                return ''

        elif 'proxies:' in sub_content: # 对 Clash 内容进行格式化处理
            try:
                try_load = yaml.safe_load(sub_content)
                if output == False:
                    sub_content_yaml = try_load
                elif output == True:
                    sub_content_yaml = sub_content
            except Exception:
                try:
                    sub_content = sub_content.replace('\'', '').replace('"', '')
                    url_list = []
                    il_chars = ['|','丨', '?', '[', ']', '@', '!', '%']

                    lines = re.split(r'\n+', sub_content)
                    line_fix_list = []
                    for line in lines:
                        value_list = re.split(r': |, ', line)
                        if len(value_list) > 6:
                            # '- {name: 🇨🇳 v1丨印度丨北京- HK隧道-印度丨顺手更新下订阅, server: zhuanfabj1.yooo.me, port: 44174, type: trojan, password: 1973d939-d6fc-3ead-9a46-fcd771c71dd0, skip-cert-verify: true}'
                            # line = re.sub(r'(name: *[^:]*?)(?<=,| )[?@!%]([^:]*?, *\b\w*?:)',r'\1\2',bb)
                            line = re.sub(r'name: *([^:]*?[\[\]?,][^:]*?)(, *\b\w*?:)',r'name: "\1"\2',line)
                            # '  - {name: GLaDOS-Portalgun-08, server: c68b799.v9.gladns.com, port: 3331, type: vmess, uuid: 57e0cb4d-eae5-48ec-8091-149dc2b309e0, alterId: 0, cipher: auto, tls: true, skip-cert-verify: true, network: ws, ws-path: /t, ws-headers: {Host: %7B%22Edge%22:%22c68b799.fm.huawei.com:50307%22,%22Host%22:%22tls.apple.com%22%7D}, udp: true}'
                            line = re.sub(r'path: *([^:]*?[?%][^:]*?)((, *\b\w*?:)|(}))',r'path: "\1"\2',line)
                            line = re.sub(r'{Host: *([^}]*?[?%].*?)}', r'{Host: "\1"}', line)

                            try:
                                yaml.safe_load(line)
                                line_fix_list.append(line)
                            except Exception:
                                print(f'yaml格式有非法字符 :  {line}')
                        else:
                            try:
                                yaml.safe_load(line)
                                line_fix_list.append(line)
                            except Exception:
                                print(f'yaml格式有非法字符 :  {line}')

                    sub_content = '\n'.join(line_fix_list).replace('False', 'false').replace('True', 'true')

                    if output == False:
                        sub_content_yaml = yaml.safe_load(sub_content)
                    else: # output 值为 True 时返回修饰过的 YAML 文本
                        sub_content_yaml = sub_content
                except:
                    print('Sub_content 格式错误')
                    return '' # 解析 URL 内容错误时返回空字符串
            if output == False:
                for item in sub_content_yaml['proxies']:# 对转换过程中出现的不标准配置格式转换
                    try:
                        if item['type'] == 'vmess' and 'ws-path' in item.keys():
                            item['ws-opts'] = {'path': item.pop('ws-path')}
                        if item['type'] == 'vmess' and 'HOST' in item['ws-headers'].keys():
                            item['ws-headers']['Host'] = item['ws-headers'].pop("HOST")
                        if item['type'] == 'vmess' and 'ws-headers' in item.keys():
                            item['ws-opts']['headers'] = item.pop('ws-headers')


                    except KeyError:
                        if '.' not in item['server']:
                            sub_content_yaml['proxies'].remove(item)
                        pass

            return sub_content_yaml # 返回字典, output 值为 True 时返回修饰过的 YAML 文本
    def makeup(input): # 对节点进行重命名和格式化，输出 YAML 文本 
        # 区域判断(Clash YAML): https://blog.csdn.net/CSDN_duomaomao/article/details/89712826 (ip-api)
        if isinstance(input, dict):
            sub_content = input
        else:
            if 'proxies:' in input:
                sub_content = sub_convert.format(input)
            else:
                yaml_content_raw = sub_convert.convert(input, 'content', 'YAML')
                sub_content = yaml.safe_load(yaml_content_raw)
        proxies_list = sub_content['proxies']


        # 重命名重复节点
        pdlst = [proxies_list[i]['name'] for i in range(len(proxies_list))]
        thnlst = list(set(pdlst))

        for i in range(len(thnlst)):
            if pdlst.count(thnlst[i]) > 1:
                n = 0
                for k in range(len(proxies_list)):
                    if proxies_list[k]['name'] == thnlst[i]:
                        n += 1
                        proxies_list[k]['name'] = f'{thnlst[i]} {str(n).zfill(3)}'

        print('共发现:{}个节点'.format(len(proxies_list)))

        for i in proxies_list:
            i['name'] = i['name'].strip()
        url_names = [i['name'] for i in proxies_list if i['server'] != '127.0.0.1']
        url_list = [str(i) for i in proxies_list if i['server'] != '127.0.0.1']

        clashmodel['proxies'] = url_list
        clashmodel['proxy-groups'][0]['proxies']= ['♻️ automatic'] + url_names
        clashmodel['proxy-groups'][1]['proxies']=url_names
        yaml_content_dic = clashmodel

        yaml_content_raw = yaml.dump(yaml_content_dic, default_flow_style=False, sort_keys=False, allow_unicode=True, width=750, indent=2) # yaml.dump 显示中文方法 https://blog.csdn.net/weixin_41548578/article/details/90651464 yaml.dump 各种参数 https://blog.csdn.net/swinfans/article/details/88770119
        yaml_content = yaml_content_raw.replace('\'', '').replace('False', 'false').replace('True', 'true').replace('- {name','  - {name')

        yaml_content = sub_convert.format(yaml_content,True)

        return yaml_content # 输出 YAML 格式文本

    def yaml_encode(url_content): # 将 URL 内容转换为 YAML (输出默认 YAML 格式)
        url_list = []
        lines = re.split(r'\n+', url_content)
        for line in lines:
            yaml_url = {}
            if 'vmess://' in line:
                try:
                    node_tent = line[8:]
                    if node_tent.find('?') < 0:
                        proxy_str = sub_convert.safe_decode(node_tent)
                        vmess_json = json.loads(proxy_str)

                    else:
                        nodgrp = re.match(r'(^.*?)(\?.*?$)',node_tent)
                        proxy_str = sub_convert.safe_decode(nodgrp.group(1))+nodgrp.group(2)

                        flags = dict()
                        matcher = re.match(r'(.*?):(.*)@(.*):(.*)\?', proxy_str)
                        if matcher:
                            flags['cipher'] = matcher.group(1)
                            flags['id'] = matcher.group(2)
                            flags['add'] = matcher.group(3)
                            flags['port'] = matcher.group(4)
                            span = [i.split('=') for i in proxy_str.split('?')[1].split('&')]
                            flags.update(dict(span))
                            vmess_json = flags
                        else:
                            print(f'v2ray节点解析失败,链接:  {node}')

                    if vmess_json['id'] == '' or vmess_json['id'] is None:
                        print('v2ray节点格式错误')
                    else:
                        yaml_url['name'] = sub_convert.safe_unquote(vmess_json.get('remarks') or vmess_json.get('ps')) or 'v2_node'
                        yaml_url['server'] = vmess_json.get('add')
                        yaml_url['port'] = int(vmess_json.get('port'))
                        yaml_url['type'] = 'vmess'
                        yaml_url['uuid'] = vmess_json['id']
                        yaml_url['alterId'] = int(vmess_json.get('aid') or vmess_json.get('alterId') or 0)
                        yaml_url['cipher'] = vmess_json.get('cipher') or  vmess_json.get('scy') or 'auto'
                        yaml_url['tls'] = True if vmess_json.get('tls') in ['1','tls','true','True'] else False
                        yaml_url['skip-cert-verify'] = False

                        nets = vmess_json.get('obfs') or vmess_json.get('net') or vmess_json.get('ws-path')
                        if nets in ['websocket', 'ws']:
                            yaml_url['network'] = 'ws'

                            if  vmess_json.get('path'):
                                yaml_url['ws-opts'] = {'path': vmess_json['path']}

                            else:
                                yaml_url['ws-opts'] = {'path': '/'}
                            if vmess_json.get('obfsParam'):
                                yaml_url['ws-opts']['headers'] = {'Host':vmess_json['obfsParam']}
                            elif vmess_json.get('peer'):
                                yaml_url['ws-opts']['headers'] = {'Host':vmess_json['peer']}
                            elif vmess_json.get('host'):
                                yaml_url['ws-opts']['headers'] = {'Host':vmess_json['host']}
                            else:
                                yaml_url['ws-opts']['headers'] = {'Host':vmess_json['add']}


                        yaml_url['udp'] = True

                        url_list.append(yaml_url)
                except Exception as err:
                    print(f'yaml_encode 解析 vmess 节点发生错误: {err}')
                    pass

            if  re.match(r'(^ss://)', line):
                try:
                    node_tent = line[5:]
                    proxy_str = sub_convert.safe_decode(node_tent)
                    if proxy_str.find('server') > 0 or node_tent.find('port') > 0:
                        ss_json = json.loads(proxy_str)
                    else:
                        flags = dict()
                        param = node_tent
                        if param.find('#') > -1:
                            flags['name'] = sub_convert.safe_unquote(param[param.find('#') + 1:])
                            param = param[:param.find('#')]
                            param = sub_convert.safe_decode(param) if '@' not in param else param

                        if param.find('?') > -1:
                            plugin = sub_convert.safe_unquote(param[param.find('?') + 1:])
                            param = re.match(r'(.*?)(?=\?|/\?)',param).group(1)
                            param = sub_convert.safe_decode(param) if '@' not in param else param
                            for p in plugin.split(';'):
                                key_value = p.split('=')
                                flags[key_value[0]]=sub_convert.safe_decode(key_value[1])

                        if param.find('@') > -1:
                            param_a = sub_convert.safe_decode(re.match(r'(.*)@',param).group(1))
                            param = re.sub(r'.*@',param_a+'@',param)
                            matcher = re.match(r'(.*?):(.*)@(.*):(.*)$', param)
                            if matcher:
                                flags['method'] = matcher.group(1)
                                flags['password'] = matcher.group(2)
                                flags['server'] = matcher.group(3)
                                flags['port'] = matcher.group(4)
                            ss_json = flags
                        else:
                            print(f'ss节点解析失败,链接:  {line}')

                        nodname = ss_json.get('name') or ss_json.get('remarks') or 'ss_node'

                        yaml_url.setdefault('name', nodname)
                        yaml_url.setdefault('server', ss_json.get('server'))
                        yaml_url.setdefault('port', ss_json.get('port'))
                        yaml_url.setdefault('type', 'ss')
                        yaml_url.setdefault('cipher', ss_json.get('method'))
                        yaml_url.setdefault('password', ss_json.get('password'))


                        if ss_json.get('plugin'):
                            yaml_url['plugin'] = 'obfs' if 'obfs' in ss_json['plugin'] else ss_json['plugin']
                        if ss_json.get('obfs'):
                            yaml_url['plugin-opts'] = {}
                            yaml_url['plugin-opts']['mode'] = ss_json['obfs']
                        if ss_json.get('obfs-host'):
                            yaml_url['plugin-opts']['host'] = ss_json['obfs-host']
                        if ss_json.get('obfs-uri'):
                            yaml_url['plugin-opts']['uri'] = ss_json['obfs-uri']

                        yaml_url.setdefault('udp',True)

                        url_list.append(yaml_url)
                except Exception as err:
                    print(f'yaml_encode 解析 ss 节点发生错误: {err}')
                    pass

            if 'ssr://' in line:
                try:
                    node_tent = line[6:]
                    proxy_str = sub_convert.safe_decode(node_tent)
                    if proxy_str.find('server') > 0 or node_tent.find('port') > 0:
                        ssr_json = json.loads(proxy_str)
                    else:
                        flags = dict()
                        parts = proxy_str.split(':')
                        if len(parts) != 6:
                            print('该ssr节点解析失败，链接:{}\n=={}'.format(node,parts))
                            continue
                        flags = {
                            'server': parts[0],
                            'port': parts[1],
                            'protocol': parts[2],
                            'method': parts[3],
                            'obfs': parts[4]
                        }
                        password_params = parts[5].split('/?')
                        flags['password'] = sub_convert.safe_decode(password_params[0])
                        params = sub_convert.safe_unquote(password_params[1])
                        params = params.split('&')
                        for p in params:
                            key_value = re.search(r'(.*?)=(.*$)',p)
                            flags[key_value.group(1)] = sub_convert.safe_decode(key_value.group(2))

                        ssr_json = flags


                        yaml_url = {
                            'name':ssr_json.get('remarks').strip() if ssr_json.get('remarks') else 'ssr_node',
                            'type':'ssr',
                            'server':ssr_json.get('server'),
                            'port':int(ssr_json.get('port')),
                            'cipher':ssr_json.get('method'),
                            'password':ssr_json.get('password'),
                            'obfs':ssr_json.get('obfs'),
                            'protocol':ssr_json.get('protocol'),
                            'obfs-param':ssr_json.get('obfsparam'),
                            'protocol-param':ssr_json.get('protoparam'),
                            'udp':True
                        }
                        for key in list(yaml_url.keys()):
                            if yaml_url.get(key) is None:
                                del yaml_url[key]


                        url_list.append(yaml_url)
                except Exception as err:
                    print(f'yaml_encode 解析 ssr 节点发生错误: {err}')
                    pass

            if 'trojan://' in line:
                try:
                    node_tent = line[9:]
                    proxy_str = sub_convert.safe_decode(node_tent)
                    if proxy_str.find('server') > 0 or node_tent.find('port') > 0:
                        yaml_url = json.loads(proxy_str)
                    else: 
                        part_list = re.split('#', node_tent, maxsplit=1) # https://www.runoob.com/python/att-string-split.html
                        yaml_url.setdefault('name', urllib.parse.unquote(part_list[1]))
                        server_part = part_list[0]
                        server_part_list = re.split(r':|@|\?|&', server_part) # 使用多个分隔符 https://blog.csdn.net/shidamowang/article/details/80254476 https://zhuanlan.zhihu.com/p/92287240
                        yaml_url.setdefault('server', server_part_list[1])
                        yaml_url.setdefault('port', server_part_list[2])
                        yaml_url.setdefault('type', 'trojan')
                        yaml_url.setdefault('password', server_part_list[0])
                        server_part_list = server_part_list[3:]

                        for config in server_part_list:
                            if 'sni=' in config or 'peer' in config:
                                yaml_url.setdefault('sni', config[4:])
                            elif 'allowInsecure=' in config or 'tls=' in config:
                                if config[-1] == 0:
                                    yaml_url.setdefault('tls', False)
                            elif 'type=' in config:
                                if config[5:] != 'tcp':
                                    yaml_url.setdefault('network', config[5:])
                            elif 'path=' in config:
                                yaml_url.setdefault('ws-path', config[5:])
                            elif 'security=' in config:
                                if config[9:] != 'tls':
                                    yaml_url.setdefault('tls', False)

                        yaml_url.setdefault('skip-cert-verify', False)
                        yaml_url.setdefault('udp', True)

                        url_list.append(yaml_url)
                except Exception as err:
                    print(f'yaml_encode 解析 trojan 节点发生错误: {err}')
                    pass

        yaml_content_dic = {'proxies': url_list}
        yaml_content_raw = yaml.dump(yaml_content_dic, default_flow_style=False, sort_keys=False, allow_unicode=True, width=750, indent=2)
        yaml_content = sub_convert.format(yaml_content_raw)
        return yaml_content

    def yaml_decode(url_content): # YAML 文本转换为 URL 链接内容
        
        try:
            if isinstance(url_content, dict):
                sub_content = url_content
            else:
                if 'proxies:' in url_content:
                    sub_content = sub_convert.format(url_content)
                else:
                    yaml_content_raw = sub_convert.convert(url_content, 'content', 'YAML')
                    sub_content = yaml.safe_load(yaml_content_raw)
            proxies_list = sub_content['proxies']

            protocol_url = []
            for index in range(len(proxies_list)): # 不同节点订阅链接内容 https://github.com/hoochanlon/fq-book/blob/master/docs/append/srvurl.md
                proxy = proxies_list[index]

                if proxy['type'] == 'vmess': # Vmess 节点提取, 由 Vmess 所有参数 dump JSON 后 base64 得来。

                    yaml_default_config = {
                        'name': 'Vmess Node', 'server': '0.0.0.0', 'port': 0, 'uuid': '', 'alterId': 0,
                        'cipher': 'auto', 'network': 'ws', 'ws-headers': {'Host': proxy['server']},
                        'ws-path': '/', 'tls': '', 'sni': ''
                    }

                    yaml_default_config.update(proxy)
                    proxy_config = yaml_default_config

                    vmess_value = {
                        'v': 2, 'ps': proxy_config['name'], 'add': proxy_config['server'],
                        'port': proxy_config['port'], 'id': proxy_config['uuid'], 'aid': proxy_config['alterId'],
                        'scy': proxy_config['cipher'], 'net': proxy_config['network'], 'type': None, 'host': proxy_config['ws-headers']['Host'],
                        'path': proxy_config['ws-path'], 'tls': proxy_config['tls'], 'sni': proxy_config['sni']
                        }

                    vmess_raw_proxy = json.dumps(vmess_value, sort_keys=False, indent=2, ensure_ascii=False)
                    vmess_proxy = str('vmess://' + sub_convert.base64_encode(vmess_raw_proxy) + '\n')
                    protocol_url.append(vmess_proxy)

                elif proxy['type'] == 'ss': # SS 节点提取, 由 ss_base64_decoded 部分(参数: 'cipher', 'password', 'server', 'port') Base64 编码后 加 # 加注释(URL_encode) 
                    ss_base64_decoded = str(proxy['cipher']) + ':' + str(proxy['password']) + '@' + str(proxy['server']) + ':' + str(proxy['port'])
                    ss_base64 = sub_convert.base64_encode(ss_base64_decoded)
                    ss_proxy = str('ss://' + ss_base64 + '#' + str(urllib.parse.quote(proxy['name'])) + '\n')
                    protocol_url.append(ss_proxy)

                elif proxy['type'] == 'trojan': # Trojan 节点提取, 由 trojan_proxy 中参数再加上 # 加注释(URL_encode) # trojan Go https://p4gefau1t.github.io/trojan-go/developer/url/
                    if 'tls' in proxy.keys() and 'network' in proxy.keys():
                        if proxy['tls'] == True and proxy['network'] != 'tcp':
                            network_type = proxy['network']
                            trojan_go = f'?security=tls&type={network_type}&headerType=none'
                        elif proxy['tls'] == False and proxy['network'] != 'tcp':
                            trojan_go = f'??allowInsecure=0&type={network_type}&headerType=none'
                    else:
                        trojan_go = '?allowInsecure=1'
                    if 'sni' in proxy.keys():
                        trojan_go = trojan_go+'&sni='+proxy['sni']
                    trojan_proxy = str('trojan://' + str(proxy['password']) + '@' + str(proxy['server']) + ':' + str(proxy['port']) + trojan_go + '#' + str(urllib.parse.quote(proxy['name'])) + '\n')
                    protocol_url.append(trojan_proxy)

                # elif proxy['type'] == 'ssr':
                #     ssr_base64_decoded = str(proxy['server']) + ':' + str(proxy['port']) + ':' + str(proxy['protocol']) 
                #     ssr_base64_decoded = ssr_base64_decoded + ':' + str(proxy['cipher']) + ':' + str(proxy['obfs']) + ':' + str(sub_convert.base64_encode(proxy['password'])) + '/?'
                #     protocol_url.append(ssr_proxy)

            yaml_content = ''.join(protocol_url)
            return yaml_content
        except Exception as err:
            print(f'yaml decode 发生 {err} 错误')
            return '订阅内容解析错误'

    def base64_encode(url_content): # 将 URL 内容转换为 Base64
        base64_content = base64.b64encode(url_content.encode('utf-8')).decode('ascii')
        return base64_content
    def base64_decode(url_content): # Base64 转换为 URL 链接内容
        if '-' in url_content:
            url_content = url_content.replace('-', '+')
        elif '_' in url_content:
            url_content = url_content.replace('_', '/')
        #print(len(url_content))
        missing_padding = len(url_content) % 4
        if missing_padding != 0:
            url_content += '='*(4 - missing_padding) # 不是4的倍数后加= https://www.cnblogs.com/wswang/p/7717997.html
        try:
            base64_content = base64.b64decode(url_content.encode('utf-8')).decode('utf-8','ignore') # https://www.codenong.com/42339876/
            return base64_content
        except UnicodeDecodeError:
            base64_content = base64.b64decode(url_content)
            return base64_content

    def safe_unquote(s):
        while s != requests.utils.unquote(s):
            s = requests.utils.unquote(s)
        return s
    # 针对url的base64解码
    def safe_decode(s):
        ori = s
        try:
            s = s + '=' * (4 - len(s) % 4) if len(s) % 4 else s
            s = base64.urlsafe_b64decode(s).decode()
        except Exception as er:
            s = ori
        return s

    def convert_remote(url='', output_type='clash', host='http://127.0.0.1:25500'): #{url='订阅链接', output_type={'clash': 输出 Clash 配置, 'base64': 输出 Base64 配置, 'url': 输出 url 配置}, host='远程订阅转化服务地址'}
        # 使用远程订阅转换服务，输出相应配置。
        sever_host = host
        url = urllib.parse.quote(url, safe='') # https://docs.python.org/zh-cn/3/library/urllib.parse.html
        if output_type == 'clash':
            converted_url = sever_host+'/sub?target=clash&url='+url+'&insert=false&emoji=true&list=true'
            try:
                resp = requests.get(converted_url)
            except Exception as err:
                print(err)
                return 'Url 解析错误'
            if resp.text == 'No nodes were found!':
                sub_content = 'Url 解析错误'
            else:
                sub_content = sub_convert.makeup(sub_convert.format(resp.text), dup_rm_enabled=False, format_name_enabled=True)
        elif output_type == 'base64':
            converted_url = sever_host+'/sub?target=mixed&url='+url+'&insert=false&emoji=true&list=true'
            try:
                resp = requests.get(converted_url)
            except Exception as err:
                print(err)
                return 'Url 解析错误'
            if resp.text == 'No nodes were found!':
                sub_content = 'Url 解析错误'
            else:
                sub_content = sub_convert.base64_encode(resp.text)
        elif output_type == 'url':
            converted_url = sever_host+'/sub?target=mixed&url='+url+'&insert=false&emoji=true&list=true'
            try:
                resp = requests.get(converted_url)
            except Exception as err:
                print(err)
                return 'Url 解析错误'
            if resp.text == 'No nodes were found!':
                sub_content = 'Url 解析错误'
            else:
                sub_content = resp.text

        return sub_content


hdtop = '''log-level: silent
mode: global
port: 23940
external-controller: 127.0.0.1:23941
'''

clashmodel = {'port': 7890, 'socks-port': 7891, 'mode': 'rule', 'log-level': 'silent', 'external-controller': '127.0.0.1:9090', 
         'proxies': [],
         'proxy-groups': [{'name': 'Proxy', 'type': 'select', 'proxies': ['♻️ automatic']}, {'name': '♻️ automatic', 'type': 'url-test', 'proxies': [], 'url': 'https://www.google.com/favicon.ico', 'interval': 300}],
         'rules': ['DOMAIN,safebrowsing.urlsec.qq.com,DIRECT', 'DOMAIN,safebrowsing.googleapis.com,DIRECT',
                   'DOMAIN,developer.apple.com,Proxy', 'DOMAIN-SUFFIX,digicert.com,Proxy',
                   'DOMAIN,ocsp.apple.com,Proxy', 'DOMAIN,ocsp.comodoca.com,Proxy',
                   'DOMAIN,ocsp.usertrust.com,Proxy', 'DOMAIN,ocsp.sectigo.com,Proxy',
                   'DOMAIN,ocsp.verisign.net,Proxy', 'DOMAIN-SUFFIX,apple-dns.net,Proxy',
                   'DOMAIN,testflight.apple.com,Proxy', 'DOMAIN,sandbox.itunes.apple.com,Proxy',
                   'DOMAIN,itunes.apple.com,Proxy', 'DOMAIN-SUFFIX,apps.apple.com,Proxy',
                   'DOMAIN-SUFFIX,blobstore.apple.com,Proxy', 'DOMAIN,cvws.icloud-content.com,Proxy',
                   'DOMAIN-SUFFIX,mzstatic.com,DIRECT', 'DOMAIN-SUFFIX,itunes.apple.com,DIRECT',
                   'DOMAIN-SUFFIX,icloud.com,DIRECT', 'DOMAIN-SUFFIX,icloud-content.com,DIRECT',
                   'DOMAIN-SUFFIX,me.com,DIRECT', 'DOMAIN-SUFFIX,aaplimg.com,DIRECT',
                   'DOMAIN-SUFFIX,cdn20.com,DIRECT', 'DOMAIN-SUFFIX,cdn-apple.com,DIRECT',
                   'DOMAIN-SUFFIX,akadns.net,DIRECT', 'DOMAIN-SUFFIX,akamaiedge.net,DIRECT',
                   'DOMAIN-SUFFIX,edgekey.net,DIRECT', 'DOMAIN-SUFFIX,mwcloudcdn.com,DIRECT',
                   'DOMAIN-SUFFIX,mwcname.com,DIRECT', 'DOMAIN-SUFFIX,apple.com,DIRECT',
                   'DOMAIN-SUFFIX,apple-cloudkit.com,DIRECT', 'DOMAIN-SUFFIX,apple-mapkit.com,DIRECT',
                   'DOMAIN-SUFFIX,cn,DIRECT', 'DOMAIN-KEYWORD,-cn,DIRECT', 'DOMAIN-SUFFIX,126.com,DIRECT',
                   'DOMAIN-SUFFIX,126.net,DIRECT', 'DOMAIN-SUFFIX,127.net,DIRECT', 'DOMAIN-SUFFIX,163.com,DIRECT',
                   'DOMAIN-SUFFIX,360buyimg.com,DIRECT', 'DOMAIN-SUFFIX,36kr.com,DIRECT',
                   'DOMAIN-SUFFIX,acfun.tv,DIRECT', 'DOMAIN-SUFFIX,air-matters.com,DIRECT',
                   'DOMAIN-SUFFIX,aixifan.com,DIRECT', 'DOMAIN-KEYWORD,alicdn,DIRECT',
                   'DOMAIN-KEYWORD,alipay,DIRECT', 'DOMAIN-KEYWORD,taobao,DIRECT', 'DOMAIN-SUFFIX,amap.com,DIRECT',
                   'DOMAIN-SUFFIX,autonavi.com,DIRECT', 'DOMAIN-KEYWORD,baidu,DIRECT',
                   'DOMAIN-SUFFIX,bdimg.com,DIRECT', 'DOMAIN-SUFFIX,bdstatic.com,DIRECT',
                   'DOMAIN-SUFFIX,bilibili.com,DIRECT', 'DOMAIN-SUFFIX,bilivideo.com,DIRECT',
                   'DOMAIN-SUFFIX,caiyunapp.com,DIRECT', 'DOMAIN-SUFFIX,clouddn.com,DIRECT',
                   'DOMAIN-SUFFIX,cnbeta.com,DIRECT', 'DOMAIN-SUFFIX,cnbetacdn.com,DIRECT',
                   'DOMAIN-SUFFIX,cootekservice.com,DIRECT', 'DOMAIN-SUFFIX,csdn.net,DIRECT',
                   'DOMAIN-SUFFIX,ctrip.com,DIRECT', 'DOMAIN-SUFFIX,dgtle.com,DIRECT',
                   'DOMAIN-SUFFIX,dianping.com,DIRECT', 'DOMAIN-SUFFIX,douban.com,DIRECT',
                   'DOMAIN-SUFFIX,doubanio.com,DIRECT', 'DOMAIN-SUFFIX,duokan.com,DIRECT',
                   'DOMAIN-SUFFIX,easou.com,DIRECT', 'DOMAIN-SUFFIX,ele.me,DIRECT', 'DOMAIN-SUFFIX,feng.com,DIRECT',
                   'DOMAIN-SUFFIX,fir.im,DIRECT', 'DOMAIN-SUFFIX,frdic.com,DIRECT',
                   'DOMAIN-SUFFIX,g-cores.com,DIRECT', 'DOMAIN-SUFFIX,godic.net,DIRECT',
                   'DOMAIN-SUFFIX,gtimg.com,DIRECT', 'DOMAIN,cdn.hockeyapp.net,DIRECT',
                   'DOMAIN-SUFFIX,hongxiu.com,DIRECT', 'DOMAIN-SUFFIX,hxcdn.net,DIRECT',
                   'DOMAIN-SUFFIX,iciba.com,DIRECT', 'DOMAIN-SUFFIX,ifeng.com,DIRECT',
                   'DOMAIN-SUFFIX,ifengimg.com,DIRECT', 'DOMAIN-SUFFIX,ipip.net,DIRECT',
                   'DOMAIN-SUFFIX,iqiyi.com,DIRECT', 'DOMAIN-SUFFIX,jd.com,DIRECT',
                   'DOMAIN-SUFFIX,jianshu.com,DIRECT', 'DOMAIN-SUFFIX,knewone.com,DIRECT',
                   'DOMAIN-SUFFIX,le.com,DIRECT', 'DOMAIN-SUFFIX,lecloud.com,DIRECT',
                   'DOMAIN-SUFFIX,lemicp.com,DIRECT', 'DOMAIN-SUFFIX,licdn.com,DIRECT',
                   'DOMAIN-SUFFIX,luoo.net,DIRECT', 'DOMAIN-SUFFIX,meituan.com,DIRECT',
                   'DOMAIN-SUFFIX,meituan.net,DIRECT', 'DOMAIN-SUFFIX,mi.com,DIRECT',
                   'DOMAIN-SUFFIX,miaopai.com,DIRECT', 'DOMAIN-SUFFIX,microsoft.com,DIRECT',
                   'DOMAIN-SUFFIX,microsoftonline.com,DIRECT', 'DOMAIN-SUFFIX,miui.com,DIRECT',
                   'DOMAIN-SUFFIX,miwifi.com,DIRECT', 'DOMAIN-SUFFIX,mob.com,DIRECT',
                   'DOMAIN-SUFFIX,netease.com,DIRECT', 'DOMAIN-SUFFIX,office.com,DIRECT',
                   'DOMAIN-SUFFIX,office365.com,DIRECT', 'DOMAIN-KEYWORD,officecdn,DIRECT',
                   'DOMAIN-SUFFIX,oschina.net,DIRECT', 'DOMAIN-SUFFIX,ppsimg.com,DIRECT',
                   'DOMAIN-SUFFIX,pstatp.com,DIRECT', 'DOMAIN-SUFFIX,qcloud.com,DIRECT',
                   'DOMAIN-SUFFIX,qdaily.com,DIRECT', 'DOMAIN-SUFFIX,qdmm.com,DIRECT',
                   'DOMAIN-SUFFIX,qhimg.com,DIRECT', 'DOMAIN-SUFFIX,qhres.com,DIRECT',
                   'DOMAIN-SUFFIX,qidian.com,DIRECT', 'DOMAIN-SUFFIX,qihucdn.com,DIRECT',
                   'DOMAIN-SUFFIX,qiniu.com,DIRECT', 'DOMAIN-SUFFIX,qiniucdn.com,DIRECT',
                   'DOMAIN-SUFFIX,qiyipic.com,DIRECT', 'DOMAIN-SUFFIX,qq.com,DIRECT',
                   'DOMAIN-SUFFIX,qqurl.com,DIRECT', 'DOMAIN-SUFFIX,rarbg.to,DIRECT',
                   'DOMAIN-SUFFIX,ruguoapp.com,DIRECT', 'DOMAIN-SUFFIX,segmentfault.com,DIRECT',
                   'DOMAIN-SUFFIX,sinaapp.com,DIRECT', 'DOMAIN-SUFFIX,smzdm.com,DIRECT',
                   'DOMAIN-SUFFIX,snapdrop.net,DIRECT', 'DOMAIN-SUFFIX,sogou.com,DIRECT',
                   'DOMAIN-SUFFIX,sogoucdn.com,DIRECT', 'DOMAIN-SUFFIX,sohu.com,DIRECT',
                   'DOMAIN-SUFFIX,soku.com,DIRECT', 'DOMAIN-SUFFIX,speedtest.net,Proxy',
                   'DOMAIN-SUFFIX,sspai.com,DIRECT', 'DOMAIN-SUFFIX,suning.com,DIRECT',
                   'DOMAIN-SUFFIX,taobao.com,DIRECT', 'DOMAIN-SUFFIX,tencent.com,DIRECT',
                   'DOMAIN-SUFFIX,tenpay.com,DIRECT', 'DOMAIN-SUFFIX,tianyancha.com,DIRECT',
                   'DOMAIN-SUFFIX,tmall.com,DIRECT', 'DOMAIN-SUFFIX,tudou.com,DIRECT',
                   'DOMAIN-SUFFIX,umetrip.com,DIRECT', 'DOMAIN-SUFFIX,upaiyun.com,DIRECT',
                   'DOMAIN-SUFFIX,upyun.com,DIRECT', 'DOMAIN-SUFFIX,veryzhun.com,DIRECT',
                   'DOMAIN-SUFFIX,weather.com,DIRECT', 'DOMAIN-SUFFIX,weibo.com,DIRECT',
                   'DOMAIN-SUFFIX,xiami.com,DIRECT', 'DOMAIN-SUFFIX,xiami.net,DIRECT',
                   'DOMAIN-SUFFIX,xiaomicp.com,DIRECT', 'DOMAIN-SUFFIX,ximalaya.com,DIRECT',
                   'DOMAIN-SUFFIX,xmcdn.com,DIRECT', 'DOMAIN-SUFFIX,xunlei.com,DIRECT',
                   'DOMAIN-SUFFIX,yhd.com,DIRECT', 'DOMAIN-SUFFIX,yihaodianimg.com,DIRECT',
                   'DOMAIN-SUFFIX,yinxiang.com,DIRECT', 'DOMAIN-SUFFIX,ykimg.com,DIRECT',
                   'DOMAIN-SUFFIX,youdao.com,DIRECT', 'DOMAIN-SUFFIX,youku.com,DIRECT',
                   'DOMAIN-SUFFIX,zealer.com,DIRECT', 'DOMAIN-SUFFIX,zhihu.com,DIRECT',
                   'DOMAIN-SUFFIX,zhimg.com,DIRECT', 'DOMAIN-SUFFIX,zimuzu.tv,DIRECT',
                   'DOMAIN-SUFFIX,zoho.com,DIRECT', 'DOMAIN-KEYWORD,amazon,Proxy', 'DOMAIN-KEYWORD,google,Proxy',
                   'DOMAIN-KEYWORD,gmail,Proxy', 'DOMAIN-KEYWORD,youtube,Proxy', 'DOMAIN-KEYWORD,facebook,Proxy',
                   'DOMAIN-SUFFIX,fb.me,Proxy', 'DOMAIN-SUFFIX,fbcdn.net,Proxy', 'DOMAIN-KEYWORD,twitter,Proxy',
                   'DOMAIN-KEYWORD,instagram,Proxy', 'DOMAIN-KEYWORD,dropbox,Proxy',
                   'DOMAIN-SUFFIX,twimg.com,Proxy', 'DOMAIN-KEYWORD,blogspot,Proxy', 'DOMAIN-SUFFIX,youtu.be,Proxy',
                   'DOMAIN-KEYWORD,whatsapp,Proxy', 'DOMAIN-KEYWORD,admarvel,REJECT',
                   'DOMAIN-KEYWORD,admaster,REJECT', 'DOMAIN-KEYWORD,adsage,REJECT',
                   'DOMAIN-KEYWORD,adsmogo,REJECT', 'DOMAIN-KEYWORD,adsrvmedia,REJECT',
                   'DOMAIN-KEYWORD,adwords,REJECT', 'DOMAIN-KEYWORD,adservice,REJECT',
                   'DOMAIN-SUFFIX,appsflyer.com,REJECT', 'DOMAIN-KEYWORD,domob,REJECT',
                   'DOMAIN-SUFFIX,doubleclick.net,REJECT', 'DOMAIN-KEYWORD,duomeng,REJECT',
                   'DOMAIN-KEYWORD,dwtrack,REJECT', 'DOMAIN-KEYWORD,guanggao,REJECT',
                   'DOMAIN-KEYWORD,lianmeng,REJECT', 'DOMAIN-SUFFIX,mmstat.com,REJECT',
                   'DOMAIN-KEYWORD,mopub,REJECT', 'DOMAIN-KEYWORD,omgmta,REJECT', 'DOMAIN-KEYWORD,openx,REJECT',
                   'DOMAIN-KEYWORD,partnerad,REJECT', 'DOMAIN-KEYWORD,pingfore,REJECT',
                   'DOMAIN-KEYWORD,supersonicads,REJECT', 'DOMAIN-KEYWORD,uedas,REJECT',
                   'DOMAIN-KEYWORD,umeng,REJECT', 'DOMAIN-KEYWORD,usage,REJECT', 'DOMAIN-SUFFIX,vungle.com,REJECT',
                   'DOMAIN-KEYWORD,wlmonitor,REJECT', 'DOMAIN-KEYWORD,zjtoolbar,REJECT',
                   'DOMAIN-SUFFIX,9to5mac.com,Proxy', 'DOMAIN-SUFFIX,abpchina.org,Proxy',
                   'DOMAIN-SUFFIX,adblockplus.org,Proxy', 'DOMAIN-SUFFIX,adobe.com,Proxy',
                   'DOMAIN-SUFFIX,akamaized.net,Proxy', 'DOMAIN-SUFFIX,alfredapp.com,Proxy',
                   'DOMAIN-SUFFIX,amplitude.com,Proxy', 'DOMAIN-SUFFIX,ampproject.org,Proxy',
                   'DOMAIN-SUFFIX,android.com,Proxy', 'DOMAIN-SUFFIX,angularjs.org,Proxy',
                   'DOMAIN-SUFFIX,aolcdn.com,Proxy', 'DOMAIN-SUFFIX,apkpure.com,Proxy',
                   'DOMAIN-SUFFIX,appledaily.com,Proxy', 'DOMAIN-SUFFIX,appshopper.com,Proxy',
                   'DOMAIN-SUFFIX,appspot.com,Proxy', 'DOMAIN-SUFFIX,arcgis.com,Proxy',
                   'DOMAIN-SUFFIX,archive.org,Proxy', 'DOMAIN-SUFFIX,armorgames.com,Proxy',
                   'DOMAIN-SUFFIX,aspnetcdn.com,Proxy', 'DOMAIN-SUFFIX,att.com,Proxy',
                   'DOMAIN-SUFFIX,awsstatic.com,Proxy', 'DOMAIN-SUFFIX,azureedge.net,Proxy',
                   'DOMAIN-SUFFIX,azurewebsites.net,Proxy', 'DOMAIN-SUFFIX,bing.com,Proxy',
                   'DOMAIN-SUFFIX,bintray.com,Proxy', 'DOMAIN-SUFFIX,bit.com,Proxy', 'DOMAIN-SUFFIX,bit.ly,Proxy',
                   'DOMAIN-SUFFIX,bitbucket.org,Proxy', 'DOMAIN-SUFFIX,bjango.com,Proxy',
                   'DOMAIN-SUFFIX,bkrtx.com,Proxy', 'DOMAIN-SUFFIX,blog.com,Proxy',
                   'DOMAIN-SUFFIX,blogcdn.com,Proxy', 'DOMAIN-SUFFIX,blogger.com,Proxy',
                   'DOMAIN-SUFFIX,blogsmithmedia.com,Proxy', 'DOMAIN-SUFFIX,blogspot.com,Proxy',
                   'DOMAIN-SUFFIX,blogspot.hk,Proxy', 'DOMAIN-SUFFIX,bloomberg.com,Proxy',
                   'DOMAIN-SUFFIX,box.com,Proxy', 'DOMAIN-SUFFIX,box.net,Proxy', 'DOMAIN-SUFFIX,cachefly.net,Proxy',
                   'DOMAIN-SUFFIX,chromium.org,Proxy', 'DOMAIN-SUFFIX,cl.ly,Proxy',
                   'DOMAIN-SUFFIX,cloudflare.com,Proxy', 'DOMAIN-SUFFIX,cloudfront.net,Proxy',
                   'DOMAIN-SUFFIX,cloudmagic.com,Proxy', 'DOMAIN-SUFFIX,cmail19.com,Proxy',
                   'DOMAIN-SUFFIX,cnet.com,Proxy', 'DOMAIN-SUFFIX,cocoapods.org,Proxy',
                   'DOMAIN-SUFFIX,comodoca.com,Proxy', 'DOMAIN-SUFFIX,crashlytics.com,Proxy',
                   'DOMAIN-SUFFIX,culturedcode.com,Proxy', 'DOMAIN-SUFFIX,d.pr,Proxy',
                   'DOMAIN-SUFFIX,danilo.to,Proxy', 'DOMAIN-SUFFIX,dayone.me,Proxy', 'DOMAIN-SUFFIX,db.tt,Proxy',
                   'DOMAIN-SUFFIX,deskconnect.com,Proxy', 'DOMAIN-SUFFIX,disq.us,Proxy',
                   'DOMAIN-SUFFIX,disqus.com,Proxy', 'DOMAIN-SUFFIX,disquscdn.com,Proxy',
                   'DOMAIN-SUFFIX,dnsimple.com,Proxy', 'DOMAIN-SUFFIX,docker.com,Proxy',
                   'DOMAIN-SUFFIX,dribbble.com,Proxy', 'DOMAIN-SUFFIX,droplr.com,Proxy',
                   'DOMAIN-SUFFIX,duckduckgo.com,Proxy', 'DOMAIN-SUFFIX,dueapp.com,Proxy',
                   'DOMAIN-SUFFIX,dytt8.net,Proxy', 'DOMAIN-SUFFIX,edgecastcdn.net,Proxy',
                   'DOMAIN-SUFFIX,edgekey.net,Proxy', 'DOMAIN-SUFFIX,edgesuite.net,Proxy',
                   'DOMAIN-SUFFIX,engadget.com,Proxy', 'DOMAIN-SUFFIX,entrust.net,Proxy',
                   'DOMAIN-SUFFIX,eurekavpt.com,Proxy', 'DOMAIN-SUFFIX,evernote.com,Proxy',
                   'DOMAIN-SUFFIX,fabric.io,Proxy', 'DOMAIN-SUFFIX,fast.com,Proxy',
                   'DOMAIN-SUFFIX,fastly.net,Proxy', 'DOMAIN-SUFFIX,fc2.com,Proxy',
                   'DOMAIN-SUFFIX,feedburner.com,Proxy', 'DOMAIN-SUFFIX,feedly.com,Proxy',
                   'DOMAIN-SUFFIX,feedsportal.com,Proxy', 'DOMAIN-SUFFIX,fiftythree.com,Proxy',
                   'DOMAIN-SUFFIX,firebaseio.com,Proxy', 'DOMAIN-SUFFIX,flexibits.com,Proxy',
                   'DOMAIN-SUFFIX,flickr.com,Proxy', 'DOMAIN-SUFFIX,flipboard.com,Proxy',
                   'DOMAIN-SUFFIX,g.co,Proxy', 'DOMAIN-SUFFIX,gabia.net,Proxy', 'DOMAIN-SUFFIX,geni.us,Proxy',
                   'DOMAIN-SUFFIX,gfx.ms,Proxy', 'DOMAIN-SUFFIX,ggpht.com,Proxy',
                   'DOMAIN-SUFFIX,ghostnoteapp.com,Proxy', 'DOMAIN-SUFFIX,git.io,Proxy',
                   'DOMAIN-KEYWORD,github,Proxy', 'DOMAIN-SUFFIX,globalsign.com,Proxy',
                   'DOMAIN-SUFFIX,gmodules.com,Proxy', 'DOMAIN-SUFFIX,godaddy.com,Proxy',
                   'DOMAIN-SUFFIX,golang.org,Proxy', 'DOMAIN-SUFFIX,gongm.in,Proxy', 'DOMAIN-SUFFIX,goo.gl,Proxy',
                   'DOMAIN-SUFFIX,goodreaders.com,Proxy', 'DOMAIN-SUFFIX,goodreads.com,Proxy',
                   'DOMAIN-SUFFIX,gravatar.com,Proxy', 'DOMAIN-SUFFIX,gstatic.com,Proxy',
                   'DOMAIN-SUFFIX,gvt0.com,Proxy', 'DOMAIN-SUFFIX,hockeyapp.net,Proxy',
                   'DOMAIN-SUFFIX,hotmail.com,Proxy', 'DOMAIN-SUFFIX,icons8.com,Proxy',
                   'DOMAIN-SUFFIX,ifixit.com,Proxy', 'DOMAIN-SUFFIX,ift.tt,Proxy', 'DOMAIN-SUFFIX,ifttt.com,Proxy',
                   'DOMAIN-SUFFIX,iherb.com,Proxy', 'DOMAIN-SUFFIX,imageshack.us,Proxy',
                   'DOMAIN-SUFFIX,img.ly,Proxy', 'DOMAIN-SUFFIX,imgur.com,Proxy', 'DOMAIN-SUFFIX,imore.com,Proxy',
                   'DOMAIN-SUFFIX,instapaper.com,Proxy', 'DOMAIN-SUFFIX,ipn.li,Proxy', 'DOMAIN-SUFFIX,is.gd,Proxy',
                   'DOMAIN-SUFFIX,issuu.com,Proxy', 'DOMAIN-SUFFIX,itgonglun.com,Proxy',
                   'DOMAIN-SUFFIX,itun.es,Proxy', 'DOMAIN-SUFFIX,ixquick.com,Proxy', 'DOMAIN-SUFFIX,j.mp,Proxy',
                   'DOMAIN-SUFFIX,js.revsci.net,Proxy', 'DOMAIN-SUFFIX,jshint.com,Proxy',
                   'DOMAIN-SUFFIX,jtvnw.net,Proxy', 'DOMAIN-SUFFIX,justgetflux.com,Proxy',
                   'DOMAIN-SUFFIX,kat.cr,Proxy', 'DOMAIN-SUFFIX,klip.me,Proxy', 'DOMAIN-SUFFIX,libsyn.com,Proxy',
                   'DOMAIN-SUFFIX,linkedin.com,Proxy', 'DOMAIN-SUFFIX,linode.com,Proxy',
                   'DOMAIN-SUFFIX,lithium.com,Proxy', 'DOMAIN-SUFFIX,littlehj.com,Proxy',
                   'DOMAIN-SUFFIX,live.com,Proxy', 'DOMAIN-SUFFIX,live.net,Proxy',
                   'DOMAIN-SUFFIX,livefilestore.com,Proxy', 'DOMAIN-SUFFIX,llnwd.net,Proxy',
                   'DOMAIN-SUFFIX,macid.co,Proxy', 'DOMAIN-SUFFIX,macromedia.com,Proxy',
                   'DOMAIN-SUFFIX,macrumors.com,Proxy', 'DOMAIN-SUFFIX,mashable.com,Proxy',
                   'DOMAIN-SUFFIX,mathjax.org,Proxy', 'DOMAIN-SUFFIX,medium.com,Proxy',
                   'DOMAIN-SUFFIX,mega.co.nz,Proxy', 'DOMAIN-SUFFIX,mega.nz,Proxy',
                   'DOMAIN-SUFFIX,megaupload.com,Proxy', 'DOMAIN-SUFFIX,microsofttranslator.com,Proxy',
                   'DOMAIN-SUFFIX,mindnode.com,Proxy', 'DOMAIN-SUFFIX,mobile01.com,Proxy',
                   'DOMAIN-SUFFIX,modmyi.com,Proxy', 'DOMAIN-SUFFIX,msedge.net,Proxy',
                   'DOMAIN-SUFFIX,myfontastic.com,Proxy', 'DOMAIN-SUFFIX,name.com,Proxy',
                   'DOMAIN-SUFFIX,nextmedia.com,Proxy', 'DOMAIN-SUFFIX,nsstatic.net,Proxy',
                   'DOMAIN-SUFFIX,nssurge.com,Proxy', 'DOMAIN-SUFFIX,nyt.com,Proxy',
                   'DOMAIN-SUFFIX,nytimes.com,Proxy', 'DOMAIN-SUFFIX,omnigroup.com,Proxy',
                   'DOMAIN-SUFFIX,onedrive.com,Proxy', 'DOMAIN-SUFFIX,onenote.com,Proxy',
                   'DOMAIN-SUFFIX,ooyala.com,Proxy', 'DOMAIN-SUFFIX,openvpn.net,Proxy',
                   'DOMAIN-SUFFIX,openwrt.org,Proxy', 'DOMAIN-SUFFIX,orkut.com,Proxy',
                   'DOMAIN-SUFFIX,osxdaily.com,Proxy', 'DOMAIN-SUFFIX,outlook.com,Proxy',
                   'DOMAIN-SUFFIX,ow.ly,Proxy', 'DOMAIN-SUFFIX,paddleapi.com,Proxy',
                   'DOMAIN-SUFFIX,parallels.com,Proxy', 'DOMAIN-SUFFIX,parse.com,Proxy',
                   'DOMAIN-SUFFIX,pdfexpert.com,Proxy', 'DOMAIN-SUFFIX,periscope.tv,Proxy',
                   'DOMAIN-SUFFIX,pinboard.in,Proxy', 'DOMAIN-SUFFIX,pinterest.com,Proxy',
                   'DOMAIN-SUFFIX,pixelmator.com,Proxy', 'DOMAIN-SUFFIX,pixiv.net,Proxy',
                   'DOMAIN-SUFFIX,playpcesor.com,Proxy', 'DOMAIN-SUFFIX,playstation.com,Proxy',
                   'DOMAIN-SUFFIX,playstation.com.hk,Proxy', 'DOMAIN-SUFFIX,playstation.net,Proxy',
                   'DOMAIN-SUFFIX,playstationnetwork.com,Proxy', 'DOMAIN-SUFFIX,pushwoosh.com,Proxy',
                   'DOMAIN-SUFFIX,rime.im,Proxy', 'DOMAIN-SUFFIX,servebom.com,Proxy', 'DOMAIN-SUFFIX,sfx.ms,Proxy',
                   'DOMAIN-SUFFIX,shadowsocks.org,Proxy', 'DOMAIN-SUFFIX,sharethis.com,Proxy',
                   'DOMAIN-SUFFIX,shazam.com,Proxy', 'DOMAIN-SUFFIX,skype.com,Proxy',
                   'DOMAIN-SUFFIX,smartdnsProxy.com,Proxy', 'DOMAIN-SUFFIX,smartmailcloud.com,Proxy',
                   'DOMAIN-SUFFIX,sndcdn.com,Proxy', 'DOMAIN-SUFFIX,sony.com,Proxy',
                   'DOMAIN-SUFFIX,soundcloud.com,Proxy', 'DOMAIN-SUFFIX,sourceforge.net,Proxy',
                   'DOMAIN-SUFFIX,spotify.com,Proxy', 'DOMAIN-SUFFIX,squarespace.com,Proxy',
                   'DOMAIN-SUFFIX,sstatic.net,Proxy', 'DOMAIN-SUFFIX,st.luluku.pw,Proxy',
                   'DOMAIN-SUFFIX,stackoverflow.com,Proxy', 'DOMAIN-SUFFIX,startpage.com,Proxy',
                   'DOMAIN-SUFFIX,staticflickr.com,Proxy', 'DOMAIN-SUFFIX,steamcommunity.com,Proxy',
                   'DOMAIN-SUFFIX,symauth.com,Proxy', 'DOMAIN-SUFFIX,symcb.com,Proxy',
                   'DOMAIN-SUFFIX,symcd.com,Proxy', 'DOMAIN-SUFFIX,tapbots.com,Proxy',
                   'DOMAIN-SUFFIX,tapbots.net,Proxy', 'DOMAIN-SUFFIX,tdesktop.com,Proxy',
                   'DOMAIN-SUFFIX,techcrunch.com,Proxy', 'DOMAIN-SUFFIX,techsmith.com,Proxy',
                   'DOMAIN-SUFFIX,thepiratebay.org,Proxy', 'DOMAIN-SUFFIX,theverge.com,Proxy',
                   'DOMAIN-SUFFIX,time.com,Proxy', 'DOMAIN-SUFFIX,timeinc.net,Proxy', 'DOMAIN-SUFFIX,tiny.cc,Proxy',
                   'DOMAIN-SUFFIX,tinypic.com,Proxy', 'DOMAIN-SUFFIX,tmblr.co,Proxy',
                   'DOMAIN-SUFFIX,todoist.com,Proxy', 'DOMAIN-SUFFIX,trello.com,Proxy',
                   'DOMAIN-SUFFIX,trustasiassl.com,Proxy', 'DOMAIN-SUFFIX,tumblr.co,Proxy',
                   'DOMAIN-SUFFIX,tumblr.com,Proxy', 'DOMAIN-SUFFIX,tweetdeck.com,Proxy',
                   'DOMAIN-SUFFIX,tweetmarker.net,Proxy', 'DOMAIN-SUFFIX,twitch.tv,Proxy',
                   'DOMAIN-SUFFIX,txmblr.com,Proxy', 'DOMAIN-SUFFIX,typekit.net,Proxy',
                   'DOMAIN-SUFFIX,ubertags.com,Proxy', 'DOMAIN-SUFFIX,ublock.org,Proxy',
                   'DOMAIN-SUFFIX,ubnt.com,Proxy', 'DOMAIN-SUFFIX,ulyssesapp.com,Proxy',
                   'DOMAIN-SUFFIX,urchin.com,Proxy', 'DOMAIN-SUFFIX,usertrust.com,Proxy',
                   'DOMAIN-SUFFIX,v.gd,Proxy', 'DOMAIN-SUFFIX,v2ex.com,Proxy', 'DOMAIN-SUFFIX,vimeo.com,Proxy',
                   'DOMAIN-SUFFIX,vimeocdn.com,Proxy', 'DOMAIN-SUFFIX,vine.co,Proxy',
                   'DOMAIN-SUFFIX,vivaldi.com,Proxy', 'DOMAIN-SUFFIX,vox-cdn.com,Proxy',
                   'DOMAIN-SUFFIX,vsco.co,Proxy', 'DOMAIN-SUFFIX,vultr.com,Proxy', 'DOMAIN-SUFFIX,w.org,Proxy',
                   'DOMAIN-SUFFIX,w3schools.com,Proxy', 'DOMAIN-SUFFIX,webtype.com,Proxy',
                   'DOMAIN-SUFFIX,wikiwand.com,Proxy', 'DOMAIN-SUFFIX,wikileaks.org,Proxy',
                   'DOMAIN-SUFFIX,wikimedia.org,Proxy', 'DOMAIN-SUFFIX,wikipedia.com,Proxy',
                   'DOMAIN-SUFFIX,wikipedia.org,Proxy', 'DOMAIN-SUFFIX,windows.com,Proxy',
                   'DOMAIN-SUFFIX,windows.net,Proxy', 'DOMAIN-SUFFIX,wire.com,Proxy',
                   'DOMAIN-SUFFIX,wordpress.com,Proxy', 'DOMAIN-SUFFIX,workflowy.com,Proxy',
                   'DOMAIN-SUFFIX,wp.com,Proxy', 'DOMAIN-SUFFIX,wsj.com,Proxy', 'DOMAIN-SUFFIX,wsj.net,Proxy',
                   'DOMAIN-SUFFIX,xda-developers.com,Proxy', 'DOMAIN-SUFFIX,xeeno.com,Proxy',
                   'DOMAIN-SUFFIX,xiti.com,Proxy', 'DOMAIN-SUFFIX,yahoo.com,Proxy', 'DOMAIN-SUFFIX,yimg.com,Proxy',
                   'DOMAIN-SUFFIX,ying.com,Proxy', 'DOMAIN-SUFFIX,yoyo.org,Proxy', 'DOMAIN-SUFFIX,ytimg.com,Proxy',
                   'DOMAIN-SUFFIX,telegra.ph,Proxy', 'DOMAIN-SUFFIX,telegram.org,Proxy',
                   'IP-CIDR,91.108.4.0/22,Proxy', 'IP-CIDR,91.108.8.0/21,Proxy', 'IP-CIDR,91.108.16.0/22,Proxy',
                   'IP-CIDR,91.108.56.0/22,Proxy', 'IP-CIDR,149.154.160.0/20,Proxy',
                   'IP-CIDR6,2001:67c:4e8::/48,Proxy', 'IP-CIDR6,2001:b28:f23d::/48,Proxy',
                   'IP-CIDR6,2001:b28:f23f::/48,Proxy', 'DOMAIN,injections.adguard.org,DIRECT',
                   'DOMAIN,local.adguard.org,DIRECT', 'DOMAIN-SUFFIX,local,DIRECT', 'IP-CIDR,127.0.0.0/8,DIRECT',
                   'IP-CIDR,172.16.0.0/12,DIRECT', 'IP-CIDR,192.168.0.0/16,DIRECT', 'IP-CIDR,10.0.0.0/8,DIRECT',
                   'IP-CIDR,17.0.0.0/8,DIRECT', 'IP-CIDR,100.64.0.0/10,DIRECT', 'IP-CIDR,224.0.0.0/4,DIRECT',
                   'IP-CIDR6,fe80::/10,DIRECT', 'GEOIP,CN,DIRECT', 'MATCH,Proxy']}





if __name__ == '__main__':

    subs = ['https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2',
            'https://gitlab.com/xlzlucky/bpjd/-/raw/main/freejd',
            'https://raw.githubusercontent.com/Lewis-1217/FreeNodes/main/bpjzx2',
            'https://raw.githubusercontent.com/poduv/poduv/i/long',
            'https://raw.githubusercontent.com/Jsnzkpg/Jsnzkpg/Jsnzkpg/Jsnzkpg',
            'https://raw.githubusercontent.com/freefq/free/master/v2',
            'https://raw.githubusercontent.com/mzcorleone/clash/main/node-all.yaml']

    filname = ['aibox','xluck','lewis','poduv','jszk','frfq','corle',]
    for i in range(len(subs)):
        content = sub_convert.convert(subs[i], 'url', 'YAML')
        if not os.path.exists('./subs'):
            os.mkdir('subs')
        file = open(f'./subs/{filname[i]}.yaml', 'w', encoding= 'utf-8')
        file.write(content)
        file.close()
        print(f'Writing content to temp.working.yaml\n')













