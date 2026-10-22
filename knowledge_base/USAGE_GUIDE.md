# 技术博客知识库使用指南

## 📚 知识库内容

### 已爬取博客

| 博客名称 | URL | 主要内容 |
|---------|-----|---------|
| 甬哥侃侃侃 | https://ygkkk.blogspot.com | VPS代理教程、Sing-box、Argo隧道、翻墙技术 |
| 编程随想 | https://program-think.blogspot.com | 翻墙安全、Tor/I2P、隐私保护 |
| 233Boy | https://233boy.com | Sing-box一键脚本、图文教程 |
| 科技老王 | https://kejilaowang.com | VPS评测、代理工具推荐 |
| 老E的博客 | https://appscross.com | 开源代理客户端选择指南 |

### 已保存文章（ygkkk博客）

1. **Sing-box精装桶小白一键脚本** (2023-11)
   - 支持本地WARP+赛风VPN切换
   - Argo固定临时双隧道可共存
   - 支持本地IP订阅链接
   
2. **ArgoSBX一键无交互小钢炮脚本** (2025-08)
   - Sing-box + Xray + Cloudflared-Argo 三内核
   - 一键SSH命令生成器
   - 多协议自由搭配

3. **Racknerd-VPS推荐** (2026-04)
   - 高性价比VPS选购指南
   - 自建翻墙代理协议组合方案

4. **CF Socks5/Http免费代理教程** (2025-12)
   - Cloudflare Workers代理
   - ECH/TLS/无TLS三种模式

---

## 🔍 如何使用知识库

### 1. 查找教程

```bash
# 查找Sing-box相关教程
grep -r "sing-box" knowledge_base/

# 查找VPS推荐
grep -r "racknerd\|搬瓦工" knowledge_base/

# 查找Argo隧道配置
grep -r "argo" knowledge_base/
```

### 2. 常见问题解决

#### IP被封
- 方案1: 联系VPS客服更换IP（Racknerd 72小时内免费换）
- 方案2: 使用Argo固定隧道隐藏真实IP
- 方案3: 切换至CDN优选IP

#### 端口被封
- 切换到80/443端口
- 使用Argo固定隧道（无需开端口）
- Hysteria2端口跳跃功能

#### 速度缓慢
- 使用优选IP或优选域名
- 切换VPS机房（美西 > 美东）
- 开启WARP出站分流

---

## 📂 知识库结构

```
knowledge_base/
├── ygkkk_blog/
│   ├── articles.json          # 已爬取的文章内容
│   └── README.md              # 博客说明
├── knowledge_base_index.json  # 知识库索引
└── USAGE_GUIDE.md             # 本文件
```

---

## 🎯 常用命令速查

### VPS相关
```bash
# 测试VPS性能
bash <(curl -Ls https://bench.sh)

# 查看系统信息
uname -a
cat /etc/os-release

# 查看网络状态
netstat -tulpn
ss -tulpn
```

### Sing-box相关
```bash
# 进入管理界面
sb

# 添加节点
sb add reality
sb add hy2
sb add tuic

# 查看配置
sb info
```

### Cloudflare Argo相关
```bash
# 安装cloudflared
wget -qO- https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -O cloudflared.deb && sudo dpkg -i cloudflared.deb

# 登录Cloudflare
cloudflared tunnel login

# 创建隧道
cloudflared tunnel create my-tunnel
```

---

## 🔗 相关资源

### YouTube频道
- 甬哥侃侃侃: https://www.youtube.com/@ygkkk
- 小白AI笔记: https://www.youtube.com/@xiaobaiAINotes

### GitHub项目
- yonggekkk/sing-box-yg: Sing-box一键脚本
- yonggekkk/argosbx: ArgoSBX小钢炮脚本
- 2dust/v2rayN: V2rayN客户端

### 客户端下载
- V2rayN: https://github.com/2dust/v2rayN
- Clash Verge: https://github.com/clash-verge-rev/clash-verge-rev
- Nekobox: https://github.com/MatsuriDayo/Nekobox

---

## ⚠️ 注意事项

1. **法律合规**: 本知识库仅供技术研究和学习使用，请遵守当地法律法规
2. **定期更新**: 建议定期重新爬取博客获取最新教程
3. **备份配置**: 重要配置请备份到本地，防止丢失
4. **安全第一**: 不要在不安全的网络上输入敏感信息

---

## 📝 更新日志

- 2026-10-20: 初始版本，爬取ygkkk博客4篇文章
- 2026-10-20: 添加知识库索引和常见问题解决方案
