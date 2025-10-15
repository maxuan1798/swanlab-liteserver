# SwanLab-Server 认证系统实现总结

## ✅ 实现完成

基于 Flask + Redis + MySQL 架构，参考 Dify 的认证逻辑，成功实现了完整的用户认证系统。

## 📁 新增文件列表

### 1. 数据库模型 (Database Models)
```
swanboard/db/mysql/
├── auth_models.py          # 认证相关数据库模型
└── init_auth_tables.py     # 数据库表初始化脚本
```

**新增表：**
- `accounts` - 用户账号表
- `tenants` - 租户/工作空间表
- `tenant_account_joins` - 用户-租户关联表
- `account_integrates` - OAuth集成表
- `refresh_tokens` - 刷新令牌表

### 2. 业务服务 (Services)
```
swanboard/services/
├── __init__.py
├── auth_service.py         # 认证服务（密码哈希、JWT令牌）
└── oauth_service.py        # OAuth服务（GitHub/Google登录）
```

### 3. 配置文件 (Configuration)
```
swanboard/config/
├── __init__.py
└── auth_config.py          # 认证配置类
```

### 4. API路由 (Routes)
```
swanboard/router/
├── auth.py                 # 认证API路由
└── oauth.py                # OAuth API路由
```

### 5. 文档和示例 (Documentation & Examples)
```
docs/
└── AUTHENTICATION.md       # 完整的认证系统文档

examples/
└── auth_example.py         # Python客户端使用示例
```

### 6. 配置更新
- `requirements.txt` - 新增认证依赖包
- `.env.example` - 新增认证相关环境变量
- `swanboard/app.py` - 注册认证路由

## 🔑 核心功能

### 1. 账号密码认证
- ✅ 用户注册（带自动创建默认工作空间）
- ✅ 密码加密存储（bcrypt + salt）
- ✅ 用户登录验证
- ✅ JWT访问令牌（默认1小时有效）
- ✅ JWT刷新令牌（默认7天有效）
- ✅ 令牌刷新机制
- ✅ 用户登出（撤销令牌）

### 2. OAuth第三方登录
- ✅ GitHub OAuth登录支持
- ✅ 账号自动关联（GitHub账号链接到已有SwanLab账号）
- ✅ 新用户自动注册
- ✅ 用户信息同步（头像、邮箱等）
- ⏳ Google OAuth（预留接口，待实现）

### 3. 租户管理（Multi-tenancy）
- ✅ 多租户支持
- ✅ 工作空间自动创建
- ✅ 用户-租户关联
- ✅ 角色管理（owner/admin/member/viewer）
- ✅ 当前活跃租户切换

### 4. 安全特性
- ✅ 密码加盐哈希（bcrypt）
- ✅ JWT令牌认证
- ✅ 刷新令牌存储（数据库 + Redis可选）
- ✅ 账号状态管理（active/pending/banned）
- ✅ OAuth CSRF保护（state参数）
- ✅ 令牌过期处理

## 📡 API端点

### 认证API (`/api/v1/auth`)
- `POST /auth/register` - 用户注册
- `POST /auth/login` - 用户登录
- `POST /auth/refresh` - 刷新访问令牌
- `POST /auth/logout` - 用户登出
- `GET /auth/me` - 获取当前用户信息
- `GET /auth/health` - 健康检查

### OAuth API (`/api/v1/oauth`)
- `GET /oauth/github/authorize` - 获取GitHub授权URL
- `GET /oauth/github/callback` - GitHub回调处理
- `GET /oauth/github` - 直接重定向到GitHub授权
- `GET /oauth/google/*` - Google OAuth（预留）

## 🛠 技术栈

| 组件 | 技术 |
|------|------|
| Web框架 | FastAPI |
| ORM | Peewee |
| 数据库 | MySQL |
| 缓存 | Redis |
| 密码哈希 | passlib + bcrypt |
| JWT | python-jose |
| HTTP客户端 | httpx |

## 📦 新增依赖

```txt
passlib[bcrypt]>=1.7.4
PyJWT>=2.8.0
redis>=4.6.0
httpx>=0.25.0
python-jose[cryptography]>=3.3.0
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd /path/to/SwanLab-Server
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `.env` 文件：

```bash
# JWT配置
JWT_SECRET_KEY=your-very-secure-secret-key
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=604800

# Redis配置
REDIS_URL=redis://localhost:6379/0

