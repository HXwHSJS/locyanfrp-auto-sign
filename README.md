# LoCyanFrp Auto Sign (Windows + OAuth)

一个面向 **LoCyanFrp** 的 Windows 自动签到项目。

## 功能

- OAuth ` access_token`
- `GET /sign` -> `POST /sign`
- 主备 API 自动切换
- 401 后自动重取 token 
- Windows 单实例锁，避免并发运行
- 成功、失败桌面右上角提示( + 常驻错误窗口）
<img width="400" height="100" alt="image" src="https://github.com/user-attachments/assets/cce05aa0-e1f6-4c9f-a2ca-81e0290a09e2" />
<img width="470" height="130" alt="image" src="https://github.com/user-attachments/assets/59e8a428-c2da-44c1-b996-7554da91bede" />
<img width="620" height="370" alt="image" src="https://github.com/user-attachments/assets/8761cd8a-4650-4ae1-9748-8dfc77054783" />
- `logs/auto_sign.log` 和 `last_status.json`

## 目录结构

```text
locyanfrp-auto-sign/
├─ auto_sign.py
├─ get_refresh_token.py
├─ config.example.json
├─ requirements.txt
├─ .gitignore
└─ README.md
```

## 环境要求

- Windows 10 / 11
- 项目编写环境为Python 3.9+
- 已在 LoCyanFrp 网站创建 OAuth 应用

## 第 1 步：准备 OAuth 应用

在 LoCyanFrp 网站后台准备一个 OAuth 应用，并确认你知道自己的 `app_id`。
<img width="901" height="715" alt="image" src="https://github.com/user-attachments/assets/ea58395a-59f6-4fe0-8056-561e2765b459" />


建议申请的最小权限：

- `Sign.Read`
- `Sign.Action.Sign`

## 第 2 步：克隆项目(或者下载zip文件)

```powershell
git clone https://github.com/HXwHSJS/locyanfrp-auto-sign.git
cd locyanfrp-auto-sign
```
<img width="690" height="249" alt="image" src="https://github.com/user-attachments/assets/0f06d5c7-ae23-4006-a67d-3834d0db7c22" />


## 第 3 步：安装依赖

-本项目只依赖一个第三方库：`requests`.

```powershell
py -m pip install -r requirements.txt
```
-你可以先检查是否已安装
```powershell
py -c "import requests; print(requests.__version__)" 
```
<img width="786" height="47" alt="image" src="https://github.com/user-attachments/assets/7b2d4d07-5c64-417f-b55b-efa0bd2f8dc4" />


## 第 4 步：生成本地配置文件

复制示例配置：

```powershell
copy config.example.json config.json
```
<img width="615" height="227" alt="image" src="https://github.com/user-attachments/assets/538078ba-7dd7-4229-a1a1-01ab0e2afab5" />


然后编辑 `config.json`。

最少先填好：

```json
{
  "app_id": "你的应用ID",
  "refresh_token": ""
}
```
<img width="310" height="324" alt="image" src="https://github.com/user-attachments/assets/d72949c9-c44f-4a20-b897-5b2c7827cb93" />

> `refresh_token` 先留空，下一步会自动写入。

## 第 5 步：获取一次性授权 code

浏览器打开下面的链接，把 `你的应用ID` 改成你的 `app_id`：

```text
https://dashboard.locyanfrp.cn/auth/oauth/authorize?client_id=你的应用ID&scopes=Sign.Read,Sign.Action.Sign&mode=code
```
<img width="596" height="634" alt="image" src="https://github.com/user-attachments/assets/43d2e813-39d1-4182-aa4c-8c35e0649941" />
授权成功后，页面会给你一个一次性 `code`。
<img width="469" height="304" alt="image" src="https://github.com/user-attachments/assets/4d13cc88-7024-49ae-8353-c28a473abaa3" />

## 第 6 步：把 code 换成 refresh_token

运行：

```powershell
py get_refresh_token.py
```

按提示粘贴 `code`。
<img width="530" height="68" alt="image" src="https://github.com/user-attachments/assets/96d13d21-0ea3-4fa7-b77e-513a841ddc28" />

成功后，脚本会自动把 `refresh_token` 写进 `config.json`。
<img width="838" height="184" alt="image" src="https://github.com/user-attachments/assets/ab619d31-2ee9-4a3a-af13-accc66af8ced" />

## 第 7 步：手动测试

运行：

```powershell
py auto_sign.py
```

正常情况下，你会看到以下结果之一：

- 今日已签到，无需重复操作
- 签到成功
- 明确的错误信息

示例：
<img width="1199" height="250" alt="image" src="https://github.com/user-attachments/assets/60849ffb-45a3-4e0c-a1e8-b26a071824b9" />

日志文件在：

```text
logs\auto_sign.log
```
<img width="636" height="352" alt="image" src="https://github.com/user-attachments/assets/47d8b916-6d05-4c00-aca8-081197ee1c4f" />
<img width="652" height="43" alt="image" src="https://github.com/user-attachments/assets/d446abdd-1a31-4b22-acfb-b23a3dfe2d28" />


状态文件在：

```text
last_status.json
```
注意：状态文件仅记录最后一次签到日志，log文件记录完整日志。

## 第 8 步：测试提醒功能

### 成功提醒

```powershell
py auto_sign.py --test-success
```
<img width="400" height="100" alt="image" src="https://github.com/user-attachments/assets/cce05aa0-e1f6-4c9f-a2ca-81e0290a09e2" />

### 失败提醒

```powershell
py auto_sign.py --test-failure
```
<img width="470" height="130" alt="image" src="https://github.com/user-attachments/assets/59e8a428-c2da-44c1-b996-7554da91bede" />
<img width="620" height="370" alt="image" src="https://github.com/user-attachments/assets/8761cd8a-4650-4ae1-9748-8dfc77054783" />

你应该会看到：

- 成功：绿色短提醒
- 失败：右上角红提示 + 下方常驻错误窗口

## 第 9 步：配置 Windows 计划任务
<img width="1188" height="792" alt="image" src="https://github.com/user-attachments/assets/3a48ebd2-5a46-486a-9309-83d77cd6e58f" />

推荐配置：

### 常规

- 名称：`LoCyanFrp Auto Sign`（建议选项，随意）
- 仅当用户登录时运行
- 可选：使用最高权限运行
<img width="646" height="547" alt="image" src="https://github.com/user-attachments/assets/e27e61ef-14b9-4fc7-b661-17df4426f59d" />

### 触发器
- 1.新建
- 2.按预定计划
- 3.每天（根据自己时段）
- 4.勾选“已启用”
<img width="605" height="523" alt="image" src="https://github.com/user-attachments/assets/0119977d-e7ec-42be-8559-081177b57ede" />

### 操作

**程序或脚本：**

```text
你的 python.exe 绝对路径
```

例如：

```text
H:\Tools\Python\3.9.8\python.exe
```

**添加参数：**

```text
auto_sign.py
```

**起始于：**

```text
项目目录绝对路径
```

例如：

```text
H:\LocyanSign
```
<img width="468" height="507" alt="image" src="https://github.com/user-attachments/assets/24a40518-ab4b-45c3-a1ec-d2da58b9fffc" />

### 条件
如果是笔记本，建议取消勾选“只有在计算机使用交流电源时才启动此任务”
<img width="646" height="547" alt="image" src="https://github.com/user-attachments/assets/a94ecb3e-06ff-4cd5-a7c4-3e18e34b3fd4" />

### 设置

- 允许按需运行任务
- 如果过了计划开始时间，立即启动任务
- 如果任务失败：30 分钟后重试 1 次
- 如果任务已经在运行：**请勿启动新实例**
- <img width="646" height="547" alt="image" src="https://github.com/user-attachments/assets/b257538a-303e-4d59-8e09-3a33d6b6fd80" />


## 配置项说明

打开 `config.json`，常见字段如下：

### `traffic_unit`签到单位（LocyanFrp牛逼）

```json
"traffic_unit": "GB"
```

用于提示文案展示单位。

### 成功/失败提醒开关

```json
"notify_on_success": true, 
"notify_on_already_signed": false,
"notify_on_failure": true
```

- `notify_on_success`：签到成功是否提示
- `notify_on_already_signed`：今天已签到是否提示
- `notify_on_failure`：失败是否提示

### 弹窗位置

```json
"popup_right_margin": 20,
"popup_top": 40,
"popup_stack_gap": 10
```

- `popup_right_margin`：距离右边的边距
- `popup_top`：距离顶部的边距
- `popup_stack_gap`：红提示与常驻窗口之间的间距

## 建议

首次部署完成后，先手动运行一次，再配置计划任务。

- 这是第三方项目，不是 LoCyanFrp 官方项目
- 用户需要自行承担使用风险（API都写了，可能不会有事？LocyanFrp牛逼）
- 请勿把自己的 token 上传到 GitHub

## 常见问题

### 1. 执行 `py -m pip install -r requirements.txt` 时提示 SSL EOF / 无法连接 PyPI

这通常是本机网络、代理、证书或 PyPI 连接问题，不是本项目脚本本身的问题。

你可以先执行：

```powershell
py -c "import requests; print(requests.__version__)"
如果已经安装了 requests，并且版本不低于 2.15.0，可以直接跳过依赖安装，继续执行后续步骤。
```
