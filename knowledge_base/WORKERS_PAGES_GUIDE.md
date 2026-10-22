# Cloudflare Workers/Pages 免费代理完全指南

## 🎯 什么是Workers/Pages代理？

利用Cloudflare免费的Workers（服务器端函数）或Pages（静态网站）服务，部署代理脚本，实现**完全免费、无VPS成本**的科学上网节点。

### 核心优势
- ✅ **零成本** - 完全免费，无需购买VPS
- ✅ **无限流量** - 无流量限制
- ✅ **全球节点** - 自动使用CF全球边缘节点
- ✅ **难被封锁** - workers.dev域名难以被墙
- ✅ **自动优选** - 无需手动配置优选IP

---

## 📦 推荐脚本

### 1. 甬哥 CF代理脚本（推荐新手）

**GitHub**: https://github.com/yonggekkk/Cloudflare-vless-trojan

**功能特点**:
- 支持VLESS+WS+TLS
- 支持Trojan+WS+TLS
- 支持Socks5/HTTP本地代理
- ECH-TLS/普通TLS/无TLS三种模式
- 单节点链接、聚合订阅、通用节点订阅
- Sing-box/Clash节点订阅格式

**版本**: 25.5.4（持续更新）

---

### 2. v2ray-agent 八合一

**GitHub**: https://github.com/mack-a/v2ray-agent

**功能特点**:
- Xray-core + Sing-box 双内核
- 支持Tuic、Hysteria2
- 八合一多功能脚本
- Docker部署支持

---

## 🚀 部署步骤

### 方式一：Cloudflare Workers（推荐）

#### 1. 注册Cloudflare账号
- 访问 https://dash.cloudflare.com
- 免费注册，绑定邮箱即可

#### 2. 创建Worker
```
Workers & Pages → Create Application → Worker → Deploy
```

#### 3. 获取脚本代码
```bash
# 从GitHub复制最新代码
# https://github.com/yonggekkk/Cloudflare-vless-trojan
# 选择 workers.js 文件内容
```

#### 4. 编辑代码
粘贴到Worker编辑器，修改以下参数：

```javascript
// 第4行 - Trojan密码（必须自定义）
const PASSWORD = 'your-trojan-password';

// 第5行 - ProxyIP（可选，留空自动优选）
const PROXYIP = '';

// 第6行 - 伪装网页（建议留空）
const FAKE_URL = '';
```

#### 5. 部署
点击 **Deploy** 按钮

#### 6. 获取节点
```
VLESS: https://your-worker.workers.dev/your-uuid
Trojan: https://your-worker.workers.dev/your-password
```

---

### 方式二：Cloudflare Pages

#### 1. 创建Pages应用
```
Workers & Pages → Create Application → Pages → Deploy directly
```

#### 2. 获取脚本
从GitHub下载 `pages` 文件夹内容

#### 3. 编辑配置
修改 `index.html` 或配置文件中的参数

#### 4. 部署
上传文件或连接GitHub仓库自动部署

---

### 方式三：GitHub Actions自动部署

#### 1. Fork仓库
fork https://github.com/yonggekkk/Cloudflare-vless-trojan

#### 2. 启用Actions
Settings → Actions → Enable

#### 3. 配置Secrets
```
UUID: 你的UUID
PASSWORD: 你的Trojan密码
PROXYIP: 可选ProxyIP
```

#### 4. 手动触发
Actions → Run workflow → 选择分支

---

## 🔧 高级配置

### 1. 自定义域名

**优点**: 更稳定，不易被封
**缺点**: 需要域名，配置稍复杂

#### 步骤：
1. 在Cloudflare添加域名
2. Worker设置 → Triggers → Custom Domains
3. 添加域名并等待DNS生效

### 2. ProxyIP配置

ProxyIP用于解决优选IP问题，让流量从特定节点出站。

```javascript
// 方式一：直接填写IP
const PROXYIP = '104.16.0.0';

// 方式二：使用域名
const PROXYIP = 'proxyip.example.com';

// 方式三：留空自动优选（推荐）
const PROXYIP = '';
```

**注意**: 如果无法访问CF官网或ChatGPT，说明ProxyIP失效，需更换。