# GitHub OAuth（可选）
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
```

### 3. 初始化数据库

```bash
python -m swanboard.db.mysql.init_auth_tables create
```

### 4. 启动服务

```bash
python -m swanboard.run
```

### 5. 测试API

访问 API 文档：
- Swagger UI: http://localhost:5173/api/docs
- ReDoc: http://localhost:5173/api/redoc

或运行测试脚本：
```bash
python examples/auth_example.py
```

## 📊 数据库ER图

```
┌─────────────┐
│  accounts   │
│  (用户表)   │
└──────┬──────┘
       │
       │ 1:N
       │
┌──────▼──────────────┐
│ account_integrates  │
│   (OAuth集成)       │
└─────────────────────┘

┌─────────────┐          ┌──────────────────────┐          ┌─────────────┐
│  accounts   │          │ tenant_account_joins │          │   tenants   │
│  (用户表)   ├─────────▶│   (关联表 N:M)       │◀─────────┤  (租户表)   │
└─────────────┘          └──────────────────────┘          └─────────────┘

┌─────────────┐
│  accounts   │
│  (用户表)   │
└──────┬──────┘
       │
       │ 1:N
       │
┌──────▼──────────┐
│ refresh_tokens  │
│  (令牌表)       │
└─────────────────┘
```

## 🔐 安全建议

### 生产环境必做

1. **更改默认JWT密钥**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **使用HTTPS**
   - 配置SSL证书
   - 启用HSTS

3. **配置CORS**
   ```bash
   CORS_ORIGINS=https://yourdomain.com
   ```

4. **数据库安全**
   - 使用强密码
   - 限制访问权限
   - 定期备份

5. **Redis安全**
   - 设置密码
   - 限制网络访问

## 📝 使用示例

### Python

```python
from examples.auth_example import SwanLabAuthClient

client = SwanLabAuthClient("http://localhost:22224/api/v1")

# 注册
client.register("user@example.com", "password123", "User Name")

# 登录
client.login("user@example.com", "password123")

# 获取信息
profile = client.get_profile()

# 刷新令牌
client.refresh()

# 登出
client.logout()
```

### JavaScript/前端

```javascript
// 登录
const response = await fetch('/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});
const { access_token, refresh_token } = await response.json();

// 调用API
const profile = await fetch('/api/v1/auth/me', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
```

### cURL

```bash
# 注册
curl -X POST http://localhost:22224/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","name":"Test"}'

# 登录
curl -X POST http://localhost:22224/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

## 🎯 下一步计划

### 待实现功能
- [ ] Google OAuth支持
- [ ] 邮箱验证
- [ ] 密码重置
- [ ] 两步验证（2FA）
- [ ] API Key管理
- [ ] 登录历史
- [ ] 操作日志
- [ ] 登录失败限制
- [ ] 可疑登录通知

### 优化建议
- [ ] 添加单元测试
- [ ] 性能测试和优化
- [ ] 错误处理完善
- [ ] 日志记录增强
- [ ] 监控告警集成

## 📚 参考文档

- [完整文档](docs/AUTHENTICATION.md) - 详细的API文档和使用指南
- [使用示例](examples/auth_example.py) - Python客户端示例代码
- [环境配置](.env.example) - 环境变量配置示例

## 🐛 故障排查

### 常见问题

1. **数据库连接失败**
   - 检查MySQL服务是否运行
   - 验证环境变量配置

2. **Redis连接失败**
   - 检查Redis服务状态
   - 验证REDIS_URL配置

3. **GitHub OAuth失败**
   - 确认CLIENT_ID和CLIENT_SECRET
   - 检查REDIRECT_URI配置
   - 验证GitHub应用设置

4. **JWT令牌无效**
   - 检查JWT_SECRET_KEY
   - 确认令牌未过期
   - 验证令牌格式

## ✨ 总结

已成功实现完整的账号认证系统，包括：

1. ✅ 账号密码登录
2. ✅ JWT令牌管理
3. ✅ GitHub OAuth登录
4. ✅ 租户管理
5. ✅ 完整的API文档
6. ✅ 使用示例和测试代码

系统已经可以投入使用，支持用户注册、登录、OAuth第三方登录、多租户管理等核心功能。

---

**实现时间**: 2025-01-15
**技术栈**: FastAPI + Peewee + MySQL + Redis + JWT
**参考**: Dify认证逻辑