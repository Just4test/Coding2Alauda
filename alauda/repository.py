from .apibase import APIBase, APISimpleDataBase
from .build import Build

class TagConfig(APIBase):
    
    _aliasmap = {
        'image_tag': 'docker_repo_tag',
        'branch_or_tag_name': 'code_repo_type_value'
    }
    
    _hideset = {'docker_repo_tag', 'code_repo_type_value', 'code_repo_type'}
        
    @property
    def is_breach(self):
        '指定是分支还是标签。前者返回True，后者返回False'
        return self.data['code_repo_type'] == 'branch'
       
    @property 
    def code_branch(self):
        return self.branch_or_tag_name if self.is_breach else None
            
    @property 
    def code_tag(self):
        return self.branch_or_tag_name if not self.is_breach else None
    
    @staticmethod
    def create(image_tag, code_branch = None, code_tag = None, 
    branch_or_tag_name = None, is_breach = None, build_context_path = '/', dockerfile_location = '/', 
    is_active = False, build_cache_enabled = False, version_tagging = 0):
        '''
        根据参数创建一个TagConfig
        可以指定 branch_or_tag_name 和 is_breach；
        或者指定 code_branch、code_tag之一。
        '''
        if code_branch:
            if code_tag or branch_or_tag_name:
                raise Exception('code_branch、code_tag、branch_or_tag_name 不能同时使用')
            branch_or_tag_name = code_branch
            is_breach = True
        elif code_tag:
            if branch_or_tag_name:
                raise Exception('code_branch、code_tag、branch_or_tag_name 不能同时使用')
            branch_or_tag_name = code_tag
            is_breach = False
            
        if branch_or_tag_name is None:
            raise Exception('必须指定三者之一：code_branch、code_tag、branch_or_tag_name')
            
        if dockerfile_location.find(build_context_path) != 0:
            raise Exception('dockerfile_location 必须以 build_context_path 作为前缀')
            
        
        data = {
            'docker_repo_tag': image_tag,
            'code_repo_type': 'branch' if is_breach else 'tag',
            'code_repo_type_value': branch_or_tag_name,
            'build_context_path': build_context_path,
            'dockerfile_location': dockerfile_location,
            'is_active': is_active,
            'build_cache_enabled': build_cache_enabled,
            'version_tagging': version_tagging,
        }
        
        return TagConfig(data)

class BuildConfig(APIBase):
    
    _aliasmap = {
    }
    
    _hideset = {}
        
    def _update_attributes(self, data):
        self.tag_configs = []
        for c in data['tag_configs']:
            self.tag_configs.append(TagConfig(c))
        
    @property
    def use_cn_node(self):
        return self.build_node == 'cn'
    
    @staticmethod
    def create_client(client, namespace, name, tagconfig,
    use_cn_node = False, email_enabled = False):
        '''
        创建已绑定的代码托管服务的BuildConfig。
        client: 代码托管服务，可选择GitHub, Bitbucket, OSChina, GitCafe
        namespace: 服务的用户名/组织名
        name: 仓库名
        '''
        if isinstance(tagconfig, TagConfig):
            tagconfig = [tagconfig]
        
        data = {
            'code_repo_client': client,
            'code_repo_namespace': namespace,
            'code_repo_name': name,
            'build_node': 'cn' if use_cn_node else 'in',
            'email_enabled': email_enabled,
            'tag_configs': [i.json_data for i in tagconfig]
        }
        
        return BuildConfig(data)
        
    @staticmethod
    def create_simple(url, tagconfig, use_cn_node = False, email_enabled = False):
        '根据版本仓库url创建BuildConfig'
        if isinstance(tagconfig, TagConfig):
            tagconfig = [tagconfig]
        
        data = {
            'code_repo_client': 'Simple',
            'code_repo_clone_url': url,
            'build_node': 'cn' if use_cn_node else 'in',
            'email_enabled': email_enabled,
            'tag_configs': [i.json_data for i in tagconfig]
        }
        
        return BuildConfig(data)

