# 文件路径：ui_modules/output_ui/output_modules/originality_statement.py

import streamlit as st

MODULE_META = {
    "title": "独创性声明",
    "category": "声明类",
    "order": 1
}

def render():
    st.markdown("""
    <div style='font-size: 28px; font-weight: bold;'>🧾 独创性声明</div>
    <hr>

    🔬 本项目为 <span style='font-weight:bold;'>《农村光伏项目经济性评估工具》</span> 的核心组成部分，包含的架构设计、数据流处理、经济模型构建与可视化界面等，均为作者原创开发。未经许可，不得抄袭、转载或用于商业用途。

    ✍️ 除另有注明之第三方资源或引用部分外，其余代码与逻辑均为原创。我们欢迎在开源协议范围内进行非商业使用，包括科研、教学和公益探索。

    ---

    <div style='font-size: 22px; font-weight: bold;'>👤 作者信息</div>

    - **姓名**：鲁棒研究生（Galvanize）  
    - **邮箱**：3191653970@qq.com  
    - **项目名称**：农村光伏项目经济性评估工具  
    - **GitHub**：[github.com/GavinWang2023/solar-project](https://github.com/GavinWang2023/solar-project)  
    - **最后更新日期**：2025年6月2日  

    ---

    <div style='font-size: 22px; font-weight: bold;'>📜 版权与许可协议</div>

    本项目采用 **MIT 开源协议**，你可以自由地使用、修改与分发本工具，前提是必须保留本声明和许可证副本。

    > “Empowering Rural Sustainability through Transparent Economics.”

    ---
    <div style='text-align:center;'>
        <img src='https://img.shields.io/badge/license-MIT-green' style='margin-right: 10px;'>
        <img src='https://img.shields.io/badge/python-3.9+-blue'>
        <img src='https://img.shields.io/badge/platform-Streamlit-orange'>
    </div>
    """, unsafe_allow_html=True)
