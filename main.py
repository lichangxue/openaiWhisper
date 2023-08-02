import streamlit as st
import openai
import time
import json
import requests
import math
import os
import urllib
from urllib.parse import urljoin, urlparse
import uuid

def file_downloand(image_url):  #######文件下载
    # 文件基准路径
    basedir = os.path.abspath(os.path.dirname(__file__))
    # 下载到服务器的地址
    file_path = os.path.join(basedir, 'downloads')
    # 如果没有这个path则直接创建
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    file_suffix = os.path.splitext(image_url)[1]
    file_name = str(uuid.uuid1())
    filename = '{}\\{}{}'.format(file_path,file_name ,file_suffix)  # 拼接文件名。
    if os.path.exists(filename) == False:  # 判断是否存在文件
        try:
            urllib.request.urlretrieve(image_url, filename=filename)
            # print("成功下载文件")
            return filename
        except IOError as exception_first:  #设置抛出异常
            st.write(exception_first)
            return False
        except Exception as exception_second:  #设置抛出异常
            st.write(exception_second)
            return False
    else:
        st.write("文件已经存在！")
        return False

st.header('音频转文本')
st.header('基于 OpenAI  :blue[Whisper 技术]  :sunglasses:')
st.info('音频识别文本需要耗时较长，请耐心等待', icon="ℹ️")
# 全局变量初始化
if 'type_trans' not in st.session_state:
    st.session_state['type_trans'] = '上传音频'
if 'number_pid' not in st.session_state:
    st.session_state['number_pid'] = '0'
if 'number_rid' not in st.session_state:
    st.session_state['number_rid'] = '0'
if 'type_response' not in st.session_state:
    st.session_state['type_response'] = '输出到页面'
if 'transcribe' not in st.session_state:
    st.session_state['transcribe'] = ''
if 'uploaded_files' not in st.session_state:
    st.session_state['uploaded_files'] = ''

openai.api_key = st.text_input(label='请输入openai Key')
uploaded_files=None
with st.sidebar:
    type_trans = st.radio(
        "使用哪种方式进行音频转文本",
        ('上传音频', '按专辑转换', '按单期转换'))
    st.session_state['type_trans'] = type_trans
    if type_trans == '上传音频':
        uploaded_files = st.file_uploader("选择音频文件，可多选", accept_multiple_files=True,type=['mp3','mp4','mpeg','mpga','m4a','wav','webm'])
        # for uploaded_file in uploaded_files:
            # bytes_data = uploaded_file.read()
            # uploaded_file_New = uploaded_file
            # st.write(uploaded_file)
            # st.session_state['uploaded_files'] = uploaded_file
    elif type_trans == '按专辑转换':
        number_pid = st.number_input('输入专辑ID',help='会把此专辑下的所有开播单期（免费、付费）全部进行转换，会消耗大量时间，关闭页面则停止（慎用！）',step=1)
        st.session_state['number_pid'] = number_pid
        type_response = st.radio(
            "输出方式选择",
            ('输出到页面', '更新到数据库'))
        st.session_state['type_response'] = type_response
    elif type_trans == '按单期转换':
        number_rid = st.number_input('输入单期ID', help='',step=1)
        st.session_state['number_rid'] = number_rid
        type_response = st.radio(
            "输出方式选择",
            ('输出到页面', '更新到数据库'))
        st.session_state['type_response'] = type_response

if st.button('开始识别'):
    if st.session_state['type_trans'] == '上传音频':
        if uploaded_files is None:
            st.error('请上传文件', icon="🚨")
        else:
            for uploaded_file in uploaded_files:
                st.write(uploaded_file)
                data = openai.Audio.transcribe("whisper-1",uploaded_file)
                st.write("识别结果：")
                st.write(data.text)
    elif st.session_state['type_trans'] == '按专辑转换':
        if st.session_state['number_pid'] == '':
            st.error('请输入专辑ID', icon="🚨")
        else:
            pagenum = 1
            url = 'https://d.fm.renbenai.com/fm/read/fmd/android/600/getProgramAudioList.html?pid=%s&pagenum=%d' % (
            st.session_state['number_pid'], pagenum)
            res = requests.get(url)
            # st.write(res.text)
            res = json.loads(res.text)
            # st.write(res['code'])
            resources = []
            if int(res['code']) == 0:
                list = res['data']['list']
                # st.write(list)
                count = int(res['data']['count'])
                for val_ in list:
                    url = urljoin(val_["audiolist"][0]["filePath"], urlparse(val_["audiolist"][0]["filePath"]).path)
                    resources.append({"pid": val_["programId"], "rid": val_["id"], "title": val_["title"],
                                     "filepath": url})
                allPage = math.ceil(count/20)
                st.write(allPage)
                for page in [2,allPage]:
                    _url = 'https://d.fm.renbenai.com/fm/read/fmd/android/600/getProgramAudioList.html?pid=%s&pagenum=%d' % (
                        st.session_state['number_pid'], page)
                    _res = requests.get(_url)
                    _res = json.loads(_res.text)
                    if int(_res['code']) == 0:
                        _list = _res['data']['list']
                        for __val in _list:
                            _url = urljoin(__val["audiolist"][0]["filePath"],
                                          urlparse(__val["audiolist"][0]["filePath"]).path)
                            resources.append({"pid": __val["programId"], "rid": __val["id"], "title": __val["title"],
                                     "filepath": _url})
                # 先下载 再识别
                # st.write(resources)
                for resource in resources:
                    download = file_downloand(resource["filepath"])
                    if download != False:
                        # 开始识别
                        audio_file = open(download, "rb")
                        data = openai.Audio.transcribe("whisper-1", audio_file)
                        st.write("单期：%s 识别结果：" % resource["title"])
                        st.write(data.text)
                        if st.session_state['type_response'] == '更新到数据库':
                            st.write('更新到数据库功能只能在公司内网使用，暂时无法提供服务')
                    else:
                        st.write('下载失败：%s' % resource["title"])








