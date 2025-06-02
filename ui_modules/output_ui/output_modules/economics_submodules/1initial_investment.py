import streamlit as st
import yaml
import os

# 模块元信息
MODULE_META = {
    "order": 1,
    "title": "初始投入计算"
}

# 假设 YAML 文件位于项目根目录或已知路径中
YAML_PATH = os.path.abspath("user_inputs.yaml")
OUTPUT_YAML_PATH = os.path.abspath("user_outputs.yaml")


def load_yaml_data(yaml_path):
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        st.error(f"❌ 无法加载 YAML 文件：{e}")
        return None


def save_to_output_yaml(output_data, output_path):
    try:
        if os.path.exists(output_path):
            with open(output_path, "r", encoding="utf-8") as f:
                existing_data = yaml.safe_load(f) or {}
        else:
            existing_data = {}

        # 更新数据
        existing_data.update(output_data)

        with open(output_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(existing_data, f, allow_unicode=True)

        # st.info("✅ 初始投入结果已保存到 user_outputs.yaml")
    except Exception as e:
        st.error(f"❌ 保存到 YAML 文件失败：{e}")


def render():
    st.subheader("💰 初始投入计算")

    data = load_yaml_data(YAML_PATH)
    if not data:
        return

    try:
        # 读取参数
        solar_area = data["2光伏发电参数"]["太阳能板面积（㎡）"]
        panel_price = data["3项目建设参数配置"]["光伏组件价格"]
        inverter_price = data["3项目建设参数配置"]["逆变器总价"]
        install_cost_per_m2 = data["3项目建设参数配置"]["安装费用"]
        design_cost = data["3项目建设参数配置"]["方案设计成本"]
        decision_cost = data["3项目建设参数配置"]["项目决策成本"]
        other_initial_cost = data["3项目建设参数配置"]["其他初期费用"]

        # 计算
        equipment_cost = panel_price * solar_area + inverter_price
        install_cost = install_cost_per_m2 * solar_area
        total_investment = decision_cost + design_cost + equipment_cost + install_cost + other_initial_cost

        # 显示计算过程（使用非折叠显示，避免嵌套错误）
        st.markdown("#### 📋 详细计算过程")
        st.write(f"🔹 光伏组件价格 × 面积：{panel_price} × {solar_area} = {panel_price * solar_area:.2f} 元")
        st.write(f"🔹 逆变器总价：{inverter_price} 元")
        st.write(f"🔹 安装费用 × 面积：{install_cost_per_m2} × {solar_area} = {install_cost:.2f} 元")
        st.write(f"🔹 项目决策成本：{decision_cost} 元")
        st.write(f"🔹 方案设计成本：{design_cost} 元")
        st.write(f"🔹 其他初期费用：{other_initial_cost} 元")

        # 总结果
        st.success(f"💡 **初始投入总计：{total_investment:,.2f} 元**")

    except KeyError as e:
        st.error(f"❌ YAML 数据中缺失字段：{e}")
    except Exception as e:
        st.error(f"❌ 计算过程中出错：{e}")

    # 构造保存数据结构
    output_data = {
        "初始投入计算": {
            "光伏组件费用": round(panel_price * solar_area, 2),
            "逆变器费用": round(inverter_price, 2),
            "设备费合计": round(equipment_cost, 2),
            "安装费用": round(install_cost, 2),
            "方案设计成本": round(design_cost, 2),
            "项目决策成本": round(decision_cost, 2),
            "其他初期费用": round(other_initial_cost, 2),
            "初始投入总计": round(total_investment, 2)
        }
    }

    # 保存结果
    save_to_output_yaml(output_data, OUTPUT_YAML_PATH)


