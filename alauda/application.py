from .apibase import APIBase
class Application(APIBase):
    '''
    灵雀云应用
    '''
    
    @classmethod
    def create(cls, alauda, name, region = None, yml = None):
        url = '/v1/applications/{namespace}'
        data = {
           'app_name': name,
           'region': region if region else alauda.default_region,
           'namespace': alauda.namespace,
        }
        if yml:
            data['services'] = yml
            
        r = alauda._request_helper(url, 'post', data = data)
        
        if 201 == r.status_code:
            return cls(alauda, r.json())
        else:
            print(data)
            raise Exception('发生了异常：\n{}\n{}'.format(r.status_code, r.text))
            
    @classmethod
    def get(cls, alauda, name):
        url = '/v1/applications/{namespace}/{name}'.format(
            name = name, namespace = alauda.namespace)
        r = alauda._request_helper(url, 'get')
        
        if 200 == r.status_code:
            return cls(alauda, r.json())
        elif 404 == r.status_code:
            return None
        else:
            raise Exception('发生了异常：\n{}\n{}'.format(r.status_code, r.text))
    
    @classmethod
    def list(cls, alauda):
        '列出应用'
        url = '/v1/application/{namespace}'
        r = alauda._request_helper(url, 'get')
        
        if 200 == r.status_code:
            ret = []
            for data in r.json()['results']:
                ret.append(cls(alauda, data))
            return ret
        else:
            raise Exception('发生了异常：\n{}\n{}'.format(r.status_code, r.text))
       
    
    _aliasmap = {
        'name':'app_name',
    }
    
    _hideset = {'app_name'}
    
    def __init__(self, alauda, data):
        self._alauda = alauda
        super().__init__(data)
    
    def _format_url(self, url = ''):
        return '/v1/applications/{namespace}/{name}/{url}'.format(
            name = self.name, url = url, namespace = self._alauda.namespace)
        
    @property
    def api_url(self):
        return self._format_url()
        
    @property
    def yaml(self):
        url = self._format_url('/yaml')
        r = self._alauda._request_helper(url, 'get')
        if 200 == r.status_code:
            return r.text
        else:
            raise Exception('发生了异常：\n{}\n{}'.format(r.status_code, r.text))
            
    def update(self, yaml):
        files = {'services': yaml}
        r = self._alauda._request_helper(self.api_url, 'put', files = files)
        if 204 == r.status_code:
            return
        else:
            raise Exception('发生了异常：\n{}\n{}'.format(r.status_code, r.text))
            
    def list_service(self):
        return self._alauda.list_service(self.name)
        
    def delete_service(self, name):
        return self._alauda.delete_service(name, self.name)
            
            
    def start(self):
        url = self._format_url('/start')
        r = self._alauda._request_helper(url, 'put')
        if 204 == r.status_code:
            return r.text
        else:
            raise Exception('发生了异常：\n{}\n{}'.format(r.status_code, r.text))
            
    def stop(self):
        url = self._format_url('/start')
        r = self._alauda._request_helper(url, 'put')
        if 204 == r.status_code:
            return r.text
        else:
            raise Exception('发生了异常：\n{}\n{}'.format(r.status_code, r.text))
            
    def delete(self):
        r = self._alauda._request_helper(self.api_url, 'delete')
        if 204 == r.status_code:
            return r.text
        else:
            raise Exception('发生了异常：\n{}\n{}'.format(r.status_code, r.text))
            
    
    
    def __repr__(self):
        return '<Application [{}] in [{}], len[{}]>'.format(self.name, self.region_name, len(self.services))
