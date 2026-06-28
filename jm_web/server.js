const express = require('express');
const axios = require('axios');
const cors = require('cors');
const path = require('path');

// 初始化Express应用
const app = express();
const PORT = 3000;
const PYTHON_API_URL = 'http://localhost:5000/api';

// 跨域配置（仅用cors中间件，无任何*路径）
app.use(cors());

// 解析JSON请求体
app.use(express.json());

// 静态文件服务
app.use(express.static(path.resolve(__dirname, 'public')));

// 根路径返回前端页面
app.get('/', (req, res) => {
  res.sendFile(path.resolve(__dirname, 'public', 'index.html'));
});

// 1. 获取PDF列表接口
app.get('/api/get-pdf-list', async (req, res) => {
  try {
    const response = await axios.get(`${PYTHON_API_URL}/get-pdf-list`, { timeout: 10000 });
    res.json(response.data);
  } catch (error) {
    res.status(500).json({
      success: false,
      msg: `获取PDF列表失败：${error.message}`
    });
  }
});

// 2. 下载漫画接口
app.post('/api/download', async (req, res) => {
  try {
    const response = await axios.post(`${PYTHON_API_URL}/download`, req.body, { timeout: 30000 });
    res.json(response.data);
  } catch (error) {
    res.status(500).json({
      success: false,
      msg: `下载失败：${error.message}`
    });
  }
});

// 3. 预览PDF接口
app.get('/api/view-pdf', async (req, res) => {
  try {
    const response = await axios.get(`${PYTHON_API_URL}/view-pdf`, {
      params: req.query,
      responseType: 'stream',
      timeout: 30000
    });
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `inline; filename=${req.query.filename || 'comic.pdf'}`);
    response.data.pipe(res);
  } catch (error) {
    res.status(500).json({
      success: false,
      msg: `预览失败：${error.message}`
    });
  }
});

// 4. 下载PDF接口
app.get('/api/download-pdf', async (req, res) => {
  try {
    const response = await axios.get(`${PYTHON_API_URL}/download-pdf`, {
      params: req.query,
      responseType: 'stream',
      timeout: 30000
    });
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename=${req.query.filename || 'comic.pdf'}`);
    response.data.pipe(res);
  } catch (error) {
    res.status(500).json({
      success: false,
      msg: `下载PDF失败：${error.message}`
    });
  }
});

// 启动服务
app.listen(PORT, () => {
  console.log(`Node.js服务启动成功：http://localhost:${PORT}`);
  // 测试Python连通性
  axios.get('http://localhost:5000/health', { timeout: 5000 })
    .then(() => console.log('✅ Python API 连通正常'))
    .catch(err => console.log('❌ Python API 连通失败：', err.message));
});