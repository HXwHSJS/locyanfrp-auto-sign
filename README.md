# LoCyanFrp Auto Sign (Windows + OAuth)

一个面向 **LoCyanFrp** 的 Windows 自动签到项目。

## 功能

- OAuth ` access_token`
- `GET /sign` -> `POST /sign`
- 主备 API 自动切换
- 401 后自动重取 token 
- Windows 单实例锁，避免并发运行
- 成功轻提醒
- 失败右上角红提示 + 常驻错误窗口
- 写入 `logs/auto_sign.log` 和 `last_status.json`

## 目录结构

```text
locyanfrp-auto-sign-template/
├─ auto_sign.py
├─ get_refresh_token.py
├─ config.example.json
├─ requirements.txt
├─ .gitignore
└─ README.md
```

## 环境要求

- Windows 10 / 11
- Python 3.9+
- 已在 LoCyanFrp 网站创建 OAuth 应用

## 第 1 步：准备 OAuth 应用

在 LoCyanFrp 网站后台准备一个 OAuth 应用，并确认你知道自己的 `app_id`。

建议申请的最小权限：

- `Sign.Read`
- `Sign.Action.Sign`

## 第 2 步：克隆项目

```powershell
git clone <你的仓库地址>
cd locyanfrp-auto-sign-template
```

## 第 3 步：安装依赖

```powershell
py -m pip install -r requirements.txt
```

## 第 4 步：生成本地配置文件

复制示例配置：

```powershell
copy config.example.json config.json
```

然后编辑 `config.json`。

最少先填好：

```json
{
  "app_id": "你的应用ID",
  "refresh_token": ""
}
```

> `refresh_token` 先留空，下一步会自动写入。

## 第 5 步：获取一次性授权 code

浏览器打开下面的链接，把 `你的应用ID` 改成你的 `app_id`：

```text
https://dashboard.locyanfrp.cn/auth/oauth/authorize?client_id=你的应用ID&scopes=Sign.Read,Sign.Action.Sign&mode=code
```

授权成功后，页面会给你一个一次性 `code`。

## 第 6 步：把 code 换成 refresh_token

运行：

```powershell
py get_refresh_token.py
```

按提示粘贴 `code`。

成功后，脚本会自动把 `refresh_token` 写进 `config.json`。

## 第 7 步：手动测试

运行：

```powershell
py auto_sign.py
```

正常情况下，你会看到以下结果之一：

- 今日已签到，无需重复操作
- 签到成功
- 明确的错误信息

日志文件在：

```text
logs\auto_sign.log
```

状态文件在：

```text
last_status.json
```

## 第 8 步：测试提醒功能

### 成功提醒

```powershell
py auto_sign.py --test-success
```

### 失败提醒

```powershell
py auto_sign.py --test-failure
```

你应该会看到：

- 成功：绿色短提醒
- 失败：右上角红提示 + 下方常驻错误窗口

## 第 9 步：配置 Windows 计划任务

推荐配置：

### 常规

- 名称：`LoCyanFrp Auto Sign`
- 仅当用户登录时运行
- 可选：使用最高权限运行

### 触发器

- 每天一次
- 例如 `09:00`

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

### 设置

- 允许按需运行任务
- 如果错过计划时间，尽快运行任务
- 如果任务失败：30 分钟后重试 1 次
- 如果任务已经在运行：**不要启动新实例**

## 配置项说明

打开 `config.json`，常见字段如下：

### `traffic_unit`

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

## 不要提交到 GitHub 的文件

这些内容只应该保留在本地，已经在 `.gitignore` 中处理：

- `config.json`
- `logs/`
- `last_status.json`
- `auto_sign.lock`

## 建议

首次部署完成后，先手动运行一次，再配置计划任务。

如果你准备公开发布这个项目，建议在 README 中明确说明：

- 这是第三方示例项目，不是 LoCyanFrp 官方项目
- 用户需要自行承担使用风险
- 请勿把自己的 token 上传到 GitHub
