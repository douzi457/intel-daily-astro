# 面板配置完全指南 - 3X-UI / S-UI / H-UI

## 📊 面板对比

| 面板 | 优点 | 缺点 | 推荐场景 |
|-----|------|------|---------|
| **3X-UI** | 界面友好、功能全面、文档多 | 资源占用稍高 | 新手入门、快速部署 |
| **S-UI** | Sing-box原生、现代界面、多协议 | 更新频繁 | 进阶用户、多协议需求 |
| **H-UI** | 轻量级、低资源占用 | 功能相对简单 | 低配VPS、单协议 |

---

## 🔧 3X-UI 面板详解

### 安装命令
```bash
bash <(curl -Ls https://raw.githubusercontent.com/MHSanaei/3x-ui/main/install.sh)
```

### 安装过程
1. 输入命令回车
2. 选择面板端口（建议1024-65535）
3. 选择SSL证书（有域名选1，无域名选2）
4. 记录随机生成的账号密码

### 登录面板
```
https://VPS_IP:端口
或
https://域名:端口
```

### 核心功能

#### 1. 入站列表 - 节点管理
- **添加入站**: 创建新节点
- **编辑**: 修改节点配置
- **删除**: 移除节点
- **克隆**: 复制节点配置

#### 2. 客户端列表 - 用户管理
- 查看在线用户
- 设置流量配额
- 设置到期时间
- 禁用/启用用户

#### 3. 系统设置
- 面板端口修改
- SSL证书管理
- 数据库备份恢复
- 面板语言设置

#### 4. 证书管理
- Let's Encrypt自动申请
- 自定义证书上传
- 自动续签设置

### 添加节点步骤

#### VLESS + Reality节点
1. 入在列表 → 添加
2. 协议选择: VLESS
3. 端口: 443
4. ID: 自动生成UUID
5. 流控: reality
6. 目标: 选择Google/Apple等
7. 点击创建

#### Hysteria2节点
1. 入在列表 → 添加
2. 协议选择: Hysteria
3. 端口: 建议非443（如8080）
4. 密码: 自定义
5. 跳转端口: 可选UDP Hop
6. 点击创建

#### VMess + WS + TLS节点
1. 入在列表 → 添加
2. 协议选择: VMess
3. 端口: 443
4. 传输: WebSocket
5. 路径: /random-path
6. TLS: 开启
7. 点击创建

### 导出配置
```
1. 入在列表 → 选择节点
2. 点击"信息"或"二维码"
3. 复制订阅链接
4. 或使用"分享"生成单个节点链接
```

---

## 🔧 S-UI 面板详解

### 安装命令
```bash
bash <}(curl -Ls https://raw.githubusercontent.com/sprov065/s-ui/master/install.sh)
```

### 特点
- 原生支持Sing-box
- 更好的Tuic/Hy2支持
- 现代化界面设计
- 支持多节点订阅

### 核心功能

#### 1.  inbound管理
- 支持协议更丰富
- 配置更直观
- 实时流量统计

#### 2. 多节点管理
- 一键订阅生成
- 第三方节点导入
- 节点分组管理

#### 3. 模板系统
- 预设配置模板
- 快速部署常用方案
- 配置导出导入

### 添加Hysteria2节点
```
1. Inbound → Add
2. Protocol: Hysteria
3. Port: 非443端口
4. Password: 自定义
5. Skip cert verify: true
6. Save
```

### 添加Tuic节点
```
1. Inbound → Add
2. Protocol: TUIC
3. Port: 443
4. User: 自定义
5. Password: 自定义
6. Save
```

---

## 🔧 H-UI 面板详解

### 安装命令
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/jonssonyan/h-ui/main/install.sh)
```

### 特点
- 最低配置要求：1核CPU、512MB内存
- 专注Hysteria2协议
- 极致性能优化

### 配置要点
1. 监听地址: 446等（建议非443）
2. TLS: 开启
3. 流量统计API: 默认即可
4. 使用Hysteria2证书（自动识别）

---

## 🎨 面板配置最佳实践

### 1. 多协议共存
一台VPS同时运行多种协议，提高可用性：
```
- Reality节点（日常使用）
- Hysteria2节点（高延迟网络）
- Tuic节点（大带宽需求）
- WS-TLS节点（套CDN用）
```

### 2. 证书管理
- 使用有效域名申请SSL证书
- 开启自动续签
- 备份证书文件

### 3. 安全设置
```bash
# 防火墙规则
iptables -A INPUT -p tcp --dport 端口 -j ACCEPT
iptables -A INPUT -p udp --dport 端口 -j ACCEPT

# 或firewalld
firewall-cmd --add-port=端口/tcp --permanent
firewall-cmd --add-port=端口/udp --permanent
firewall-cmd --reload
```

### 4. 备份策略
```bash
# 定期备份数据库
cp /usr/local/3x-ui/x-ui.db /backup/
cp /usr/local/s-ui/s-ui.db /backup/

# 备份配置文件
tar -czf config-backup.tar.gz /usr/local/3x-ui/bin/
```

---

## ⚡ 故障排查

### 面板无法访问
1. 检查端口是否开放
2. 检查防火墙设置
3. 检查服务状态: `systemctl status x-ui`
4. 重启服务: `systemctl restart x-ui`

### 证书续签失败
1. 检查域名DNS解析
2. 检查80端口是否开放
3. 手动续签: `x-ui.sh` → SSL证书管理
4. 更换域名或IP

### 节点无法连接
1. 检查端口是否正确
2. 检查防火墙规则
3. 检查协议是否匹配
4. 检查UUID/密码是否正确

---

## 📋 面板命令速查

### 3X-UI
```bash
# 管理面板
cd /usr/local/3x-ui && ./x-ui.sh

# 查看状态
systemctl status x-ui

# 启动/停止/重启
systemctl start x-ui
systemctl stop x-ui
systemctl restart x-ui

# 开机自启
systemctl enable x-ui
```

### S-UI
```bash
# 管理面板
cd /usr/local/s-ui && ./s-ui.sh

# 查看状态
systemctl status s-ui

# 启动/停止/重启
systemctl start s-ui
systemctl stop s-ui
systemctl restart s-ui
```

### H-UI
```bash
# 管理面板
h-ui

# 查看状态
systemctl status h-ui
```

---

## 🔗 相关资源

- 3X-UI GitHub: https://github.com/MHSanaei/3x-ui
- S-UI GitHub: https://github.com/sprov065/s-ui
- H-UI GitHub: https://github.com/jonssonyan/h-ui
