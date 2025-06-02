# 农村光伏项目经济性评估工具

本项目是一个基于 Streamlit 开发的农村光伏项目经济性分析工具，旨在帮助用户评估光伏项目在农村场景下的经济可行性。

## 🎯 功能亮点

- ✅ 初始投资构成与出资结构分析
- ✅ 年度收入与支出动态计算
- ✅ 净现金流与现值分析（考虑折现率与通货膨胀）
- ✅ 利益相关方（农户、企业、村集体等）独立视角分析
- ✅ 敏感性分析与 Tornado 图展示
- ✅ 可视化图表输出与模块化结构，便于扩展

## 📁 项目结构

```
农村光伏项目2.0/
├── app.py                         # Streamlit 主入口
├── user_inputs.yaml               # 用户输入参数
├── user_outputs.yaml              # 模型输出缓存
├── stakeholder_modules/           # 利益相关方分析子模块
├── ui_modules/                    # 输入与输出界面模块
├── sensitivity_log.yaml           # 敏感性分析日志记录
├── .streamlit/                    # Streamlit 配置文件夹
└── README.md                      # 项目说明文件（本文件）
```

## 🚀 使用方法

1. 安装依赖（推荐使用虚拟环境）：

   ```bash
   pip install -r requirements.txt
   ```

2. 运行主程序：

   ```bash
   streamlit run app.py
   ```

## 🧑‍💻 作者

[Gavin Wang](https://github.com/GavinWang2023)  
2025年6月

---

欢迎提出建议或贡献代码！
