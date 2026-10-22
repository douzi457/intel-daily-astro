# 面板配置详解 - 3X-UI v3.6.0 / S-UI 最新版

## 📌 版本信息
- **3X-UI**: v3.6.0（2026年稳定版）
- **S-UI**: 持续更新，支持Sing-box原生
- **H-UI**: 轻量级，专注Hysteria2

---

## 🔧 3X-UI v3.6.0 核心配置字段详解

### 1. 入站列表配置

#### VLESS + Reality 节点
| 字段 | 说明 | 推荐值 |
|-----|------|-------|
| **备注** | 节点名称 | 自定义，如"Reality-主" |
| **端口** | 监听端口 | 443（首选）或自定义 |
| **ID** | UUID | 自动生成 |
| **流控** | 加密方式 | reality |
| **目标** | 伪装网站 | google.com / apple.com / intel.com |
| **私钥** | 自动生成 | 保持默认 |
| **指纹** | Client Fingerprint | safari / chrome / firefox |
| **最短客户端版本** | 版本限制 | 保持默认 |
| **服务器域名** | SNI | 与目标一致 |
| **开启嗅探** | HTTP Host嗅探 | 启用 |
| **仅路由** | 仅路由流量 | 可选启用 |

#### Hysteria2 节点
| 字段 | 说明 | 推荐值 |
|-----|------|-------|
| **端口** | UDP端口 | 非443端口（如8080） |
| **密码** | 连接密码 | 自定义强密码 |
| **跳过证书验证** | Insecure | true（自签证书） |
| **跳转端口** | UDP Hop | 可选（如48000） |
| **SNI** | Server Name | 你的域名 |

#### VMess + WebSocket + TLS 节点（套CDN用）
| 字段 | 说明 | 推荐值 |
|-----|------|-------|
| **端口** | 监听端口 | 443 |
| **传输** | 网络类型 | WebSocket |
| **路径** | WS Path | /random-path（自定义） |
| **TLS** | 加密传输 | 开启 |
| **域名** | Host | CDN域名（如ai.yourdomain.com） |

---

### 2. 系统设置配置

| 设置项 | 说明 | 推荐 |
|-------|------|-----|
| **面板端口** | Web管理端口 | 1024-65535之间 |
| **Webbasepath** | 面板路径 | 随机字符串（如/xui888） |
| **SSL证书** | HTTPS证书 | 有域名用Let's Encrypt |
| **数据库路径** | 数据存储 | /etc/x-ui/x-ui.db |
| **日志级别** | 日志详细度 | info |

---

### 3. 环境变量配置（Docker部署）

```bash
# 基础配置
XUI_LOG_LEVEL=info           # 日志级别：debug/info/warning/error
XUI_DB_TYPE=sqlite          # 数据库类型：sqlite/postgres
XUI_DB_FOLDER=/etc/x-ui     # 数据库文件夹

# 安全配置
XUI_ENABLE_FAIL2BAN=true    # 启用Fail2ban防爆破
NODE_TOKEN_ENCRYPTION=off   # 节点Token加密：off/migration/required

# 隧道健康监控
XUI_TUNNEL_HEALTH_MONITOR=false  # 启用健康监控
XUI_TUNNEL_HEALTH_INTERVAL=30s   # 探测间隔
XUI_TUNNEL_HEALTH_TIMEOUT=10s    # 超时时间
XUI_TUNNEL_HEALTH_FAILURES=3     # 连续失败次数触发重启
XUI_TUNNEL_HEALTH_COOLDOWN=5m    # 重启冷却时间
```

---

### 4. 客户端配置导出

#### 订阅链接格式
```
# VLESS订阅
https://面板域名:端口/sub?uuid=你的UUID&format=v2ray

# Clash订阅
https://面板域名:端口/sub?uuid=你的UUID&format=clash

# Sing-box订阅
https://面板域名:端口/sub?uuid=你的UUID&format=sing-box
```

#### 单节点分享链接
```
# VLESS+Reality
vless://UUID@域名:443?type=reality&security=reality&sni=目标域名&fp=safari&flow=xtls-rprx-vision&remark=节点名

# Hysteria2
hysteria2://密码@域名:端口?insecure=1&pinSHA256=指纹&servername=域名#节点名
```

---

## 🔧 S-UI 面板配置特点

### 核心优势
- 原生支持Sing-box
- TUIC/Hysteria2配置更直观
- 支持多节点订阅整合
- 现代化UI界面

### 添加TUIC节点步骤
1. Inbound → Add
2. Protocol: TUIC
3. Port: 443
4. User: 自定义用户名
5. Password: 自定义密码
6. Disable SNI: 可选
7. Save

### 添加Hysteria2节点步骤
1. Inbound → Add
2. Protocol: Hysteria2
3. Port: 自定义（建议非443）
4. Password: 自定义
5. Obfs: 可选混淆密码
6. Save

---

## ⚡ 面板故障排查

### 问题1: 面板无法访问
```bash
# 检查服务状态
systemctl status x-ui
# 或
systemctl status s-ui

# 重启服务
systemctl restart x-ui
# 或
systemctl restart s-ui

# 检查端口占用
netstat -tulpn | grep 端口号
```

### 问题2: SSL证书失效
```bash
# 手动续签证书
cd /usr/local/3x-ui
./x-ui.sh
# 选择 SSL证书管理 → 重新申请
```

### 问题3: 节点无法连接
- 检查防火墙是否放行端口
- 检查协议是否匹配客户端
- 检查UUID/密码是否正确
- 尝试切换协议（Reality→Hy2）

### 问题4: 订阅链接失效
- 检查面板是否在运行
- 检查Webbasepath是否正确
- 清除客户端缓存并重新导入

---

## 📋 面板安全加固

### 1. 防火墙配置
```bash
# 放行必要端口
firewall-cmd --add-port=443/tcp --permanent
firewall-cmd --add-port=80/tcp --permanent
firewall-cmd --add-port=你的面板端口/tcp --permanent
firewall-cmd --reload

# 或iptables
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 面板端口 -j ACCEPT
```

### 2. 面板安全设置
- 使用随机Webbasepath
- 启用强密码
- 启用2FA（如支持）
- 限制IP访问（如可能）

### 3. 定期备份
```bash
# 备份数据库
cp /etc/x-ui/x-ui.db /backup/x-ui-backup-$(date +%Y%m%d).db

# 备份配置
tar -czf x-ui-config-backup.tar.gz /etc/x-ui/
```