### 3. ECH-TLS配置

ECH（Encrypted Client Hello）增强隐私保护。

```javascript
// 启用ECH
const ENABLE_ECH = true;

// ECH配置
const ECH_CONFIG = '...'; // 从工具生成
```

---

## 📱 客户端配置

### V2rayN (Windows)

#### 导入订阅
```
复制 Worker 订阅链接 → V2rayN → 订阅 → 添加
```

#### 手动添加节点
```json
{
  "mux": {"enabled": false},
  "log": {"loglevel": "warning"},
  "inbounds": [{
    "port": 1080,
    "listen": "127.0.0.1",
    "protocol": "socks"
  }],
  "outbounds": [{
    "protocol": "vless",
    "settings": {
      "vnext": [{
        "address": "your-worker.workers.dev",
        "port": 443,
        "users": [{"id": "your-uuid"}]
      }]
    },
    "streamSettings": {
      "network": "ws",
      "security": "tls",
      "wsSettings": {"path": "/your-uuid"}
    }
  }]
}
```

### Clash Verge

#### 导入订阅
```
配置 → 订阅 → 添加 → 粘贴订阅链接
```

### sing-box (移动端)

#### 导入配置
```json
{
  "inbounds": [{
    "type": "mixed",
    "listen": "127.0.0.1",
    "listen_port": 2080
  }],
  "outbounds": [{
    "type": "vless",
    "server": "your-worker.workers.dev",
    "server_port": 443,
    "uuid": "your-uuid",
    "transport": {
      "type": "ws",
      "path": "/your-uuid"
    }
  }]
}
```

---

## ⚡ 优选IP配置

### 什么是优选IP？

Cloudflare在全球有300+节点，优选IP就是选择延迟低、速度快的CF边缘节点IP。

### 方法一：脚本自动优选（推荐）

甬哥脚本内置自动优选功能，部署时自动选择最佳IP。

### 方法二：手动配置

```javascript
// 在脚本中指定优选IP
const PROXYIP = '104.16.0.0';  // 美西
const PROXYIP = '162.159.0.0'; // 欧洲
const PROXYIP = '172.64.0.0';  // 亚洲
```

### 常用优选IP段

```
美国: 104.16.0.0/12, 172.64.0.0/13
欧洲: 162.159.0.0/16, 104.18.0.0/15
亚洲: 172.67.0.0/16, 104.20.0.0/14
```

---

## 🔍 故障排查

### 问题1：无法访问节点链接

**原因**: Workers域名被墙
**解决**: 
- 尝试Pages域名
- 使用自定义域名
- 检查脚本是否正确部署

### 问题2：连接速度慢

**原因**: 优选IP不佳
**解决**:
- 更换PROXYIP
- 尝试不同地区IP
- 检查网络环境

### 问题3：节点频繁失效

**原因**: 免费额度限制或被检测
**解决**:
- 部署多个Worker备用
- 定期更新脚本版本
- 使用自定义域名

### 问题4：订阅更新失败

**原因**: 缓存或网络问题
**解决**:
- 清除客户端缓存
- 手动刷新订阅
- 检查网络连接

---

## 💡 最佳实践

### 1. 多脚本备份
部署2-3个不同Worker，互为备份。

### 2. 定期更新
关注GitHub更新，及时更新脚本版本。

### 3. 组合使用
Workers免费节点 + VPS付费节点组合，双重保障。

### 4. 域名保护
使用自定义域名时，开启CF防护功能。

---

## 📚 相关资源

### GitHub仓库
- 甬哥CF代理: https://github.com/yonggekkk/Cloudflare-vless-trojan
- v2ray-agent: https://github.com/mack-a/v2ray-agent
- Sing-box: https://github.com/SagerNet/sing-box

### 教程视频
- 科技老王YouTube: https://www.youtube.com/@kejilaowang
- 甬哥YouTube: https://www.youtube.com/@ygkkk

### 工具下载
- V2rayN: https://github.com/2dust/v2rayN
- Clash Verge: https://github.com/clash-verge-rev/clash-verge-rev
- Sing-box UI: https://github.com/StashKing/sing-box-unity
