# ui_modules/output_ui/output_modules/sensitivity_analysis_panel.py

import os
import streamlit as st
import importlib.util

MODULE_META = {
    "title": "敏感性分析面板",
    "category": "经济分析",
    "order": 4
}

CHILD_MODULE_FOLDER = "ui_modules/output_ui/output_modules/sensitivity_charts"

def load_child_modules(folder_path):
    modules = []
    if not os.path.exists(folder_path):
        return modules

    for file in os.listdir(folder_path):
        if file.endswith(".py"):
            module_path = os.path.join(folder_path, file)
            module_name = os.path.splitext(file)[0]
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
                if hasattr(mod, "render_chart"):
                    modules.append(mod)
            except Exception as e:
                st.warning(f"❌ 子模块 `{module_name}` 加载失败：{e}")
    return modules

def render():
    # st.markdown("### 📊 敏感性分析图表面板")

    modules = load_child_modules(CHILD_MODULE_FOLDER)
    if not modules:
        st.warning("⚠️ 未找到任何敏感性图表子模块，请在 `sensitivity_charts/` 文件夹中添加子模块。")
        return

    for mod in modules:
        try:
            mod.render_chart()
        except Exception as e:
            st.error(f"模块 `{mod.__name__}` 渲染失败：{e}")
