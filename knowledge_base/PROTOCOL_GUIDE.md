# 协议节点类型对比与配置指南

## 📊 主流协议对比表

| 协议 | 特点 | 速度 | 稳定性 | 抗封锁 | 推荐场景 |
|-----|------|-----|-------|-------|---------|
| **VLESS+Reality** | 零RTT握手，伪装真实网站TLS | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 首选推荐，最稳定 |
| **Hysteria2** | QUIC协议，低延迟抗丢包 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | 高延迟/丢包网络 |
| **Tuic5** | 基于QUIC，多路复用 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | 大带宽需求 |
| **VMess+TLS** | 成熟稳定，兼容性好 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | 基础方案 |
| **Trojan+TLS** | 简单高效，伪装HTTPS | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 简单部署 |
| **VMESS-WS-TLS** | CDN友好，套CF首选 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 需要CDN加速 |

---

## 🔧 各协议详细说明

### 1. VLESS + Reality（推荐首选）

**原理**: Reality协议通过"借用"真实目标网站（如Google、Apple）的TLS指纹来伪装服务器，让流量看起来像访问正常网站。

**优势**:
- 无需证书，自动生成
- 抗DNS污染能力强
- 无法被SNI检测
- 性能开销极小

**配置参数**:
```
协议: VLESS
地址: VPS_IP或域名
端口: 443
UUID: 自动生成
流控: reality
 publicKey: 自动生成
 shortId: 可选
 spiderX: / (可选)
```

**适用场景**: 日常使用、追求稳定、不被检测

---

### 2. Hysteria2 (Hy2)

**原理**: 基于QUIC协议（HTTP/3的底层），专为弱网环境优化，自带拥塞控制。

**优势**:
- 低延迟（尤其高RTT网络）
- 抗丢包能力强
- 支持端口跳跃（UDP Hop）
- 自带流量统计

**配置参数**:
```
协议: Hysteria2
地址: VPS_IP或域名
端口: 443（建议非443）
密码: 自定义
跳过证书验证: true（自签证书）
```

**适用场景**: 网络不稳定、高延迟、需要端口跳跃

---

### 3. Tuic5

**原理**: 基于QUIC的多协议代理，支持多路复用和优先级调度。

**优势**:
- 高并发性能优秀
- 支持 QUIC 多路复用
- 低延迟传输

**配置参数**:
```
协议: TUIC
地址: VPS_IP或域名
端口: 443
用户: 自定义
密码: 自定义
```

**适用场景**: 多设备同时使用、大带宽需求

---

### 4. VMess + WebSocket + TLS

**原理**: VMess协议通过WebSocket传输，套在TLS/CDN下面，适合中转。

**优势**:
- 完美适配Cloudflare CDN
- 流量伪装成正常网页
- 支持优选IP

**配置参数**:
```
协议: VMESS
地址: CDN域名（如 ai.yourdomain.com）
端口: 443
UUID: 自定义
传输: WebSocket
路径: /random-path
TLS: 开启
```

**适用场景**: 需要套CDN、优选IP加速

---

### 5. Trojan

**原理**: 模拟HTTPS流量，使用真实TLS证书伪装。

**优势**:
- 配置简单
- 兼容性好
- 性能稳定

**配置参数**:
```
协议: TROJAN
地址: VPS_IP或域名
端口: 443
密码: 自定义
```

**适用场景**: 简单部署、快速上手

---

## 🌐 套CDN配置指南

### 为什么套CDN？

1. **隐藏真实IP** - 防止IP被封
2. **优选IP加速** - 使用CF优选节点
3. **抗封锁** - CDN域名被墙概率低
4. **免费带宽** - CF每天100GB免费流量

### 配置步骤（Sing-box + Cloudflare）

#### 第一步：VPS端配置
```bash
# 添加WS-TLS配置
sing-box add wss your.domain.com
# 记录生成的端口和路径
```

#### 第二步：Cloudflare DNS设置
1. 添加A记录: `ai` → VPS_IP（云朵灰色，直连）
2. 开启SSL/TLS → 设置为"完全"
3. 再次编辑DNS记录，云朵点亮（开启代理）

