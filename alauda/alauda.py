import requests
import json

from .service import Service
from .application import Application
from .repository import Repository

class Alauda:
    
    
    urlbase='https://api.alauda.cn'
    
    @staticmethod
    def get_token(username, password, urlbase = None):
        '使用用户名和密码获取Token'
        if urlbase is None:
            urlbase = Alauda.urlbase
            
        r = requests.post(
            url = urlbase + '/v1/generate-api-token',
            headers = {
                'Content-Type': 'application/json',
            },
            data=json.dumps({
                'username': username,
                'password': password
            })
        )
        
        result = json.loads(r.text)
        if 200 == r.status_code:
            return result['token']
        else:
            print('错误，可能是用户名和密码不匹配' + r.text)
            
    def _format_url(self, url):
        return self.urlbase + url.format(namespace = self.namespace)
            
    def _request_helper(self, url, method, data = None, params = None, headers = None, files = None, debug = False):
        '''
        发送请求，将返回值解为json对象
        args:
            - url
            - method http方法
            
        returns:
            - json对象
            - http响应码
        '''
        
        if headers is None:
            headers={}
        headers['Authorization'] = 'Token ' + self.token
        
        if isinstance(data, dict):
            headers['Content-Type'] = 'application/json'
            data = json.dumps(data)
            
        if debug == True:
            r = requests.request(method, 'https://echo.luckymarmot.com/' + self._format_url(url),
                headers = headers, params = params, data = data, files = files);
            filename = str(hash(r))[1:6] + '.html'
            open(filename, 'w').write(r.text)
            print('请求写入了文件：', filename)
            
        # print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        # print(method, self._format_url(url))
        # print(data)
        
        r = requests.request(method, self._format_url(url),
            headers = headers, params = params, data = data, files = files);
        
        return r
    
    def __init__(self, namespace, token, default_region = 'BEIJING1', urlbase = None):
        '''
        args:
            - user 用户名，或者组织名
            - token 灵雀云的API token
            - default_region 默认可用区。在没有提供可用区时使用此可用区。
        '''
        self.namespace = namespace
        self.token = token
        self.default_region = default_region
        if urlbase:
            self.urlbase = urlbase
        
        url = '/v1/auth/{namespace}/profile'
        r = self._request_helper(url, 'get')
        
        if 200 == r.status_code:
            result = r.json()
            if result.get('is_available') is True:
                print('连接成功。上次API使用时间：{}'.format(result.get('api_revoked')))
            else:
                raise Exception('账户尚未激活')
        else:
            raise Exception('账户登入失败。请检查namespace和token是否匹配。')
     
    def create_service(self, config):
        return Service.create(self, config)
        
    def get_service(self, name, app_name = None):
        return Service.get(self, name, app_name)
    
    def list_service(self, app_name = ''):
        if app_name == None:
            app_name = ''
        return Service.list(self, app_name)
        
    def list_all_service(self):
        '列出所有服务，包括应用中的服务'
        return Service.list(self, None)
        
    def delete_service(self, name, app_name = None):
        return Service.delete_service(self, name, app_name)
        
    def create_application(self, name, region = None, yml = None):
        return Application.create(self, name, region, yml)
        
    def get_application(self, name):
        return Application.get(self, name)
        
    def list_application(self):
        return Application.list(self)
    
    def create_repo(self, name, description, is_public = False, build_config = None, full_description = ''):
        return Repository.create(self, name, description, is_public, build_config, full_description)
    
    def get_repo(self, name):
        return Repository.get(self, name)
        
    def list_repo(self):
        return Repository.list(self)