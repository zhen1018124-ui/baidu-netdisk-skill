# 贡献指南

感谢您对本项目的兴趣！本文档将帮助您了解如何贡献代码。

## 开发流程

### 1. Fork 和 Clone

```bash
git clone https://github.com/YOUR_USERNAME/baidu-netdisk-skill.git
cd baidu-netdisk-skill
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux / macOS
# 或
venv\\Scripts\\activate    # Windows
```

### 3. 安装开发依赖

```bash
pip install -e .
pip install -r requirements-dev.txt
```

### 4. 创建功能分支

```bash
git checkout -b feature/your-feature-name
```

### 5. 开发和测试

```bash
# 运行测试
pytest tests/ -v

# 代码检查
flake8 scripts/baidu_pcs.py
black scripts/baidu_pcs.py --check
mypy scripts/baidu_pcs.py --ignore-missing-imports
```

### 6. 提交 PR

- 提交 PR 到 `master` 分支
- 标题格式：`feat:` / `fix:` / `docs:` / `test:`
- 在 PR 描述中说明改动内容和测试覆盖

## 代码规范

- Python 3.7+ 兼容
- 使用 PEP 8 规范（通过 black 格式化）
- 添加类型提示（type hints）
- 为新功能添加单元测试
- 更新相关文档

## 提交消息格式

使用 Conventional Commits 格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

示例：

```
feat(upload): 支持分片上传大于 4GB 的文件

实现三层分片上传流程，支持断点续传。

Closes #123
```

## 优先贡献方向

- [ ] 分片上传支持（>4GB 文件）
- [ ] 错误码中文速查表完善
- [ ] Windows .exe 发行版
- [ ] GitHub/Gitee Release 自动发版
- [ ] Chrome 扩展版
- [ ] 并发上传支持
- [ ] 断点续传功能

## 许可证

贡献即同意本项目 MIT 许可证。
