# SwanLab-Server Authentication System

本文档介绍 SwanLab-Server 的账号认证系统，包括密码登录、JWT令牌管理和GitHub OAuth登录。

## 目录

- [功能特性](#功能特性)
- [快速开始](#快速开始)
- [数据库设计](#数据库设计)
- [API文档](#api文档)
- [配置说明](#配置说明)
- [使用示例](#使用示例)
- [安全建议](#安全建议)

## 功能特性

### ✅ 已实现功能

1. **账号密码认证**
   - 用户注册（自动创建默认工作空间）
   - 密码加密存储（bcrypt + salt）
   - 登录验证
   - JWT访问令牌（1小时有效期）
   - JWT刷新令牌（7天有效期）
   - 令牌刷新机制
   - 令牌撤销（登出）

2. **OAuth认证**
   - GitHub登录支持
   - 账号关联（GitHub账号链接到已有账号）
   - 自动注册（首次GitHub登录创建账号）
   - 用户信息同步（头像、邮箱等）

3. **租户管理**
   - 多租户支持（Multi-tenancy）
   - 工作空间管理
   - 用户-租户关联
   - 角色管理（owner, admin, member, viewer）

4. **安全特性**
   - 密码加盐哈希
   - JWT令牌认证
   - Redis令牌缓存
   - 账号状态管理（active, pending, banned）
   - CSRF保护（OAuth state参数）

## 快速开始

### 1. 安装依赖

```bash
cd /path/to/SwanLab-Server
pip install -r requirements.txt
```

新增的依赖包括：
- `passlib[bcrypt]` - 密码哈希
- `PyJWT` - JWT令牌
- `python-jose[cryptography]` - JWT加密
- `redis` - 缓存
- `httpx` - HTTP客户端（OAuth）

### 2. 配置环境变量

复制环境变量示例文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下关键变量：

```bash
# JWT配置
JWT_SECRET_KEY=your-very-secure-secret-key-here
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=604800

# Redis配置
REDIS_URL=redis://localhost:6379/0

# GitHub OAuth配置（可选）
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_REDIRECT_URI=http://localhost:22224/api/v1/oauth/github/callback
```

### 3. 初始化数据库表

创建认证相关的数据库表：

```bash
python -m swanboard.db.mysql.init_auth_tables create
```

### 4. 启动服务

```bash
python -m swanboard.run
```

服务将在 `http://localhost:5173` 启动。

### 5. 访问API文档

打开浏览器访问：
- Swagger UI: `http://localhost:5173/api/docs`
- ReDoc: `http://localhost:5173/api/redoc`

## 数据库设计

### 表结构

#### 1. `accounts` - 账号表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) | 主键，UUID |
| email | VARCHAR(255) | 邮箱，唯一 |
| password | VARCHAR(255) | 哈希后的密码 |
| password_salt | VARCHAR(255) | 密码盐值 |
| name | VARCHAR(100) | 用户名 |
| avatar | VARCHAR(500) | 头像URL |
| status | VARCHAR(20) | 状态：active/pending/banned |
| current_tenant_id | VARCHAR(36) | 当前活跃的租户ID |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |
| last_login_at | DATETIME | 最后登录时间 |

#### 2. `tenants` - 租户表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) | 主键，UUID |
| name | VARCHAR(100) | 租户名称 |
| description | TEXT | 描述 |
| owner_id | VARCHAR(36) | 所有者账号ID |
| settings | TEXT | JSON格式的设置 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### 3. `tenant_account_joins` - 租户-账号关联表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) | 主键，UUID |
| tenant_id | VARCHAR(36) | 租户ID |
| account_id | VARCHAR(36) | 账号ID |
| role | VARCHAR(20) | 角色：owner/admin/member/viewer |
| current | BOOLEAN | 是否为当前活跃租户 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### 4. `account_integrates` - OAuth集成表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) | 主键，UUID |
| account_id | VARCHAR(36) | 关联的账号ID |
| provider | VARCHAR(20) | OAuth提供商：github/google |
| open_id | VARCHAR(255) | 第三方用户ID |
| access_token | TEXT | 访问令牌 |
| provider_username | VARCHAR(100) | 第三方用户名 |
| provider_email | VARCHAR(255) | 第三方邮箱 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### 5. `refresh_tokens` - 刷新令牌表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | VARCHAR(36) | 主键，UUID |
| account_id | VARCHAR(36) | 账号ID |
| token | VARCHAR(500) | 刷新令牌 |
| ip_address | VARCHAR(50) | IP地址 |
| user_agent | VARCHAR(500) | 用户代理 |
| is_revoked | BOOLEAN | 是否已撤销 |
| created_at | DATETIME | 创建时间 |
| expires_at | DATETIME | 过期时间 |

## API文档

### 认证API (`/api/v1/auth`)

#### 1. 用户注册

**POST** `/api/v1/auth/register`

注册新账号并返回JWT令牌。

**请求体：**
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "name": "John Doe"
}
```

**响应：**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### 2. 用户登录

**POST** `/api/v1/auth/login`

使用邮箱和密码登录。

**请求体：**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**响应：** 同注册接口

#### 3. 刷新令牌

**POST** `/api/v1/auth/refresh`

使用刷新令牌获取新的访问令牌。

**请求体：**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**响应：**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### 4. 获取当前用户信息

**GET** `/api/v1/auth/me`

获取当前登录用户的信息（需要认证）。

**请求头：**
```
Authorization: Bearer <access_token>
```

**响应：**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "avatar": "https://...",
  "status": "active",
  "current_tenant_id": "uuid",
  "created_at": "2025-01-01T00:00:00",
  "last_login_at": "2025-01-15T10:30:00"
}
```

#### 5. 登出

**POST** `/api/v1/auth/logout`

撤销刷新令牌，登出用户。

**请求头：**
```
Authorization: Bearer <access_token>
```

**请求体：**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### OAuth API (`/api/v1/oauth`)

#### 1. GitHub登录授权

**GET** `/api/v1/oauth/github/authorize`

获取GitHub OAuth授权URL。

**响应：**
```json
{
  "authorization_url": "https://github.com/login/oauth/authorize?...",
  "state": "csrf-token"
}
```

#### 2. GitHub OAuth回调

**GET** `/api/v1/oauth/github/callback?code=xxx&state=xxx`

GitHub OAuth回调处理（由GitHub自动调用）。

**响应：**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600,
  "is_new_user": true,
  "account_id": "uuid"
}
```

#### 3. GitHub直接登录（重定向）

**GET** `/api/v1/oauth/github`

直接重定向到GitHub授权页面。

## 配置说明

### JWT配置

```bash
# JWT密钥 - 生产环境必须使用强密钥！
JWT_SECRET_KEY=your-secret-key-change-this-in-production

# JWT算法
JWT_ALGORITHM=HS256

# 访问令牌有效期（秒）
JWT_ACCESS_TOKEN_EXPIRES=3600  # 1小时

# 刷新令牌有效期（秒）
JWT_REFRESH_TOKEN_EXPIRES=604800  # 7天
```

### Redis配置

```bash
# Redis连接URL
REDIS_URL=redis://localhost:6379/0

# Redis密码（可选）
REDIS_PASSWORD=your_redis_password
```

### GitHub OAuth配置

在 [GitHub Developer Settings](https://github.com/settings/developers) 创建OAuth应用：

1. **Application name**: SwanLab Server
2. **Homepage URL**: `http://localhost:22224`
3. **Authorization callback URL**: `http://localhost:22224/api/v1/oauth/github/callback`

获取 Client ID 和 Client Secret 后，配置：

```bash
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_REDIRECT_URI=http://localhost:22224/api/v1/oauth/github/callback
```

## 使用示例

### Python客户端示例

```python
import requests

BASE_URL = "http://localhost:22224/api/v1"

# 1. 注册账号
response = requests.post(f"{BASE_URL}/auth/register", json={
    "email": "test@example.com",
    "password": "secure_password123",
    "name": "Test User"
})
tokens = response.json()
access_token = tokens["access_token"]
refresh_token = tokens["refresh_token"]

# 2. 使用访问令牌调用受保护的API
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
user_info = response.json()
print(f"Logged in as: {user_info['name']}")

# 3. 刷新访问令牌
response = requests.post(f"{BASE_URL}/auth/refresh", json={
    "refresh_token": refresh_token
})
new_tokens = response.json()
access_token = new_tokens["access_token"]

# 4. 登出
requests.post(f"{BASE_URL}/auth/logout",
              headers={"Authorization": f"Bearer {access_token}"},
              json={"refresh_token": refresh_token})
```

### JavaScript/前端示例

```javascript
const BASE_URL = 'http://localhost:22224/api/v1';

// 1. 登录
async function login(email, password) {
  const response = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  const tokens = await response.json();

  // 保存到localStorage
  localStorage.setItem('access_token', tokens.access_token);
  localStorage.setItem('refresh_token', tokens.refresh_token);

  return tokens;
}

// 2. 调用受保护的API
async function getProfile() {
  const accessToken = localStorage.getItem('access_token');
  const response = await fetch(`${BASE_URL}/auth/me`, {
    headers: { 'Authorization': `Bearer ${accessToken}` }
  });
  return await response.json();
}

// 3. 刷新令牌
async function refreshToken() {
  const refreshToken = localStorage.getItem('refresh_token');
  const response = await fetch(`${BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken })
  });
  const tokens = await response.json();
  localStorage.setItem('access_token', tokens.access_token);
  return tokens;
}

// 4. GitHub登录
async function loginWithGitHub() {
  // 获取授权URL
  const response = await fetch(`${BASE_URL}/oauth/github/authorize`);
  const data = await response.json();

  // 重定向到GitHub
  window.location.href = data.authorization_url;
}

// 5. 处理GitHub回调（在回调页面）
async function handleGitHubCallback() {
  const params = new URLSearchParams(window.location.search);
  const code = params.get('code');
  const state = params.get('state');

  if (code) {
    // 后端会自动处理，前端获取返回的tokens
    // 实际使用中需要设计前后端交互流程
  }
}
```

### cURL示例

```bash
# 注册
curl -X POST http://localhost:22224/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","name":"Test User"}'

# 登录
curl -X POST http://localhost:22224/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# 获取用户信息
curl -X GET http://localhost:22224/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"

# 刷新令牌
curl -X POST http://localhost:22224/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token>"}'
```

## 安全建议

### 生产环境必做事项

1. **更改默认密钥**
   ```bash
   # 生成安全的JWT密钥
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **使用HTTPS**
   - 在生产环境必须使用HTTPS
   - 配置SSL证书
   - 启用HSTS

3. **配置CORS**
   ```bash
   CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
   ```

4. **数据库安全**
   - 使用强密码
   - 限制数据库访问
   - 定期备份

5. **Redis安全**
   - 设置Redis密码
   - 限制Redis访问
   - 使用加密连接

### 密码策略

可通过环境变量配置：

```bash
MIN_PASSWORD_LENGTH=8
REQUIRE_SPECIAL_CHAR=true
```

### 令牌管理

- 访问令牌短期有效（默认1小时）
- 刷新令牌长期有效（默认7天）
- 登出时撤销刷新令牌
- 定期清理过期令牌

### 账号保护

- 实现登录失败限制（TODO）
- 可疑登录通知（TODO）
- 两步验证（TODO）

## 故障排查

### 常见问题

#### 1. 数据库连接失败

检查MySQL配置：
```bash
# 测试数据库连接
mysql -h $MYSQL_HOST -P $MYSQL_PORT -u $MYSQL_USER -p$MYSQL_PASSWORD
```

#### 2. Redis连接失败

检查Redis服务：
```bash
redis-cli -h localhost -p 6379 ping
```

#### 3. GitHub OAuth失败

- 检查GITHUB_CLIENT_ID和GITHUB_CLIENT_SECRET是否正确
- 确认GITHUB_REDIRECT_URI与GitHub应用设置一致
- 检查网络连接

#### 4. JWT令牌无效

- 检查JWT_SECRET_KEY是否一致
- 令牌是否过期
- 令牌是否被撤销

## 数据库维护

### 创建表

```bash
python -m swanboard.db.mysql.init_auth_tables create
```

### 删除表（危险操作）

```bash
python -m swanboard.db.mysql.init_auth_tables drop
```

### 重建表

```bash
python -m swanboard.db.mysql.init_auth_tables recreate
```

## 扩展功能（计划中）

- [ ] Google OAuth支持
- [ ] 邮箱验证
- [ ] 密码重置
- [ ] 两步验证（2FA）
- [ ] API Key管理
- [ ] 登录历史记录
- [ ] 账号操作日志
- [ ] 租户管理UI
- [ ] 权限细粒度控制

## 技术栈

- **Web框架**: FastAPI
- **ORM**: Peewee
- **数据库**: MySQL
- **缓存**: Redis
- **密码哈希**: passlib + bcrypt
- **JWT**: python-jose
- **HTTP客户端**: httpx

## 参考资料

- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [GitHub OAuth Documentation](https://docs.github.com/en/developers/apps/building-oauth-apps)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)