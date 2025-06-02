# stakeholder_analysis.py

import streamlit as st
import importlib.util
import os
import glob

MODULE_META = {
    "category": "经济分析",
    "order": 3,
    "title": "利益相关方经济性分析"
}

# 子模块所在文件夹
SUBMODULE_FOLDER = os.path.join(os.path.dirname(__file__), "stakeholder_modules")

# 加载一个 Python 文件为模块对象
def load_module(file_path):
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        return module_name, module
    except Exception as e:
        st.error(f"❌ 子模块 `{module_name}` 加载失败：{e}")
        return None, None

def render():
    # st.markdown("### 利益相关方经济性分析")

    if not os.path.exists(SUBMODULE_FOLDER):
        st.warning("未找到子模块文件夹 `stakeholder_modules/`，请创建并添加子模块。")
        return

    submodule_files = sorted(glob.glob(os.path.join(SUBMODULE_FOLDER, "*.py")))
    if not submodule_files:
        st.info("暂无可用的利益相关方模块。")
        return

    options = []
    module_map = {}

    for file_path in submodule_files:
        module_name, module = load_module(file_path)
        if module is None:
            continue

        if not hasattr(module, "STAKEHOLDER_META") or not hasattr(module, "render"):
            st.warning(f"模块 `{module_name}` 缺少 `STAKEHOLDER_META` 或 `render()`，已跳过。")
            continue

        label = module.STAKEHOLDER_META.get("label", module_name)
        options.append(label)
        module_map[label] = module

    with st.container():
        # 左上角下拉选择器
        col1, col2 = st.columns([2, 6])
        with col1:
            selected_label = st.selectbox("👥 选择利益相关方", options, key="stakeholder_select")

    # 执行对应模块的 render
    if selected_label and selected_label in module_map:
        module = module_map[selected_label]
        module.render()
