# Git 双平台同步配置指南 (Gitee & GitHub)

本项目已配置完成，支持通过单条命令将本地代码同时推送到 **Gitee** 和 **GitHub**。

## 🛠️ 环境配置说明

本地已完成以下远程仓库绑定：
- `origin` 指向 Gitee 仓库
- `github` 指向 GitHub 仓库

为了简化推送流程，我们配置了一个自定义别名 `pushall`。其底层执行逻辑为：
`git push origin master` && `git push github master`

