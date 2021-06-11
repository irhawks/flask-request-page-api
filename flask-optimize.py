from flask import Flask, request, Response

app = Flask(__name__)

import logging
#logfile = logging.getLogger('file')
#logconsole = logging.getLogger('console')
app.logger.setLevel(logging.INFO)
#app.logger.setLevel(logging.WARN)



#from werkzeug.middleware.profiler import ProfilerMiddleware

#app.config['PROFILE'] = True
#app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])

import requests

import chardet
import json, random

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

RETRY_STRATEGY = Retry(
    total=5,
    backoff_factor=1
)
ADAPTER = HTTPAdapter(max_retries=RETRY_STRATEGY)
CC_HTTP = requests.Session()
CC_HTTP.mount('', ADAPTER)

# ==========================================================================
# Proxy Pool Managers

class DownloadManager(object):

    def __init__(self, endpoint="http://172.17.0.1:55555/random"):
        self.endpoint = endpoint
        #self.registry = 'http://proxy-pool-registry-service/random?type=https&limit=80'
        self.requests = requests.Session()

    def __get_proxies(self, **params):

        """
        返回符合条件的代理列表
        以后还可以扩展，指定anonymity属性，是否允许匿名，是否需要密码等属性信息
        params = {
            'type' : self.type,                # 请求的IP类型     （可选参数，默认为：""）
            'detection' : self.detection,      # 请求的测试网站   （可选参数，默认为：""）
            'limit' : limit                    # 每次获取的IP数   （可选参数，默认为：10）
        }
        """
        #app.logger.info(f"参数是{params}")
        resp = self.requests.get(self.endpoint, params=params).text.split("\r\n")
        return resp

    def get_random_https(self, **params):

        """得到一个随机的https代理"""
        """还可以自己添加一个detection，比如detection=mbalib """

        resp = self.__get_proxies(type="https", limit="80", **params)

        chosen = resp[random.randrange(len(resp))]
        return chosen


    def __download(self, url, use_proxy=True, detection='', **kwargs):

        if use_proxy == True:
            proxies = {'https': 'http://' + self.get_random_https(detection=detection) }
            #app.logger.info(f"选择代理 {proxies}")
        else:
            proxies = {}
            #app.logger.info(f"不使用代理 {proxies}")
        
        try:

            resp = self.requests.get(url, timeout=10, proxies=proxies, verify=False, **kwargs)

            #app.logger.info(f'{url} 响应{resp}')

            # GB2312 is treated as GB18030，原则上都转换成UTF-8的格式
            #enc = chardet.detect(resp.content)['encoding']
            #if enc == 'GB2312':
            #    content = resp.content.decode('GB18030')
            #if enc == 'Windows-1254':
            #    content = resp.content.decode('utf-8')
            #else:
            #    content = resp.content.decode(enc)
            content = resp.content.decode('utf-8') ## 百度百科就是utf-8，不用chardet解析（性能优化）
            
            #app.logger.info(f"返回结果{content}")
            return content, resp.status_code, resp.headers['Content-Type']
        except:
            return '', 404, None

    def download(self, url, num_retries=3, **kwargs):

        """
        kwargs是传递给request的参数
        """
        
        for i in range(0, num_retries+1):

            print("Trying url {} times".format(i+1)) ## 重试次数
            content, status_code, t = self.__download(url, **kwargs)

            print(f"返回结果是{status_code}")
            if status_code != 200:
                continue
            else:
                resp = Response(content)
                resp.headers['Content-Type'] = t
                return resp
        
        return 'Exceed max retries, gave up.', 404, None

    def retry_download(self, url, **kwargs):

        if use_proxy == True:
            proxies = {'https': 'http://' + self.get_random_https(detection=detection) }
        else:
            proxies = {}
        resp = CC_HTTP.get(url, proxies=proxies, verify=False, **kwargs)

        if resp.status_code == 200:
            return resp
        else:
            return 'Exceed max retries, gave up.', 404, None





# ==========================================================================
# TODO: API可能需要重新设计，将所有的下载选项写入到同一接口当中
# 1. 下载一次还是下载多次：retry=0, retry=10, retry=20
# 2. 是否使用百度百科的头文件：site=baidubaike, site=none
# 3. 手动设置超时时间以及requests的一些选项
# 4. 是否使用代理：use_proxy=yes或者use_proxy=no (default, no)

download_manager = DownloadManager()

@app.route('/download', methods=['GET'])
def download():

    # parse arguments
    url = request.args.get("url", default=None, type=str)
    use_proxy = request.args.get("use_proxy", default=False, type=bool)
    num_retries = request.args.get("num_retries", default=2, type=int)
    site_name = request.args.get("site_name", default=None, type=str)
    detection = request.args.get("detection", default="", type=str)

    #app.logger.info(f"代理使用情况 {use_proxy}")
    # check arguments
    if url is None:
        app.logger.warn("Parameter url should not be None")
        return "Error in parsing URL", 404

    #headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    headers = {}
    if site_name == 'baidubaike':
        headers = {
          'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
          'Accept': 'text / html, application / xhtml + xml, application / xml;q = 0.9,image/webp, * / *;q = 0.8'
        }

    # execute a downloading task
    app.logger.info(f"Downloading item from {url}, 使用代理 {use_proxy}")
    
    return download_manager.download(url,
        num_retries=num_retries,
        use_proxy=use_proxy,
        headers=headers,
        detection=detection)

# ==========================================================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5001', debug=True)

