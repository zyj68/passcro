import requests,os,time


hdrs = {'User-Agent':'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Mobile Safari/537.36',}
url = 'https://raw.githubusercontent.com/pojiezhiyuanjun/freev2/master/'+time.strftime('%m%d')+'clash.yml'

def pjzy(url):

    try:
        rsp = requests.get(url,headers = hdrs)
        yamltent = rsp.text.replace('(油管:破解资源君2.0)','')
        dirs = './subscribe'
        if not os.path.exists(dirs):
            os.makedirs(dirs)
        with open(dirs + '/' + 'pjzy.yaml', 'w', encoding='utf-8') as f:
            f.write(yamltent)         
    except Exception:
        pass

if __name__ == '__main__':

    pjzy(url)
