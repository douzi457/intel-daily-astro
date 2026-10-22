# 技术博客知识库 - 搜索指南

## 📊 知识库概览

| 来源 | 文章数 | 主要内容 | 更新频率 |
|-----|-------|---------|---------|
| 甬哥侃侃侃 | 4 | Sing-box脚本、Argo隧道、VPS推荐 | 不定期 |
| 233Boy | 4 | Sing-box图文教程、Cloudflare中转 | 每月 |
| 科技老王 | 4 | VPS评测、S-UI面板、Hysteria2 | 每周 |
| 编程随想 | 0 | 翻墙安全、Tor/I2P深度解析 | 不定期 |

**总计**: 12篇文章，覆盖VPS选购、代理协议、面板配置、故障排查

---

## 🔍 快速检索

### 按问题类型查找

```
IP被封怎么办？      → common_issues.IP被封
端口被封怎么办？    → common_issues.端口被封
速度太慢怎么办？    → common_issues.速度缓慢
连接不稳定？       → common_issues.连接不稳
SSL证书过期？      → common_issues.证书问题
```

### 按协议查找

| 协议 | 推荐场景 | 相关博客 |
|-----|---------|---------|
| Hysteria2 | 低延迟、抗丢包 | ygkkk, kejilaowang |
| Reality | 抗封锁、混淆好 | ygkkk, 233boy |
| Tuic5 | 高带宽、多并发 | ygkkk, kejilaowang |
| Sing-box | 全能、多协议 | 233boy (核心) |
| Xray | 稳定、生态好 | ygkkk |

### 按VPS品牌查找

| 品牌 | 特点 | 价格参考 | 推荐度 |
|-----|------|---------|-------|
| Racknerd | 性价比高 | ~$10/年 | ⭐⭐⭐⭐⭐ |
| 搬瓦工 | CN2 GIA稳定 | ~$49/年起 | ⭐⭐⭐⭐⭐ |
| Vultr | 多机房可选 | ~$2.5/月起 | ⭐⭐⭐⭐ |
| DigitalOcean | 开发者友好 | ~$4/月起 | ⭐⭐⭐ |

---

## 📖 核心教程索引

### Sing-box相关（233Boy/甬哥）

| 文章 | 内容 | 难度 |
|-----|------|-----|
| sing-box一键安装脚本 | 基础安装、20+协议支持 | ⭐ |
| sing-box图文搭建教程 | 详细步骤图解 | ⭐ |
| Cloudflare中转配置 | CDN加速、隐藏IP | ⭐⭐ |
| Argo固定隧道搭建 | 零端口、抗封锁 | ⭐⭐ |

### VPS选购（科技老王/甬哥）

| 文章 | 内容 | 重点 |
|-----|------|-----|
| Racknerd VPS推荐 | 性价比分析、购买流程 | 新手首选 |
| 搬瓦工使用体验 | 十年稳定、CN2 GIA线路 | 稳定优先 |
| VPS怎么选全攻略 | 从折腾到顶级VPN | 进阶参考 |

### 面板配置（科技老王）

| 文章 | 内容 | 功能 |
|-----|------|-----|
| H-UI/S-UI/Hysteria2 | 低配VPS性能最大化 | 面板+协议 |
| TUIC加密方式搭建 | 高性能传输协议 | 高级配置 |
| 3X-UI整合S-UI | 多面板共存管理 | 高级用户 |

---

## 🛠️ 常用命令速查

### Sing-box管理
```bash
# 安装
bash <(curl -Ls https://raw.githubusercontent.com/SagerNet/sing-box/main/sb.sh)

# 添加节点
sb add reality          # Reality协议
sb add hy2              # Hysteria2协议  
sb add tuic             # Tuic5协议
sb add ss auto auto aes-256-gcm  # Shadowsocks

# 查看配置
sb info
sb ip                  # 查看VPS IP

# 重启
sb restart
```

### S-UI面板管理
```bash
# 安装
bash <(curl -Ls https://raw.githubusercontent.com/sprov065/s-ui/master/install.sh)

# 修改配置
nano /usr/local/s-ui/config.json

# 重启服务
systemctl restart s-ui
```

### Cloudflare Argo
```bash
# 安装cloudflared
wget -qO- https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -O cloudflared.deb && sudo dpkg -i cloudflared.deb

# 创建隧道
cloudflared tunnel create my-tunnel
cloudflared tunnel route dns my-tunnel your-domain.com
cloudflared tunnel run my-tunnel
```

---

## 💡 最佳实践建议

### 新手入门路线
1. **购买VPS**: Racknerd $10/年起步
2. **安装脚本**: sing-box一键脚本
3. **配置节点**: Reality或Hysteria2协议
4. **搭配CDN**: Cloudflare中转或Argo隧道
5. **客户端**: Clash Verge (Windows) / v2rayNG (Android)

### 进阶优化路线
1. **优选IP**: 使用CF优选IP或Argo固定隧道
2. **多协议部署**: Hysteria2 + Reality + Tuic5
3. **DNS优化**: AdGuardHome + MosDNS
4. **面板管理**: S-UI多节点统一管理
5. **安全防护**: WARP出站分流、防火墙配置

### 故障排查流程
```
无法连接 → 检查IP是否被封 → 换机房/用Argo
连接慢 → 优选IP/换美西机房 → 开WARP分流
端口封 → 切80/443/用Argo → 换协议
证书错 → 续签SSL/用免费域名 → 面板自动续签
```

---

## 📝 博客更新追踪

### 甬哥博客 (ygkkk.blogspot.com)
- YouTube频道: https://www.youtube.com/@ygkkk
- GitHub: https://github.com/yonggekkk
- 主要更新: Sing-box脚本、Argo隧道、CDN优选IP

### 233Boy (233boy.com)
- 特点: 图文教程详细，适合小白
- 主要更新: sing-box脚本教程、Cloudflare中转
- GitHub捐赠: https://github.com/233boy

### 科技老王 (kejilaowang.com)
- YouTube: https://www.youtube.com/@kejilaowang
- 特点: 实测数据详细，视频教程配套
- 主要更新: VPS评测、面板配置、工具推荐

---

## ⚠️ 注意事项

1. **法律合规**: 本知识库仅供技术研究和学习使用，请遵守当地法律法规
2. **定期更新**: 建议每月重新爬取博客获取最新教程
3. **备份配置**: 重要配置请备份到本地，防止丢失
4. **安全第一**: 不要在不安全的网络上输入敏感信息
5. **版权尊重**: 转载博客内容请标注出处

---

## 🔗 相关资源

- 知识库数据: `knowledge_base/crawled_articles.json`
- 知识库索引: `knowledge_base/knowledge_base_index.json`
- 使用指南: `knowledge_base/USAGE_GUIDE.md`
- 本文件: `knowledge_base/SEARCH_GUIDE.md`
