import requests
import yaml
import base64
from urllib.parse import quote

subscribe_urls = [
    'https://raw.githubusercontent.com/zhangkaiitugithub/passcro/main/subs/speednodes.yaml',
]

proxies = './subs/chf.txt'
filterDomain = {"fsyy.fosi.hk", 
                "gddx.fosi.hk", 
                "ydgy.fosi.hk", 
                "azsh01.1aba.cn",
                "shcu.1aba.cn",
                "azbj01.1aba.cn"
                }

def get_sharelinks(subscribe_urls):
    share_links = []
    for index ,subscribe_url in enumerate(subscribe_urls):
        return_content = requests.get(subscribe_url).text
        with open("./subs/subscripe_" + str(index) + '.yaml', 'w') as f: f.write(return_content)
        yaml_content = yaml.safe_load(return_content)
        for proxy in yaml_content['proxies']:
            if proxy['server'] in filterDomain:
                share_links.append(clash2v2ray(proxy))
    return share_links

def create_ssrurl():
    """
    VPN(ShadowsocksR)配置:
    Host/ip(服务器)          :   www.baidu.com
    Port(远程端口)           :   123
    password(密码)           :   baidu123
    method(加密方式)         :   none
    protocol(协议)           :   origin
    protocol_param(协议参数) :   baidu:123
    obfs(混淆)               :   plain
    obfs_param(混淆参数)     :   baidu:321
    remarks(备注)            :   办公
    group(群组名)            :   baidu
    参数如无，可置空 例: group=''
    """
    res = "{ip}:{port}:{protocol}:{method}:{obfs}:{pwdbase64}/?" \
          "obfsparam={obfsparam64}&protoparam={protoparams64}&remarks={remarkbase64}&group={group64}".format(
            ip='www.baidu.com',
            port='123',
            pwdbase64=(base64.b64encode('baidu123'.encode())).decode(),
            method='none',
            protocol='origin',
            protoparams64=(base64.b64encode('baidu:123'.encode())).decode(),
            obfs='plain',
            obfsparam64=(base64.b64encode('baidu:321'.encode())).decode(),
            remarkbase64=(base64.b64encode('办公'.encode())).decode(),
            group64=(base64.b64encode('baidu'.encode())).decode()
            )
    ssrlink = 'ssr://' + str((base64.b64encode(res.encode())).decode())
    return ssrlink

def clash2v2ray(share_link):
    link = ''
    if share_link['type'] == 'vmess':
        link = 'vmess://'
        link += base64.b64encode(bytes(('{"v":"2","ps":"' + share_link['name'].encode('utf-16', 'surrogatepass').decode('utf-16') + '","add":"' + share_link['server'] + '","port":"' + str(
            share_link['port']) + '","id":"' + share_link['uuid'] + '","aid":"' + str(share_link['alterId']) + '","net":"tcp","type":"none","host":"","path":"","tls":""}').encode('utf-8'))).decode('utf-8')
        # TODO
    elif share_link['type'] == 'ss':
        link = 'ss://'
        link += base64.b64encode(bytes(
            (share_link['cipher'] + ':' + share_link['password']).encode('utf-8'))).decode('utf-8')
        link += '@' + share_link['server'] + ':' + str(share_link['port'])
        link += '#' + quote(share_link['name'], 'utf-8')
    elif share_link['type'] == 'trojan':
        link = 'trojan://'
        link += share_link['password']
        link += '@' + share_link['server'] + ':' + str(share_link['port'])
        if 'sni' in share_link:
            sni = share_link['sni']
        else:
            sni = share_link['server']
        link += '?sni=' + sni
        link += '&peer=' + sni
        if 'skip-cert-verify' in share_link.keys():
            link += '&skip-cert-verify=' + \
                ('1' if share_link['skip-cert-verify'] else '0')
        link += '#' + quote(share_link['name'], 'utf-8')
    elif share_link['type'] == 'vless':
        pass
    elif share_link['type'] == 'ssr':
        if 'protocol-param' in share_link:
            res = "{ip}:{port}:{protocol}:{method}:{obfs}:{pwdbase64}/?" \
            "obfsparam={obfsparam64}&protoparam={protoparams64}&remarks={remarkbase64}&group={group64}".format(
                ip=share_link['server'],
                port=share_link['port'],
                pwdbase64=(base64.b64encode(share_link['password'].encode())).decode(),
                method=share_link['cipher'],
                protocol=share_link['protocol'],
                protoparams64=(base64.b64encode(share_link['protocol-param'].encode())).decode(),
                obfs=share_link['obfs'],
                obfsparam64=(base64.b64encode(share_link['obfs-param'].encode())).decode(),
                remarkbase64=(base64.b64encode(share_link['name'].encode())).decode(),
                group64=(base64.b64encode(share_link['name'].encode())).decode()
                )
            link = 'ssr://' + str((base64.b64encode(res.encode())).decode())
    return link + '\n'


links = get_sharelinks(subscribe_urls)
filtered = filter(lambda link: link != '\n', links)

with open(proxies, 'w') as f: f.writelines(filtered)