# 漫画下载 & PDF阅读器

基于 jmcomic 的漫画下载工具，提供命令行和 Web 两种使用方式，支持下载后自动加密 PDF。

## 项目结构

```
├── test.py                 # CLI 脚本（输入ID → 下载 → 加密）
├── jm_api.py               # Flask API 后端（端口 5000）
├── option.yml              # jmcomic 下载配置
├── jm_web/
│   ├── server.js           # Express 前端服务（端口 3000）
│   ├── package.json
│   └── public/
│       └── index.html      # Web 操作界面
└── jm/                     # 下载输出目录（gitignore）
```

## 功能

- **漫画下载** — 通过 jmcomic 库按专辑 ID 下载漫画，自动合成为 PDF
- **PDF 加密** — 下载完成后自动对 PDF 加密，密码为专辑 ID
- **Web 界面** — 浏览器可视化操作，支持下载、预览、列表管理
- **命令行模式** — 直接运行 `test.py` 输入 ID 即可下载

## 依赖安装

```bash
# Python 依赖
pip install flask PyPDF2 jmcomic img2pdf

# Node.js 依赖
cd jm_web && npm install && cd ..
```

## 使用方式

### 方式一：Web 界面（推荐）

```bash
# 终端1 - 启动 Python API
python jm_api.py          # 运行在 http://localhost:5000

# 终端2 - 启动 Web 前端
cd jm_web && node server.js   # 运行在 http://localhost:3000
```

浏览器打开 `http://localhost:3000`，输入漫画 ID 即可下载。

### 方式二：命令行

```bash
python test.py
# 输入漫画专辑 ID，自动下载并生成加密 PDF
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/get-pdf-list | 获取已下载 PDF 列表 |
| POST | /api/download | 下载漫画（body: `{"album_id": 123}`） |
| GET | /api/view-pdf?filename= | 在线预览 PDF |
| GET | /api/download-pdf?filename= | 下载 PDF 文件 |
| GET | /health | Python API 健康检查 |

## 配置说明

`option.yml` 主要配置项：

```yaml
download:
  cache: true          # 已下载文件跳过重复下载
  image:
    decode: true       # 还原 JM 混淆图片
    suffix: .jpg       # 图片统一转为 JPG
  threading:
    image: 30          # 图片并发下载数
    photo: 16          # 章节并发下载数

plugins:
  after_photo:
    - plugin: img2pdf  # 章节图片合并为 PDF
      kwargs:
        pdf_dir: ./jm  # PDF 输出目录
```

## 数据流

```
浏览器 (Web UI)
    → Express (jm_web/server.js)
        → Flask API (jm_api.py)
            → jmcomic 库 → 下载图片
            → img2pdf 插件 → 合成 PDF
            → PyPDF2 → 加密 PDF
                → 输出到 jm/ 目录
```

## 注意事项

1. 下载内容仅供个人学习使用，请遵守相关法律法规
2. 需要 Python 和 Node.js 环境
3. 下载速度受线程配置和网络环境影响
4. 加密密码为专辑 ID，可在 `test.py` 中自定义

## License

MIT
