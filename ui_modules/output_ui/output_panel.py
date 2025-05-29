# output_panel.py
import streamlit as st
import importlib.util
import os
import glob
from collections import defaultdict

OUTPUT_MODULE_FOLDER = "ui_modules/output_ui/output_modules"

def load_module(file_path):
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        return module_name, module
    except Exception as e:
        st.error(f"❌ 模块 `{module_name}` 加载失败：{e}")
        return None, None


def render_output_panel():
    st.title("")

    if not os.path.exists(OUTPUT_MODULE_FOLDER):
        st.info("未找到输出模块文件夹（output_modules/），请创建并添加模块。")
        return

    module_files = sorted(glob.glob(os.path.join(OUTPUT_MODULE_FOLDER, "*.py")))
    if not module_files:
        st.info("暂无可用的输出模块。请将模块文件添加至 output_modules/ 文件夹。")
        return

    # 分类字典
    category_groups = defaultdict(list)

    for file_path in module_files:
        module_name, module = load_module(file_path)
        if module is None:
            continue

        # 判断是否包含 render 函数和 MODULE_META 信息
        if not hasattr(module, "render") or not hasattr(module, "MODULE_META"):
            st.warning(f"模块 `{module_name}` 缺少 `render()` 或 `MODULE_META`，已跳过。")
            continue

        meta = module.MODULE_META
        category = meta.get("category", "其他")
        order = meta.get("order", 999)
        title = meta.get("title", module_name)

        category_groups[category].append({
            "order": order,
            "title": title,
            "render_fn": module.render
        })

    # 排序并渲染每个分类模块
    for category, modules in category_groups.items():
        st.subheader(f"📂 {category}")
        modules_sorted = sorted(modules, key=lambda x: x["order"])
        for mod in modules_sorted:
            with st.expander(f"📌 {mod['title']}", expanded=True):
                mod["render_fn"]()
