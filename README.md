# <img width=30 src="assets/bgm-icon.jpg"> Calibre-web Bangumi 元数据插件 🧩

![platform](https://img.shields.io/badge/platform-Windows_|_Macos_|_Linux-blue)
![GitHub - License](https://img.shields.io/github/license/JeffersonQin/calibre-web-bgm)

## ✨ Features

* **支持 Bangumi 的元数据检索**
* **支持 NSFW 内容检索**
* **支持漫画 / 小说的主条目检索**
* **支持漫画 / 轻小说的单行本条目检索**
* **目前支持的元数据种类: 标题、简介、作者、发行日期、评分、标签、Bangumi ID、ISBN 书号**

## 📸 Screenshots

**主界面截图**

<div align="center">
  <img width=600 src="assets/overall.png">
</div>

**单行本**

<div align="center">
  <img width=600 src="assets/single.png">
</div>

## 🏗️ 安装

将 [`bgm.py`](./bgm.py) 复制到 `calibre-web` 项目的 `cps/metadata_provider` 目录下即可。

## 🔨 环境变量

* `BGM_ACCESS_TOKEN`: Bangumi API 访问令牌，用于检索 NSFW 内容。获取令牌方式：https://next.bgm.tv/demo/access-token
* `META_PROVIDER_BGM_THREAD_POOL`: 线程池大小，默认为 8
* `META_PROVIDER_BGM_TAG_LOWEST_USER_CNT`: 对于每个标签的最低用户标记数，低于此值的标签将被过滤，默认为 5
* `META_PROVIDER_BGM_TAG_MAX_CNT`: 每个条目的最大标签数，默认为 10

如果不会设置环境变量可以直接修改 `bgm.py` 中的默认值。

## 💡 Future

* **一个 `calibre-web` fork 正在~~火热~~开发中，将全面支持基于 Bangumi 的进度管理**
