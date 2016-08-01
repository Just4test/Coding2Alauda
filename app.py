import os
from flask import Flask, Response, redirect, request, g, url_for, render_template, send_file, jsonify, session
import requests
from alauda import *
from hashlib import sha1


ALAUDA_NS = os.environ.get('ALAUDA_NS')
ALAUDA_TOKEN = os.environ.get('ALAUDA_TOKEN')
# CODING_CLIENT_ID = os.environ.get('CODING_CLIENT_ID')
# CODING_CLIENT_SECRET = os.environ.get('CODING_CLIENT_SECRET')
CODING_ACCOUNT = os.environ.get('CODING_ACCOUNT')
CODING_PASSWD = os.environ.get('CODING_PASSWD')

CODING_HOOK_TOKEN = 'fuck'
DEPLOY_KEY_TITLE = 'link_coding_alauda'

# CODING_SCOPE = 'project,project:key,project:depot'
# CODING_ACCESS_TOKEN = None

coding_cookies = None
# coding_git_map = {} #列出用户能控制的coding代码仓库
# alauda_repo_map = {} #列出alauda引用coding的

'''
权限使用方式：
    project 列出仓库
    project:key 添加只读ssh key
    project:depot 添加git push hook
'''
print('========= 登录 =========')
def login_coding(captcha = None):
    url = 'https://coding.net/api/v2/account/login'
    r = requests.post(url, data = {
        'account': CODING_ACCOUNT,
        'password': sha1(CODING_PASSWD.encode('utf-8')).hexdigest(),
        'j_captcha': captcha,
        'remember_me': 'true'
    })
    code = r.json()['code']
    if code == 0:
        global coding_cookies
        coding_cookies = r.cookies
        return 0, None
    
    return code, r.json()['msg']
    
    
code, msg = login_coding()
if code != 0:
    if code == 903:
        print('请访问/login页面，登录需要输入验证码。')
    else:
        print('登录过程中发生了错误：{}'.format(msg))
        exit()
else:
    print('Coding 登录成功！')

alauda = Alauda(ALAUDA_NS, ALAUDA_TOKEN)
print('Alauda 登录成功！')

####################################

def coding_list_git():
    '列出coding git'
    git_map = {}
    url = 'https://coding.net/api/user/projects'
    data = {
        'pageSize': 9999
    }
    r = requests.get(url, data = data, cookies = coding_cookies)
    json = r.json()
    if r.status_code == 200 and json.get('code') == 0:
        for g in json['data']['list']:
            key = g['owner_user_name'] + '/' + g['name']
            git_map[key] = True
    
    return git_map
        
def coding_deploy_hook(owner, git_name, hook_url):
    '在coding git仓库上设置hook'
    # 删除所有指向当前url的hook
    print('检查重复的hook')
    url = 'https://coding.net/api/user/{}/project/{}/git/hooks'.format(owner, git_name)
    r = requests.get(url, cookies = coding_cookies)
    json = r.json()
    if r.status_code == 200 and json.get('code') == 0:
        for h in json['data']:
            if hook_url == h['hook_url']:
                url = 'https://coding.net/api/user/{}/project/{}/git/hook/{}'
                url = url.format(owner, git_name, h['id'])
                r = requests.delete(url, cookies = coding_cookies)
                print('删除hook', r.status_code, r.json())
    
    url = 'https://coding.net/api/user/{}/project/{}/git/hook'.format(owner, git_name)
    data = {
                'hook_url': hook_url,
                'token': CODING_HOOK_TOKEN,
                'type_push': 'true'
            }
    
    r = requests.post(url, cookies = coding_cookies, data = data)
    if r.status_code == 200 and r.json().get('code') == 0:
        return True
    else:
        return False
    
def coding_deploy_key(owner, git_name, key):
    '在coding git仓库上设置部署公钥'
    url = 'https://coding.net/api/user/{}/project/{}/git/deploy_key'.format(owner, git_name)
    data = {
        'title': DEPLOY_KEY_TITLE,
        'content': key,
        'two_factor_code': sha1(CODING_PASSWD.encode('utf-8')).hexdigest()
    }
    r = requests.post(url, data = data, cookies = coding_cookies)
    if r.status_code == 200:
        json = r.json()
        if json['code'] == 0 or json['code'] == 1207:
            return True
    print(r.status_code, r.json())
    return False
    
def coding_git_url_to_path(url):
    '将git仓库url转为coding的owner和name对'
    def check_and_strip(s):
            if url.find(s) == 0:
                return url.lstrip(s).rstrip('.git')
            else:
                return None
    return check_and_strip('https://git.coding.net/') or \
            check_and_strip('git@git.coding.net:')
    
    
#重新关联
def link_all(hook_url):
    git_map = coding_list_git()
    repo_map = {}
    for repo in alauda.list_repo():
        build_config = repo.build_config
        print(repo, build_config, build_config.code_repo_client)
        if not build_config or build_config.code_repo_client != 'Simple':
            continue
        #找到coding的仓库
        url = build_config.code_repo_path
        print(url)
        path = coding_git_url_to_path(url)
        if not path:
            continue
        if path not in git_map:
            print('Alauda 引用了 {}\n但此仓库无法通过给定的Coding账户访问。请检查权限。'.format(url))
            continue
        owner, name = path.split('/')
        print('链接到项目：{}'.format(path))
        if coding_deploy_hook(owner, name, hook_url):
            print('项目{}已连接'.format(path))
        else:
            print('项目{}在连接时出现问题'.format(path))
        if build_config.code_repo_public_key:
            if coding_deploy_key(owner, name, build_config.code_repo_public_key):
                print('部署公钥已就绪')
            else:
                print('创建部署公钥时出现问题')
        if not repo_map.get(path):
            repo_map[path] = []
        repo_map[path].append(repo)
    
    return repo_map

app = Flask(__name__)
app.debug = False

print('必须访问主页才能初始化应用。')

inited = False


@app.route('/')
def index():
    if not coding_cookies:
        return redirect(url_for('login'))
    if not inited:
        return redirect(url_for('refresh'))
    
    return 'Ready'
    

@app.route('/login')
def login():
    return ''

@app.route('/captcha')
def captcha():
    temp = requests.get('https://coding.net/api/getCaptcha')
    ret = Response(temp.content, mimetype = 'image/jpeg')
    return ret


refreshing = False
repo_map = {}
@app.route('/refresh')
def refresh():
    global refreshing, repo_map
    if refreshing:
        return '服务器正在执行刷新操作。请稍等。', 503
    refreshing = True
    hook_url = url_for('hook', _external = True)
    print('==================================')
    print(hook_url)
    print('==================================')
    repo_map = link_all(hook_url)
    refreshing = False
    return 'Job done.'
    

@app.route('/hook', methods = ['POST'])
def hook():
    # print(request.json)
    print(request.data.decode('utf-8'))
    repo_data = request.json.get('repository')
    if not repo_data:
        return 'OK'
    path = coding_git_url_to_path(repo_data['ssh_url'])
    print('{}更新了。'.format(path))
    repos = repo_map.get(path)
    if not repos:
        print('没有找到对应的仓库对象。请刷新。')
        return '', 500
    for repo in repos:
        repo.build()
    return 'OK'

app.run('0.0.0.0', 8080)