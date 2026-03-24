# API-Police 提交修改完整操作文档

适用仓库：`https://github.com/Jorwnpay/API-Police/`

---

## 0. 当前状态确认（你现在的状态）

你当前本地仓库状态如下：

- 已是 Git 仓库（已 `git init`）
- 当前分支：`master`
- 远程仓库：未配置

---

## 1. 先绑定远程仓库（建立链接）

在项目根目录执行：

```powershell
git remote add origin https://github.com/Jorwnpay/API-Police.git
```

验证是否绑定成功：

```powershell
git remote -v
```

你应看到类似输出：

- `origin  https://github.com/Jorwnpay/API-Police.git (fetch)`
- `origin  https://github.com/Jorwnpay/API-Police.git (push)`

> 如果命令报错 `remote origin already exists`，说明之前配置过，改为：

```powershell
git remote set-url origin https://github.com/Jorwnpay/API-Police.git
```

---

## 2. 首次提交并推送到 GitHub

### 2.1 查看当前变更（可选）

```powershell
git status
```

### 2.2 添加文件到暂存区

```powershell
git add .
```

### 2.3 提交

```powershell
git commit -m "chore: prepare release and update docs"
```

> 如果提示“nothing to commit”，说明当前没有新改动，可跳过 commit。

### 2.4 推送到远程（当前是 master 分支）

```powershell
git push -u origin master
```

`-u` 只需要第一次使用，它会建立本地分支与远程分支的跟踪关系。

---

## 3. 之后每次更新代码的标准流程

每次改完代码后，执行：

```powershell
git add .
git commit -m "feat: your change summary"
git push
```

如果你之后切换到 `main` 分支，则首次推送改为：

```powershell
git push -u origin main
```

---

## 4. GitHub 认证说明（Windows 常见）

使用 HTTPS 推送时，GitHub 已不支持账号密码，通常会走以下方式之一：

- 浏览器登录授权（Git Credential Manager）
- Personal Access Token（PAT）

如果弹出登录窗口，按提示登录 GitHub 即可。

---

## 5. 常见问题与处理

### 问题 A：`src refspec master does not match any`

原因：当前分支没有任何提交。

处理：先执行一次 commit，再 push。

```powershell
git add .
git commit -m "init: first commit"
git push -u origin master
```

### 问题 B：`remote origin already exists`

处理：更新远程地址。

```powershell
git remote set-url origin https://github.com/Jorwnpay/API-Police.git
```

### 问题 C：`rejected` / `non-fast-forward`

原因：远程已有新提交，本地落后。

处理（常规安全做法）：

```powershell
git pull --rebase origin master
git push
```

---

## 6. 一套可直接执行的最简命令（首次发布）

```powershell
# 在项目根目录执行
git remote add origin https://github.com/Jorwnpay/API-Police.git
git add .
git commit -m "chore: initial publish"
git push -u origin master
```

---

## 7. 发布前快速检查清单

- 已配置 `.gitignore`（已包含 `fingerprints/`）
- 重要文档已更新（README 中英文）
- 本地测试至少跑过一次（如 `pytest -q`）
- `git status` 确认没有误提交文件