class Repository(APISimpleDataBase):
    
    _aliasmap = {
        'name':'repo_name',
        'build_config_':'build_config'
    }
    
    _hideset = {'service_name'}
    
    @classmethod
    def format_url(cls, alauda, name, url = ''):
        return '/v1/repositories/{namespace}/{name}/{url}'.format(
            name = name, url = url, namespace = alauda.namespace)
            
    @classmethod
    def create(cls, alauda, name, description, 
    is_public = False, build_config = None, full_description = ''):
        data = {
            'repo_name': name,
            'description': description,
            'namespace': alauda.namespace,
            'is_public': is_public
        }
        if build_config:
            data['build_config'] = build_config.json_data
            data['full_description'] = full_description
        
        print(__import__('json').dumps(data))
        r = alauda._request_helper('/v1/repositories/{namespace}', 'post', data)
        if r.status_code == 201:
            return Repository(alauda, r.json())
        else:
            raise Exception('发生了异常：\n{}\n{}'.format(r.status_code, r.text))
    
    @classmethod
    def get_data_by_name(cls, alauda, name):
        r = alauda._request_helper(cls.format_url(alauda, name), 'get')
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 404:
            return None
        else:
            raise Exception('发生了异常：\n{}\n{}'.format(r.status_code, r.text))
            
    @classmethod
    def get(cls, alauda, name):
        data = cls.get_data_by_name(alauda, name)
        if data is None:
            return None
        return cls(alauda, data)
    
    @classmethod
    def list(cls, alauda):
        url = '/v1/repositories/{namespace}'
        r = alauda._request_helper(url, 'get')
        
        if 200 == r.status_code:
            ret = []
            for data in r.json()['results']:
                ret.append(cls(alauda, data, True))
            return ret
        else:
            raise Exception('发生了异常：\n{}\n{}'.format(r.status_code, r.text))
        
    
    def __init__(self, alauda, data, is_simple = False):
        self._alauda = alauda
        self._build_config = None
        super().__init__(data, is_simple)
        
        
    def _get_full(self):
        return self.get_data_by_name(self._alauda, self.name)
        
    @property
    def api_url(self):
        return self.format_url(self._alauda, self.name)
        
    @property
    def url(self):
        '返回镜像仓库路径'
        url = self._alauda.urlbase.replace('https://api', 'index')
        url = '{}/{}/{}'.format(url, self._alauda.namespace, self.name)
        return url
        
    @property
    def build_config(self):
        if not self.is_automated:
            return None
        if self._build_config is None:
            if self._is_simple:
                self._json_data = self._get_full()
                self._is_simple = True
            self._build_config = BuildConfig(self.build_config_)
        return self._build_config
        
    def __repr__(self):
        return '<Repository [{}]>'.format(self.name)
        
    def delete(self):
        r = self._alauda._request_helper(self.format_url(self._alauda, self.name), 'delete')
        if r.status_code == 204:
            return True
        else:
            raise Exception('发生了异常：\n{}\n{}'.format(r.status_code, r.text))
        
    def build(self, tag = None, code_commit_id = None):
        '仅构建仓库可以使用此方法。仅当只有一个标签的时候可以省略标签。'
        build_config = self.build_config
        if build_config is None:
            raise Exception('当前仓库不是一个构建仓库')
        if tag is None:
            if len(build_config.tag_configs) == 1:
                tag = build_config.tag_configs[0].image_tag
            else:
                raise Exception('当前仓库具有超过一个构建标签，请显示指定构建标签。')
        
        url = '/v1/builds'
        data = {
            'namespace': self._alauda.namespace,
            'repo_name': self.name,
            'tag': tag
        }
        if code_commit_id is not None:
            data['code_commit_id'] = code_commit_id
        r = self._alauda._request_helper(url, 'post', data)
        if r.status_code == 201:
            return Build(self._alauda, r.json())
        else:
            raise Exception('发生了异常：\n{}\n{}'.format(r.status_code, r.text))
        
