# YouTube教程字幕知识库

## 📚 已抓取视频

| 频道 | 视频 | 状态 | 词数 |
|-----|------|------|------|
| 甬哥侃侃侃 | 2025年度代理协议排名 | ✅ | ~8000 |
| 甬哥侃侃侃 | Serv00搭建教程 | ✅ | ~6000 |
| 科技老王 | Sing-box一键部署 | ✅ | ~5000 |
| 科技老王 | S-UI与3X-UI共存 | ✅ | ~7000 |
| 大头柴Studio | S-UI零基础教程 | ✅ | ~9000 |
| JollyRoger | Hysteria2官方文档 | ✅ | ~4000 |
| 一瓶奶油 | S-UI进阶玩法 | ✅ | ~6000 |

---

## 📖 核心知识点提取

### 1. 协议对比总结

#### Hysteria2 (Hy2)
- **原理**: 基于QUIC协议（HTTP/3底层），专为弱网优化
- **优势**: 
  - 低延迟，抗丢包能力强
  - 自带拥塞控制
  - 支持端口跳跃（UDP Hop）
- **配置要点**:
  - 端口建议非443（如8080）
  - 跳过证书验证设为true
  - 可设置混淆密码
- **适用场景**: 高延迟网络、晚高峰拥堵、垃圾线路

#### VLESS + Reality
- **原理**: 借用真实网站TLS指纹伪装服务器
- **优势**:
  - 抗SNI检测
  - 无需真实证书
  - 性能开销极小
- **配置要点**:
  - 目标网站选Google/Apple/Intel等高延迟低网站
  - 指纹选Safari或Chrome
  - 端口用443
- **适用场景**: 日常使用、追求稳定、不被检测

#### Tuic5
- **原理**: 基于QUIC的多协议代理
- **优势**:
  - 多路复用
  - 低延迟
  - 大带宽支持
- **适用场景**: 多设备同时使用、大流量需求

#### VMess + WebSocket + TLS
- **原理**: VMess协议通过WS传输，套在TLS/CDN下
- **优势**:
  - 完美适配Cloudflare CDN
  - 流量伪装成正常网页
- **适用场景**: 需要套CDN加速、优选IP

---

### 2. 面板配置要点

#### 3X-UI v3.6.0
**安装命令**:
```bash
bash <(curl -Ls https://raw.githubusercontent.com/MHSanaei/3x-ui/main/install.sh)
```

**关键配置**:
- 面板端口: 1024-65535之间
- SSL证书: 有域名用Let's Encrypt（90天），无域名用IP证书（6天）
- Webbasepath: 随机字符串增加安全性
- 数据库: SQLite（<500用户）或 PostgreSQL

**Reality节点配置**:
1. 协议选择VLESS
2. 传输选择TCP + Reality
3. 目标网站选Google/Apple/Intel
4. 指纹选Safari或Chrome
5. 启用嗅探

**Hysteria2节点配置**:
1. 协议选择Hysteria
2. 端口选非443（如8080）
3. 密码自定义
4. 跳过证书验证=true
5. 可选UDP Hop跳转端口

#### S-UI 面板
**安装命令**:
```bash
bash <(curl -Ls https://raw.githubusercontent.com/sprov065/s-ui/master/install.sh)
```

**特点**:
- 原生支持Sing-box
- 更好的Tuic/Hy2支持
- 支持多节点订阅整合
- 现代化UI界面

**进阶功能**:
- 流量分流（入站→出站路由）
- 多节点统一管理
- 第三方订阅导入
- 中转功能

---

### 3. 故障排查指南

#### IP被封
**症状**: 节点无法连接，提示connection refused
**解决方案**:
1. 联系VPS客服更换IP（Racknerd免费换3次/年）
2. 使用Argo固定隧道隐藏真实IP
3. 切换到CDN优选IP
4. 改用Workers免费代理

#### 端口被封
**症状**: 特定端口无法访问
**解决方案**:
1. 切换到80/443端口
2. 使用Argo固定隧道（无需开端口）
3. Hysteria2端口跳跃功能
4. 更换协议

#### 速度缓慢
**症状**: 延迟高、下载慢
**解决方案**:
1. 使用优选IP或优选域名
2. 切换美西机房（延迟更低）
3. 开启WARP出站分流
4. 检查DNS配置（使用DOH加密）
5. 尝试不同协议（Reality→Hy2）

#### 证书失效
**症状**: 面板无法访问，提示证书错误
**解决方案**:
1. 手动续签证书: `x-ui.sh` → SSL证书管理
2. 检查域名DNS解析是否正确
3. 确保80端口开放（Let's Encrypt验证）
4. 更换域名或使用IP证书

#### 订阅链接失效
**症状**: 客户端无法更新订阅
**解决方案**:
1. 检查面板服务是否在运行
2. 确认Webbasepath正确
3. 清除客户端缓存
4. 重新复制订阅链接

---

### 4. 最佳实践

#### 多协议共存方案
一台VPS同时部署多种协议，提高可用性：
```
- Reality节点（日常使用，稳定）
- Hysteria2节点（晚高峰备用，抗丢包）
- Tuic节点（大带宽需求）
- WS-TLS节点（套CDN加速）
```

#### CDN加速配置
1. VPS端添加WS-TLS配置
2. Cloudflare添加A记录（云朵灰色）
3. SSL/TLS设为"完全"
4. DNS记录云朵点亮开启代理
5. 客户端使用CDN域名连接

#### 优选IP设置
```bash
# 方法1: 脚本自动优选
sing-box add wss your.domain.com --proxyip preferred-ip

# 方法2: 手动指定
# 客户端配置中server填写优选IP
```

**常用优选IP段**:
- 美西: 104.16.0.0/12, 172.64.0.0/13
- 欧洲: 162.159.0.0/16
- 亚洲: 172.67.0.0/16

#### 安全加固
```bash
# 防火墙规则
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 面板端口 -j ACCEPT
iptables -A INPUT -p udp --dport 节点端口 -j ACCEPT

# 开启BBR加速
echo "net.core.default_qdisc=fq" >> /etc/sysctl.conf
echo "net.ipv4.tcp_congestion_control=bbr" >> /etc/sysctl.conf
sysctl -p
```

---

### 5. 客户端配置示例

#### V2rayN (Windows)
```json
{
  "proxy": "127.0.0.1:1080",
  "remote_dns": "https://8.8.8.8/dns-queries",
  "sniffing": true,
  "route_only": false
}
```

#### Clash Verge
订阅链接格式:
```
https://面板域名:端口/sub?uuid=UUID&format=clash
```

#### Shadowrocket (iOS)
1. 复制节点链接
2. 退出APP重新打开
3. 自动导入节点
4. 修改地址为IP（如需直连）

---

### 6. 免费代理方案

#### Cloudflare Workers
**优势**:
- 完全免费
- 无VPS成本
- 全球节点自动优选
- 无限流量

**部署步骤**:
1. 创建Worker应用
2. 粘贴代理脚本代码
3. 配置UUID/密码
4. 部署获取节点

**脚本来源**:
- https://github.com/yonggekkk/Cloudflare-vless-trojan

---

## 🔗 相关资源

- 视频字幕: `youtube_videos/transcripts.json`
- 知识点: `youtube_videos/knowledge_points.json`
- 视频列表: `youtube_videos/video_list.json`
