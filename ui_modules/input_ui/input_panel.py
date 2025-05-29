import streamlit as st
import os
import yaml
import pandas as pd

PARAM_SCHEMA_DIR = "ui_modules/input_ui/input_param_modules"
INPUT_RECORD_FILE = "user_inputs.yaml"
IRRADIATION_CSV_PATH = "ui_modules/input_ui/input_param_modules/solar_insolation_city.csv"  # 新增

# 加载 YAML
def load_yaml(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# 保存输入数据
def save_inputs(data):
    with open(INPUT_RECORD_FILE, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)

# 渲染联动省市 + 年辐射量
def render_solar_module(module_name, schema):
    df = pd.read_csv(IRRADIATION_CSV_PATH)

    provinces = sorted(df["省份"].unique())
    default_province = schema["参数"]["省份"].get("default", provinces[0])
    if default_province in provinces:
        province_index = provinces.index(default_province)
    else:
        province_index = 0
    selected_province = st.selectbox("省份", provinces, index=province_index)

    cities = sorted(df[df["省份"] == selected_province]["城市"].unique())
    default_city = schema["参数"]["城市"].get("default", cities[0])
    if default_city in cities:
        city_index = cities.index(default_city)
    else:
        city_index = 0
    selected_city = st.selectbox("城市", cities, index=city_index)

    # 获取年辐射量
    matched_row = df[(df["省份"] == selected_province) & (df["城市"] == selected_city)]
    irradiation = float(matched_row["年辐射量"].values[0]) if not matched_row.empty else 0.0
    st.markdown(f"**年辐射量**: `{irradiation} kWh/m²`")

    # 存储联动结果
    st.session_state["inputs"][module_name] = {
        "省份": selected_province,
        "城市": selected_city,
        "年辐射量": irradiation,  # ✅ 现在是 float 类型
    }

    # 渲染其余通用参数
    for key, param in schema["参数"].items():
        if key in ["省份", "城市"]:
            continue
        label = param.get("label", key)
        default = param.get("default", "")
        param_type = param.get("type", "number")
        full_key = f"{module_name}__{key}"

        if param_type == "number":
            min_val = param.get("min", 0.0)
            max_val = param.get("max", 1e6)
            value = st.number_input(label, min_value=min_val, max_value=max_val,
                                    value=default, key=full_key)
        elif param_type == "slider":
            min_val = param.get("min", 0.0)
            max_val = param.get("max", 1.0)
            step = param.get("step", 0.01)
            value = st.slider(label, min_value=min_val, max_value=max_val,
                              value=default, step=step, key=full_key)
        else:
            value = st.text_input(label, value=default, key=full_key)

        st.session_state["inputs"][module_name][key] = value

# 主渲染入口
def render_input_panel():
    st.sidebar.title("参数输入模块")

    if "inputs" not in st.session_state:
        st.session_state["inputs"] = {}

    param_files = sorted([
        f for f in os.listdir(PARAM_SCHEMA_DIR)
        if f.endswith(".yaml")
    ])

    for file_name in param_files:
        module_name = os.path.splitext(file_name)[0]
        schema = load_yaml(os.path.join(PARAM_SCHEMA_DIR, file_name))

        if schema is None or "参数" not in schema:
            st.warning(f"⚠️ 文件 `{file_name}` 格式不正确或缺少 '参数' 字段。")
            continue

        with st.sidebar.expander(schema.get("模块名", module_name), expanded=True):
            if module_name not in st.session_state["inputs"]:
                st.session_state["inputs"][module_name] = {}

            # 特殊处理：光伏发电参数
            if schema.get("模块名") == "光伏发电参数":
                render_solar_module(module_name, schema)
                continue

            # 通用处理逻辑
            for key, param in schema["参数"].items():
                label = param.get("label", key)
                default = param.get("default", "")
                param_type = param.get("type", "number")
                full_key = f"{module_name}__{key}"

                if param_type == "number":
                    min_val = param.get("min", 0.0)
                    max_val = param.get("max", 1e6)
                    value = st.number_input(label, min_value=min_val, max_value=max_val,
                                            value=default, key=full_key)
                elif param_type == "select":
                    options = param.get("options", [])
                    value = st.selectbox(label, options,
                                         index=options.index(default) if default in options else 0,
                                         key=full_key)
                elif param_type == "slider":
                    min_val = param.get("min", 0.0)
                    max_val = param.get("max", 1.0)
                    step = param.get("step", 0.01)
                    value = st.slider(label, min_value=min_val, max_value=max_val,
                                      value=default, step=step, key=full_key)
                else:
                    value = st.text_input(label, value=default, key=full_key)

                st.session_state["inputs"][module_name][key] = value

    save_inputs(st.session_state["inputs"])
