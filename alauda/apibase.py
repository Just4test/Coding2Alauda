import json
'''
参考自 https://github.com/sigmavirus24/github3.py/blob/develop/github3/models.py
'''
class APIBase(object):
    '用于映射JSON API对象的基类'
    
    _aliasmap = {}
    '''
    别名映射表
    如果令 _aliasmap['attr'] = 'other'，则：
    访问 apibase.attr 返回 apibase._json_data['other']
    访问 apibase.other 也会返回 apibase._json_data['other']
    如果令 _aliasmap['attr'] = ['lv1','lv2']，则：
    访问 apibase.attr 返回 apibase._json_data['lv1']['lv2']
    '''
    
    _hideset = set()
    '''
    属性隐藏表
    如果 'attr' in _hideset，则：
    访问 apibase.attr 不会返回 apibase._json_data['attr']
    '''
    
    def __init__(self, data):
        if isinstance(data, str):
            data = json.loads(data)
        self._update_attributes(data)
        self._json_data = data
        self.__dir_cache__ = None
        
    def _update_attributes(self, data):
        '子类的初始化更新方法'
        pass
        
    @property
    def json_data(self):
        '返回原始json对象'
        return self._json_data
        
    def __getattr__(self, attribute):
        '令json对象的属性可以直接访问'
        if attribute in self._aliasmap:
            attribute = self._aliasmap[attribute]
            if not isinstance(attribute, list):
                attribute = [attribute]
            temp = self._json_data
            for key in attribute:
                if key in temp:
                    temp = temp[key]
                else:
                    raise AttributeError(attribute)
            return temp
                
        if attribute not in self._hideset and attribute in self._json_data:
            return self._json_data[attribute]
        else:
            print('发生错误', attribute, self._json_data)
            raise AttributeError(attribute)
    
    def __dir__(self):
        '令dir命令枚举属性时包含json对象的属性'
        def _in(attribute):
            if isinstance(attribute, list):
                temp = self._json_data
                for key in attribute:
                    if key in temp:
                        temp = temp[key]
                    else:
                        return False
                return True
            else:
                return attribute in self._json_data
                
        if self._json_data is None:
            return super().__dir__()
        if self.__dir_cache__ is None:
            # 排除隐藏的属性
            datakeys = set(self._json_data.keys())
            temp =  datakeys - self._hideset
            # 添加属性别名
            temp |= {k for k, v in self._aliasmap.items() if _in(v)} 
            temp |= set(super().__dir__())
            self.__dir_cache__ = list(temp)
        return self.__dir_cache__


class APILiteBase(APIBase):
    '''
    在使用RESTful API时，可以获取单个对象或对象列表。
    有时，对象列表中的对象相比单个对象来说仅具有一部分关键信息。
    APILiteBase类可以使用该关键信息创建代理。
    访问代理具有的关键信息时，代理直接返回；
    当访问代理中没有的属性或方法时，代理先请求数据对象的完整版本，然后将请求转发给该完整版本
    '''
    _full_data = None
    
    def _get_full(self):
        '实现此方法以获取数据对象的完整版本'
        pass
        
    def __dir__(self):
        if self._full_data is None:
            self._full_data = self._get_full()
        return dir(self._full_data)
    
    def __getattr__(self, attribute):
        if self._full_data is not None:
            return getattr(self._full_data, attribute)
        try:
            return super().__getattr__(attribute)
        except AttributeError:
            self._full_data = self._get_full()
            return getattr(self._full_data, attribute)
            
class APISimpleDataBase(APIBase):
    '''
    允许传入简化版json数据。
    当持有简化版数据，且访问了该数据中不存在的字段时，
    首先请求完整数据，然后返回完整数据中的对应字段。
    '''
    
    def _get_full(self):
        '实现此方法以获取数据对象的完整版本'
        pass
    
    def __init__(self, data, is_simple = False):
        self._is_simple = is_simple
        super().__init__(data)
        
    def __dir__(self):
        if self._is_simple:
            self._json_data = self._get_full()
            self._is_simple = True
        return super().__dir__()
    
    def __getattr__(self, attribute):
        if self._is_simple:
            try:
                return super().__getattr__(attribute)
            except AttributeError:
                self._json_data = self._get_full()
                self._is_simple = True
            
        return super().__getattr__(attribute)
                
            