#### 第三步：客户端配置
```json
{
  "type": "vmess",
  "server": "ai.yourdomain.com",
  "port": 443,
  "uuid": "xxx",
  "transport": {
    "type": "ws",
    "path": "/xxx"
  },
  "tls": {
    "enabled": true,
    "server_name": "ai.yourdomain.com"
  }
}
```

---

## 🎯 优选IP配置

### 什么是优选IP？

Cloudflare提供大量边缘节点IP，优选IP就是选择延迟低、速度快的CF节点。

### 优选方法

#### 方法一：自动优选（推荐）
```bash
# 使用sing-box内置优选
sing-box add wss your.domain.com --proxyip preferred-ip
```

#### 方法二：手动优选
1. 使用CF优选工具扫描可用IP
2. 选择延迟<100ms的IP
3. 客户端配置中填写优选IP

#### 方法三：Workers/Pages优选
- CF Workers/Pages自带全局优选，无需手动配置
- 免费额度内无限使用

---

## 💻 面板配置指南

### 3X-UI 面板

**安装命令**:
```bash
bash <(curl -Ls https://raw.githubusercontent.com/MHSanaei/3x-ui/main/install.sh)
```

**常用功能**:
- 入站列表：管理所有节点
- 客户端列表：查看在线用户
- 系统设置：修改端口、SSL证书
- 数据库备份：定期备份配置

**添加Reality节点**:
1. 入站列表 → 添加
2. 协议选择 VLESS
3. 传输选择 TCP + Reality
4. 目标网站选 Google/Apple
5. 生成配置链接

**添加Hysteria2节点**:
1. 入在列表 → 添加
2. 协议选择 Hysteria
3. 端口填写（建议非443）
4. 密码自定义
5. 跳转端口可选（UDP Hop）

---

### S-UI 面板

**安装命令**:
```bash
bash <(curl -Ls https://raw.githubusercontent.com/sprov065/s-ui/master/install.sh)
```

**特点**:
- 原生支持Sing-box
- 更好的Tuic/Hy2支持
- 界面更现代
- 支持多节点订阅

---

## 🚀 Cloudflare Workers/Pages 免费代理

### 优势
- **完全免费** - 无VPS成本
- **全球节点** - 自动优选IP
- **不可封锁** - workers.dev域名难被墙
- **无限流量** - 无用量限制

### 部署步骤

#### 1. 创建Worker
```bash
# 登录 Cloudflare Dashboard
# Workers & Pages → Create Application → Worker → Deploy
```

#### 2. 粘贴代码
从GitHub获取最新脚本：
- https://github.com/yonggekkk/Cloudflare-vless-trojan
- 复制 workers.js 内容
- 粘贴到 Worker 编辑器

#### 3. 配置参数
```javascript
const UUID = 'your-uuid-here';
const PASSWORD = 'your-trojan-password';
const PROXYIP = ''; // 可选，留空自动优选
```

#### 4. 获取节点
```
VLESS: https://your-worker.workers.dev/UUID
TROJAN: https://your-worker.workers.dev/PASSWORD
```

---

## ⚡ 故障排查

### 连接失败
1. 检查防火墙是否开启对应端口
2. 确认SSL证书有效
3. 检查UUID/密码是否正确
4. 尝试切换协议（Reality→Hy2）

### 速度慢
1. 启用优选IP
2. 切换到美西机房
3. 使用CDN中转
4. 尝试不同协议

### IP被封
1. 联系VPS客服换IP
2. 改用Argo固定隧道
3. 切换到Workers免费代理
4. 使用CDN优选IP

---

## 📋 快速配置模板

### 一键添加多种协议
```bash
# Reality节点
sb add reality

# Hysteria2节点
sb add hy2

# Tuic5节点
sb add tuic

# WS-TLS节点（套CDN用）
sb add wss your.domain.com
```

### 查看配置信息
```bash
sb info          # 显示所有配置
sb url           # 生成分享链接
sb qr            # 生成二维码
```

---

## 🔗 相关资源

- 3X-UI GitHub: https://github.com/MHSanaei/3x-ui
- S-UI GitHub: https://github.com/sprov065/s-ui
- Sing-box脚本: https://github.com/SagerNet/sing-box
- CF代理脚本: https://github.com/yonggekkk/Cloudflare-vless-trojan
- v2ray-agent: https://github.com/mack-a/v2ray-agent
