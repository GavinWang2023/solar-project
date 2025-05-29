import streamlit as st
import numpy_financial as npf
import matplotlib.pyplot as plt
import yaml
import os

USER_INPUT_PATH = "user_inputs.yaml"


MODULE_META = {
    "title": "经济效益分析",
    "category": "分析结果",
    "order": 2
}

# 设置中文字体（Windows 默认使用 SimHei，Mac/Linux 可换为适配字体）
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


# 内嵌的参数加载功能（替代 param_loader.py）
def load_user_inputs(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        st.error(f"加载用户输入失败: {e}")
        return {}


# 核心经济测算函数
def calculate_cashflow(user_inputs: dict) -> dict:
    solar = user_inputs["2光伏发电参数"]
    project = user_inputs["3项目建设参数配置"]
    finance = user_inputs["4经济分析方法参数配置"]
    rent = user_inputs["5出租屋顶方式参数配置"]

    # 总年辐射量 = 年单位面积辐射量 × 面积
    irradiation_unit = solar["年辐射量"]
    panel_area = solar["太阳能板面积（㎡）"]
    total_irradiation = irradiation_unit * panel_area

    efficiency = solar["太阳能板转换效率（η）"]
    pr = solar["系统效率因子（PR）"]
    annual_generation = total_irradiation * efficiency * pr

    # 初始投资
    install_cost = panel_area * project["安装费用"]
    panel_cost = panel_area * project["光伏组件价格"]
    inverter_cost = project["逆变器总价"]
    other_cost = project["其他初期费用"]
    total_investment = install_cost + panel_cost + inverter_cost + other_cost

    # 收益构成
    self_use_kwh = min(project["年自用电量"], annual_generation)
    self_use_saving = self_use_kwh * project["购电电价"]

    sell_kwh = max(0, annual_generation - self_use_kwh)
    sell_income = sell_kwh * project["售电电价"]

    subsidy = project["年补贴金额"]
    subsidy_years = project["补贴年限"]

    maintenance = project["年运维成本"]
    rent_cost = rent["屋顶出租面积"] * rent["屋顶租金单价"] if rent["屋顶租金单价"] > 0 else 0

    # 年现金流
    years = int(finance["产品使用寿命"])
    cash_flows = [-total_investment]
    for i in range(1, years + 1):
        income = self_use_saving + sell_income
        if i <= subsidy_years:
            income += subsidy
        cash_flow = income - maintenance - rent_cost
        cash_flows.append(cash_flow)

    # 经济指标
    discount_rate = finance["折现率"] / 100
    npv = npf.npv(discount_rate, cash_flows)
    try:
        irr = npf.irr(cash_flows)
    except:
        irr = None

    return {
        "初始投资": total_investment,
        "总年辐射量": total_irradiation,
        "年发电量": annual_generation,
        "年自用收益": self_use_saving,
        "年售电收益": sell_income,
        "年补贴": subsidy,
        "年净现金流": cash_flows[1:],
        "NPV": npv,
        "IRR": irr,
        "Cashflow": cash_flows,
    }


# 渲染分析界面
def render():
    st.markdown("## 💰 经济分析结果")

    user_inputs = load_user_inputs(USER_INPUT_PATH)
    if not user_inputs:
        st.warning("⚠️ 未能加载用户参数数据。")
        return

    try:
        results = calculate_cashflow(user_inputs)
    except Exception as e:
        st.error(f"计算失败：{e}")
        return

    # 核心经济指标
    st.markdown("### 📊 核心经济指标")
    st.table({
        "初始投资 (元)": round(results["初始投资"], 2),
        "总年辐射量 (kWh/m² × ㎡)": round(results["总年辐射量"], 2),
        "年发电量 (kWh)": round(results["年发电量"], 2),
        "年净现金流平均值 (元)": round(sum(results["年净现金流"]) / len(results["年净现金流"]), 2),
        "NPV (元)": round(results["NPV"], 2),
        "IRR (%)": f"{results['IRR'] * 100:.2f}" if results['IRR'] is not None else "无法计算"
    })

    # 年度净现金流柱状图
    st.markdown("### 📈 年度净现金流（柱状图）")
    fig1, ax1 = plt.subplots()
    ax1.bar(range(1, len(results["年净现金流"]) + 1), results["年净现金流"], color="#4CAF50")
    ax1.set_xlabel("年份")
    ax1.set_ylabel("净现金流 (元)")
    ax1.set_title("年度净现金流柱状图")
    ax1.grid(True, linestyle='--', alpha=0.6)
    st.pyplot(fig1)

    # 年度净现金流折线图
    st.markdown("### 📉 年度净现金流（折线图）")
    fig2, ax2 = plt.subplots()
    ax2.plot(range(1, len(results["年净现金流"]) + 1), results["年净现金流"], marker='o', color="#2196F3", label="净现金流")
    ax2.axhline(0, color='gray', linestyle='--')
    ax2.set_xlabel("年份")
    ax2.set_ylabel("净现金流 (元)")
    ax2.set_title("年度净现金流折线图")
    ax2.grid(True, linestyle='--', alpha=0.6)
    ax2.legend()
    st.pyplot(fig2)

    # 累计净现金流图
    st.markdown("### 📊 累计净现金流")
    cumulative = [sum(results["年净现金流"][:i+1]) for i in range(len(results["年净现金流"]))]
    fig3, ax3 = plt.subplots()
    ax3.plot(range(1, len(cumulative) + 1), cumulative, marker='o', color="#FF9800", label="累计净现金流")
    ax3.axhline(0, color='gray', linestyle='--')
    ax3.set_xlabel("年份")
    ax3.set_ylabel("累计净现金流 (元)")
    ax3.set_title("累计净现金流趋势图")
    ax3.grid(True, linestyle='--', alpha=0.6)
    ax3.legend()
    st.pyplot(fig3)
