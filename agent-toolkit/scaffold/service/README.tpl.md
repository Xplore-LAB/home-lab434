# Service

> 长期运行的服务 / API / 后端 / 守护进程

## 约定
- 服务配置放 `config/`
- 启动脚本放 `scripts/`
- 日志目录 `logs/`
- 按端口或用途命名子目录
- 统一在 README 写明启动/停止/日志位置

## 模板
```
service/
├── README.md
├── config/
├── scripts/
└── logs/
```
