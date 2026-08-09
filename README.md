# BBK 9588 Native BDA SDK

[![SDK CI](https://github.com/HelloClyde/bbk9588-bda-sdk/actions/workflows/sdk-ci.yml/badge.svg)](https://github.com/HelloClyde/bbk9588-bda-sdk/actions/workflows/sdk-ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0%20OR%20GPL--2.0--only-blue.svg)](#license)

面向 BBK / 步步高 9588（C200）和 9688（C100）固件的原生 BDA 开发工具链。
它可以把 freestanding MIPS little-endian C 源码编译成独立 `*.bda`，并提供经过
动态验证的系统 API 头文件、示例和开发文档。

> 当前版本：`0.1.0-alpha.1`。SDK 仍处于逆向验证阶段；模拟器验证不自动等同于
> 真机验证。项目源码、公开头、文档和原创示例使用
> `Apache-2.0 OR GPL-2.0-only` 双许可证。

## 能做什么

- 从 C 源码独立构建 BDA，不依赖或修改已有 BDA 模板
- 生成菜单标题、分类、VX 图标、入口和校验字段
- 静态验证 BDA header、checksum、入口和图标区
- 使用已验证的文件、窗口、绘图、输入、对话框、控件和 raw PCM API
- 通过型号、芯片和机器码三重门禁选择 9588/9688 JZ47xx 录音 profile
- 运行带源码和预编译 BDA 的完整示例，包括触摸十字、控件和扫雷
- 在专用 NAND 副本中自动部署 BDA 到 8013 模拟器

## 快速开始

要求：Windows PowerShell、Python 3.10 或更高版本。当前构建与 CI 以 Windows
为基准；生成的程序面向 MIPS little-endian 固件，不使用宿主系统 C 运行库。

```powershell
git clone --recurse-submodules https://github.com/HelloClyde/bbk9588-bda-sdk.git
cd bbk9588-bda-sdk
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
.\scripts\setup_toolchain.ps1
```

构建并校验第一个 BDA：

```powershell
bda-pack example\basic\hello_world\hello_world_msgbox.c `
  --title HelloWorld --category 9 `
  -o build\HelloWorld.bda

bda-validate build\HelloWorld.bda
```

不安装命令行入口时，也可以使用 `python -m bda_packer` 和
`python -m bda_packer.validate`。工具链或 SDK header 位于自定义目录时，分别设置
`BDA_TOOLCHAIN_PREFIX` 和 `BDA_SDK_INCLUDE`。

## 开发入口

| 目标 | 从这里开始 |
|---|---|
| 完成首次安装和构建 | [入门教程](docs/getting_started.md) |
| 查找已验证 API | [开发文档](docs/README.md) |
| 判断模拟器/真机支持情况 | [兼容性矩阵](docs/compatibility.md) |
| 阅读可运行程序 | [已验证示例](example/README.md) |
| 了解公开 API 准入规则 | [公开 API 策略](docs/verified/public_api_policy.md) |
| 参与逆向验证 | [逆向研究区](reverse/docs/README.md) |

公开应用只应包含 [`sdk/include/`](sdk/include/) 中的头文件。未经完整动态验证的
候选接口位于 `reverse/bda_research_sdk.h`，只能用于探针，不能作为稳定 SDK API。
已验证 API 的附加精确固件绑定会通过公开成熟度字段标明
`STATIC_CANDIDATE`，不能据此宣称对应真机已经通过。

## 项目结构

```text
sdk/include/       已验证的公开 C API；SDK 的稳定边界
bda_packer/        编译、打包、图标生成和静态校验工具
example/           已验证源码及对应预编译 BDA
docs/              开发者 API 文档和教程
scripts/           工具链安装、验证和模拟器部署脚本
reverse/           候选 API、固件分析、探针和研究报告
emu/               硬件级模拟器子模块
.toolchain/         本地 MIPS 工具链缓存（生成内容不提交）
```

普通开发者只需使用前五个目录。`reverse/` 中的命名、ABI 和生命周期可能随新证据
变化；研究结论只有达到公开准入标准后才会迁入 `sdk/include/` 和 `docs/`。

## 验证

运行全量单元测试、文档约束和公开示例编译 smoke：

```powershell
.\scripts\verify_sdk.ps1
```

已安装工具链时可以跳过安装步骤：

```powershell
.\scripts\verify_sdk.ps1 -SkipToolchainSetup
```

测试单个 BDA 的 8013 模拟器部署流程：

```powershell
$env:BBK9588_EMULATOR_ROOT = "E:\bbk9588-emulator-v0.1.5"
.\scripts\test_bda_in_emulator.ps1 .\build\HelloWorld.bda -ResetImage
```

部署脚本只修改模拟器专用 NAND 副本，不修改原始 NAND。真机测试前仍应确认 API
文档中的生命周期、释放顺序和验证环境，尤其是绘图上下文与音频停止流程。

## 数据与安全边界

固件、原机应用、字典数据库、DLX、音频和本地 NAND 不属于本仓库。请只使用你有权
分析和运行的数据，并阅读 [DATA_NOTICE.md](DATA_NOTICE.md)。工具链安装脚本会校验固定
SHA-256；下载的压缩包和解压目录均保持在 Git 忽略范围内。

贡献前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。版本变化见
[CHANGELOG.md](CHANGELOG.md)，安全问题报告方式见 [SECURITY.md](SECURITY.md)。

## License

本项目中有权授权的原创代码、文档和示例采用双许可证，使用者可以任选：

- [Apache License 2.0](LICENSE)
- [GNU General Public License v2 only](LICENSE-GPL-2.0)

SPDX 表达式：`Apache-2.0 OR GPL-2.0-only`。

该许可证不覆盖固件、NAND、原机应用和资源、商标、外部工具链或子模块中的第三方
内容；具体边界见 [NOTICE](NOTICE) 和 [DATA_NOTICE.md](DATA_NOTICE.md)。
