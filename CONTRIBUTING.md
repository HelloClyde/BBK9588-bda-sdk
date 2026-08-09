# Contributing

本项目同时包含公开 SDK 和逆向研究。提交时必须保持两者边界，不能把静态猜测直接变成
开发者可调用的 API。

## 开始前

```powershell
python -m pip install -e ".[dev]"
.\scripts\setup_toolchain.ps1
.\scripts\verify_sdk.ps1 -SkipToolchainSetup
```

## 证据等级

- `confirmed`：真机已完成调用、清理并返回菜单闭环。
- `emulator`：8013 完整 NAND 模拟器已动态通过，尚不承诺真机。
- `static`：来自反汇编、交叉引用或结构分析。
- `probe`：已有测试程序，但行为或生命周期仍不完整。
- `guess`：不得用于公开 API 的名称、签名或文档结论。

静态和 probe 内容放入 `reverse/`。API 只有满足
[`docs/verified/public_api_policy.md`](docs/verified/public_api_policy.md) 后，才能加入
`sdk/include/`、`docs/` 和 `example/`。

## 提交规则

1. 公开 wrapper 使用动态系统函数表，不引入未经证明的固件绝对地址。
2. 新 API 同时提交独立示例、验证日志摘要、适用环境、清理顺序和失败边界。
3. 更新 `docs/compatibility.md`，模拟器结果与真机结果分开记录。
4. 不提交固件、NAND、原机 BDA、DLX、字典、音频、工具链或本地设备数据。
5. 生成物默认放在 `build/`；仅 `example/**/*.bda` 可作为已验证示例提交。
6. 不重写无关研究记录，不清理他人的本地实验文件。

## Pull Request

PR 描述应说明改动范围、证据等级、测试命令和设备风险。提交前运行：

```powershell
python -m unittest discover -s reverse -p "test_*.py"
git diff --check
git status --short
```

除非贡献者明确书面标记为 `Not a Contribution`，有意提交并被项目接收的贡献将按
`Apache-2.0 OR GPL-2.0-only` 双许可证授权，不附加额外条款。贡献者必须有权提交相关
代码、文档或测试数据；固件和原机版权资源不能作为贡献提交。
