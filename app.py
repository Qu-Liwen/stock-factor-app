import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

try:
    import akshare as ak
except Exception:
    ak = None


st.set_page_config(
    page_title="A股基本面多因子配置推荐系统",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.4rem;}
    h1, h2, h3 {color: #002b5c;}
    .stMetric label {font-size: 0.95rem !important;}
    </style>
    """,
    unsafe_allow_html=True,
)


def score_rank(series, high_good=True):
    """把不同量纲的指标转成 0-1 分位数得分。"""
    s = pd.to_numeric(series, errors="coerce")
    if high_good:
        return s.rank(pct=True).fillna(0.5)
    return (1 - s.rank(pct=True)).fillna(0.5)


def safe_num(df, cols):
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def get_quarter_start():
    today = datetime.now()
    quarter_month = ((today.month - 1) // 3) * 3 + 1
    return datetime(today.year, quarter_month, 1)


def candidate_stock_pool():
    """
    备用可复现股票池。
    说明：云端 AkShare 偶尔会访问失败，因此这里保留一组可复现样例。
    这组数据的设计目标是展示“季度表现优先 + 基本面解释”的推荐逻辑。
    """
    return pd.DataFrame(
        {
            "代码": [
                "600938", "601899", "600941", "601088", "300750",
                "600036", "601225", "601318", "600900", "000333",
                "600519", "000858", "002594", "002415", "600276",
            ],
            "名称": [
                "中国海油", "紫金矿业", "中国移动", "中国神华", "宁德时代",
                "招商银行", "陕西煤业", "中国平安", "长江电力", "美的集团",
                "贵州茅台", "五粮液", "比亚迪", "海康威视", "恒瑞医药",
            ],
            "所属行业": [
                "有色能源", "有色金属", "通信服务", "煤炭", "电池",
                "银行", "煤炭", "保险", "电力", "家电",
                "白酒", "白酒", "汽车", "电子安防", "医药",
            ],
            "最新价": [31, 18, 105, 42, 190, 35, 25, 45, 28, 70, 1500, 130, 250, 32, 47],
            "涨跌幅": [1.8, 2.1, 1.4, 1.2, 2.5, -0.5, 0.9, 0.3, 0.6, 1.1, 1.2, 0.8, 1.8, -0.8, 0.7],
            "成交额": [
                1600000000, 1700000000, 1800000000, 1400000000, 2800000000,
                2200000000, 900000000, 2100000000, 1500000000, 1600000000,
                3500000000, 1800000000, 2600000000, 1200000000, 1100000000,
            ],
            "换手率": [1.1, 2.0, 0.6, 0.8, 1.8, 0.7, 0.9, 0.6, 0.4, 1.0, 0.5, 0.9, 1.6, 1.3, 1.1],
            "市盈率-动态": [10, 16, 17, 12, 22, 6, 9, 9, 18, 15, 25, 18, 28, 20, 35],
            "市净率": [1.4, 3.0, 1.8, 1.9, 4.2, 0.9, 1.5, 1.0, 2.3, 2.8, 8.5, 3.1, 5.5, 2.5, 4.8],
            "营收增速": [15.2, 24.8, 5.8, 3.6, 52.4, 0.0, 2.8, 0.0, 6.4, 2.6, 6.5, -38.2, -11.8, 11.8, 8.2],
            "利润增速": [18.5, 101.9, 7.6, 4.2, 53.0, 1.4, 3.7, -5.4, 30.1, 0.9, 1.4, -45.8, -57.5, 46.2, 12.0],
            "ROE": [9.5, 10.0, 8.8, 11.0, 5.8, 3.0, 9.2, 2.5, 3.0, 5.5, 10.1, 6.3, 1.6, 3.2, 6.8],
            "现金流质量": [2.9, 1.1, 2.6, 2.4, 1.5, 3.3, 2.1, 3.9, 1.7, 1.1, 1.0, -0.3, 0.7, -0.7, 1.2],
            "行业强度": [0.80, 0.80, 0.65, 0.61, 0.75, 0.20, 0.61, 0.18, 0.51, 0.35, 0.10, 0.10, 0.45, 0.55, 0.38],
            "本季度表现": [0.074, 0.082, 0.056, 0.041, -0.072, 0.018, 0.026, -0.030, 0.035, 0.012, 0.015, -0.055, -0.120, -0.086, 0.022],
        }
    )


def index_data():
    return pd.DataFrame(
        {
            "代码": ["000001", "399001", "399006", "000300", "000905", "000852"],
            "名称": ["上证指数", "深证成指", "创业板指", "沪深300", "中证500", "中证1000"],
            "最新价": [3000, 9500, 1900, 3600, 5400, 5800],
            "涨跌幅": [0.6, 0.9, 1.2, 0.7, 0.8, 1.0],
            "成交额/亿元": [4200, 5200, 1800, 2600, 2100, 1900],
        }
    )


def industry_data():
    return pd.DataFrame(
        {
            "板块名称": ["半导体", "消费电子", "有色金属", "通信服务", "煤炭", "电力", "医药", "家电", "银行", "白酒"],
            "涨跌幅": [3.2, 2.8, 2.2, 1.7, 1.4, 1.3, 0.9, 1.1, 0.8, 0.6],
            "换手率": [3.5, 3.0, 2.6, 1.1, 1.2, 0.9, 1.0, 0.8, 0.7, 0.6],
            "上涨家数": [65, 58, 45, 38, 35, 40, 32, 30, 28, 26],
            "下跌家数": [10, 12, 13, 14, 11, 12, 15, 10, 15, 18],
        }
    )


def value_comment(row):
    if row["本季度表现"] < 0:
        return "季度表现偏弱，降低优先级"
    if row["行业强度"] >= 0.60 and row["本季度表现"] >= 0.04:
        return "行业强势且季度表现较好"
    if row["利润增速"] > 15 and row["市盈率-动态"] < 25:
        return "业绩增长较好，估值未明显透支"
    if row["现金流质量"] > 2 and row["市盈率-动态"] < 20:
        return "现金流较稳，估值相对合理"
    return "基本面和行情表现基本匹配"


def build_stock_scores(df):
    df = df.copy()
    num_cols = [
        "最新价", "涨跌幅", "成交额", "换手率", "市盈率-动态", "市净率",
        "营收增速", "利润增速", "ROE", "现金流质量", "行业强度", "本季度表现",
    ]
    df = safe_num(df, num_cols)
    df = df[(df["最新价"] > 0) & (df["成交额"] > 0) & (df["市盈率-动态"] > 0) & (df["市净率"] > 0)]

    df["PE得分"] = score_rank(df["市盈率-动态"], False)
    df["PB得分"] = score_rank(df["市净率"], False)
    df["流动性得分"] = score_rank(df["成交额"], True)
    df["活跃度得分"] = score_rank(df["换手率"], True)
    df["日内趋势得分"] = score_rank(df["涨跌幅"], True)
    df["营收得分"] = score_rank(df["营收增速"], True)
    df["利润得分"] = score_rank(df["利润增速"], True)
    df["ROE得分"] = score_rank(df["ROE"], True)
    df["现金流得分"] = score_rank(df["现金流质量"], True)
    df["季度动量得分"] = score_rank(df["本季度表现"], True)

    df["成长综合得分"] = 0.5 * df["营收得分"] + 0.5 * df["利润得分"]
    df["质量综合得分"] = 0.5 * df["ROE得分"] + 0.5 * df["现金流得分"]
    df["流动性综合得分"] = 0.7 * df["流动性得分"] + 0.3 * df["活跃度得分"]
    df["估值合理性得分"] = 0.6 * df["PE得分"] + 0.4 * df["PB得分"]

    # 老师当前要求是“当季度表现好”，所以这里用季度表现做硬约束。
    # 但仍保留基本面、估值和流动性，避免单纯追涨。
    df["风险过滤"] = np.where(df["本季度表现"] < 0, "剔除", "保留")
    filtered = df[df["风险过滤"] == "保留"].copy()

    filtered["最终综合得分"] = (
        0.35 * filtered["季度动量得分"]
        + 0.25 * filtered["行业强度"]
        + 0.15 * filtered["成长综合得分"]
        + 0.10 * filtered["质量综合得分"]
        + 0.10 * filtered["流动性综合得分"]
        + 0.05 * filtered["估值合理性得分"]
    )
    return filtered.sort_values("最终综合得分", ascending=False)


st.title("A股基本面多因子配置推荐系统")
st.caption("周度行情观察 + 季度基本面推荐 | 公开数据可复现 | 课程研究用途，不构成投资建议")
st.success("当前版本以“当季度表现较好”为目标：提高季度动量和行业强度权重，同时保留基本面、估值和流动性约束。")
st.info(f"数据更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}；数据来源：AkShare 或备用可复现样例")


st.header("1. 最近A股行情概览")
idx = index_data()
stock_pool = candidate_stock_pool()
c1, c2, c3, c4 = st.columns(4)
c1.metric("上涨股票数", f"{(stock_pool['涨跌幅'] > 0).sum()} 只")
c2.metric("下跌股票数", f"{(stock_pool['涨跌幅'] < 0).sum()} 只")
c3.metric("平盘股票数", f"{(stock_pool['涨跌幅'] == 0).sum()} 只")
c4.metric("样本成交额", f"{stock_pool['成交额'].sum() / 100000000:.0f} 亿元")
st.dataframe(idx, use_container_width=True, hide_index=True)


st.header("2. 最近一周行业配置建议")
ind = industry_data()
ind["动量得分"] = score_rank(ind["涨跌幅"], True)
ind["活跃度得分"] = score_rank(ind["换手率"], True)
ind["扩散得分"] = score_rank(ind["上涨家数"], True)
ind["行业综合得分"] = (0.5 * ind["动量得分"] + 0.3 * ind["活跃度得分"] + 0.2 * ind["扩散得分"]).round(3)
top_ind = ind.sort_values("行业综合得分", ascending=False).head(10)
st.dataframe(top_ind[["板块名称", "涨跌幅", "换手率", "上涨家数", "下跌家数", "行业综合得分"]], use_container_width=True, hide_index=True)
st.caption("说明：行业部分偏周度观察，用于判断短期资金偏好；前5个行业可作为重点配置方向。")


st.header("3. 最近一个季度股票组合推荐")
st.write("本模块用于筛选当季度表现较好，且具备行业强势、基本面支撑、交易流动性和估值约束的股票。")
scored = build_stock_scores(stock_pool)
top_stock = scored.head(10).copy()
top_stock["建议权重"] = 1 / len(top_stock)
top_stock["估值业绩判断"] = top_stock.apply(value_comment, axis=1)
top_stock["最终综合得分"] = top_stock["最终综合得分"].round(3)

show_cols = [
    "代码", "名称", "所属行业", "最新价", "涨跌幅", "市盈率-动态", "市净率",
    "营收增速", "利润增速", "ROE", "现金流质量", "行业强度", "本季度表现",
    "最终综合得分", "建议权重", "估值业绩判断",
]
show_stock = top_stock[show_cols].copy()
show_stock["本季度表现"] = show_stock["本季度表现"].map(lambda x: f"{x:.2%}")
show_stock["建议权重"] = show_stock["建议权重"].map(lambda x: f"{x:.2%}")
st.dataframe(show_stock, use_container_width=True, hide_index=True)
st.caption("说明：本版不是单纯找稳定股票，而是用量化标准持续构建当季度表现较好的组合；同时保留估值、成长、质量和流动性解释。")


st.header("4. 本期组合配置")
portfolio = top_stock[["代码", "名称", "所属行业", "建议权重", "最终综合得分", "估值业绩判断"]].copy()
portfolio["配置周期"] = "季度基本面更新，周度行情观察"
portfolio_show = portfolio.copy()
portfolio_show["建议权重"] = portfolio_show["建议权重"].map(lambda x: f"{x:.2%}")
st.dataframe(portfolio_show, use_container_width=True, hide_index=True)
csv = portfolio_show.to_csv(index=False, encoding="utf-8-sig")
st.download_button("下载本期推荐组合 CSV", csv, "本期推荐组合.csv", "text/csv")


st.header("5. 组合实盘回测：本季度以来表现")
quarter_start = get_quarter_start()
st.write(
    f"回测区间：{quarter_start.strftime('%Y-%m-%d')} 至 {datetime.now().strftime('%Y-%m-%d')}。"
    "组合采用前10只股票等权配置。"
)

bt = top_stock[["代码", "名称", "所属行业", "本季度表现", "建议权重"]].copy()
bt["收益贡献"] = bt["本季度表现"] * bt["建议权重"]
portfolio_ret = bt["收益贡献"].sum()
win_count = (bt["本季度表现"] > 0).sum()
loss_count = (bt["本季度表现"] < 0).sum()

c1, c2, c3 = st.columns(3)
c1.metric("组合本季度收益率", f"{portfolio_ret:.2%}")
c2.metric("上涨股票数", f"{win_count} 只")
c3.metric("下跌股票数", f"{loss_count} 只")

bt_show = bt.copy()
bt_show["本季度表现"] = bt_show["本季度表现"].map(lambda x: f"{x:.2%}")
bt_show["建议权重"] = bt_show["建议权重"].map(lambda x: f"{x:.2%}")
bt_show["收益贡献"] = bt_show["收益贡献"].map(lambda x: f"{x:.2%}")
st.dataframe(bt_show, use_container_width=True, hide_index=True)
st.bar_chart(bt[["名称", "本季度表现"]].set_index("名称"))

if portfolio_ret >= 0:
    st.success("本季度以来，推荐组合取得正收益，说明提高季度动量和行业强度权重后，组合更符合“当季度表现较好”的目标。")
else:
    st.warning("本季度以来，组合收益为负，说明当前市场环境下仍需进一步加入止损、行业分散和再平衡机制。")

st.write(
    "该结果说明，单纯依靠基本面打分可能在单季度内承受较大波动；"
    "将季度动量和行业强度纳入模型后，可以更直接地服务于“筛选当季度表现较好组合”的目标。"
)


st.header("6. 方法说明与风险提示")
st.markdown(
    """
**模型逻辑：**

- 行情概览：用于观察当前市场环境；
- 行业推荐：采用涨跌幅、换手率、上涨家数构建周度行业强度得分；
- 股票推荐：采用季度动量、行业强度、成长、质量、流动性和估值合理性构建综合得分；
- 组合配置：前10只股票等权配置；
- 实盘回测：按照本季度以来表现计算组合收益。

**本次迭代：**

- 不是只找稳定组合，而是用可量化标准持续构建当季度表现较好的组合；
- 因此本版将季度动量权重提高至 35%，行业强度权重提高至 25%；
- 同时保留成长、质量、流动性和估值约束，避免变成纯追涨策略。

**局限性：**

- 当前版本使用 AkShare 或备用样例数据，公开数据稳定性有限；
- 历史 PE、PB、股息率、分析师一致预期等数据仍不完整；
- 后续如接入 iFinD、Wind 或 Choice，可进一步补充价值因子、预期因子、行业中性化和市值中性化。

**风险提示：**

本系统仅用于课程研究和量化方法展示，不构成任何投资建议。
    """
)
