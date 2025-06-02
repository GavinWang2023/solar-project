# 文件路径：ui_modules/output_ui/output_modules/economic_summary.py

import streamlit as st
import importlib.util
import os
import glob

# 必要元信息
MODULE_META = {
    "category": "经济分析",
    "order": 2,
    "title": "项目经济性分析"
}

# 子模块文件夹路径
SUBMODULE_FOLDER = os.path.join(
    os.path.dirname(__file__), "economics_submodules"
)

def load_submodule(file_path):
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
    # st.header("")

    if not os.path.exists(SUBMODULE_FOLDER):
        st.warning("未找到子模块文件夹 economics_submodules/")
        return

    module_files = sorted(glob.glob(os.path.join(SUBMODULE_FOLDER, "*.py")))
    modules_to_render = []

    for file_path in module_files:
        module_name, module = load_submodule(file_path)
        if module is None:
            continue

        if not hasattr(module, "render") or not hasattr(module, "MODULE_META"):
            st.warning(f"⚠️ 子模块 `{module_name}` 缺少 `render()` 或 `MODULE_META`，已跳过。")
            continue

        meta = module.MODULE_META
        order = meta.get("order", 999)
        title = meta.get("title", module_name)

        modules_to_render.append({
            "order": order,
            "title": title,
            "render_fn": module.render
        })

    # 排序后渲染
    modules_sorted = sorted(modules_to_render, key=lambda x: x["order"])
    for mod in modules_sorted:
        with st.expander(f"📌 {mod['title']}", expanded=True):
            try:
                mod["render_fn"]()
            except Exception as e:
                st.error(f"❌ 渲染模块 `{mod['title']}` 时出错：{e}")
