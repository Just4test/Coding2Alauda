from .apibase import APIBase, APISimpleDataBase

class BuildLog(APIBase):
    pass

class Build(APIBase):
    
    _aliasmap = {
        'image_tag': 'docker_repo_tag',
        'branch_or_tag_name': 'code_repo_type_value',
        'id': 'build_id'
    }
    
    _hideset = {'docker_repo_tag', 'code_repo_type_value', 'code_repo_type', 'build_id'}
    
    def __init__(self, alauda, data):
        self._alauda = alauda
        super().__init__(data)
        
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
        
    def __repr__(self):
        return '<Build of {}:{} [{}]>'.format(self.docker_repo_path, self.image_tag, self.id)
        
    def logs(self, start_time = None, end_time = None):
        url = '/v1/builds/{}/logs'.format(self.id)
        r = self._alauda._request_helper(url, 'get')
        if r.status_code == 201:
            return r.json()
        else:
            raise Exception('发生了异常：\n{}\n{}'.format(r.status_code, r.text))