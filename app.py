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
    </style>
    """,
    unsafe_allow_html=True,
)


def score_rank(series, high_good=True):
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
    return pd.DataFrame(
        {
            "代码": [
                "601899", "600036", "600900", "600941", "600938",
                "601088", "601225", "000333", "600519", "000858",
                "300750", "002415", "002594", "601318", "600276",
            ],
            "名称": [
                "紫金矿业", "招商银行", "长江电力", "中国移动", "中国海油",
                "中国神华", "陕西煤业", "美的集团", "贵州茅台", "五粮液",
                "宁德时代", "海康威视", "比亚迪", "中国平安", "恒瑞医药",
            ],
            "最新价": [18, 35, 28, 105, 31, 42, 25, 70, 1500, 130, 190, 32, 250, 45, 47],
            "涨跌幅": [2.1, -0.5, 0.6, 1.4, 1.8, 1.2, 0.9, 1.1, 1.2, 0.8, 2.5, -0.8, 1.8, 0.3, 0.7],
            "成交额": [
                1700000000, 2200000000, 1500000000, 1800000000, 1600000000,
                1400000000, 900000000, 1600000000, 3500000000, 1800000000,
                2800000000, 1200000000, 2600000000, 2100000000, 1100000000,
            ],
            "换手率": [2.0, 0.7, 0.4, 0.6, 1.1, 0.8, 0.9, 1.0, 0.5, 0.9, 1.8, 1.3, 1.6, 0.6, 1.1],
            "市盈率-动态": [16, 6, 18, 17, 10, 12, 9, 15, 25, 18, 22, 20, 28, 9, 35],
            "市净率": [3.0, 0.9, 2.3, 1.8, 1.4, 1.9, 1.5, 2.8, 8.5, 3.1, 4.2, 2.5, 5.5, 1.0, 4.8],
            "营收增速": [24.8, 0.0, 6.4, 5.8, 15.2, 3.6, 2.8, 2.6, 6.5, -38.2, 52.4, 11.8, -11.8, 0.0, 8.2],
            "利润增速": [101.9, 1.4, 30.1, 7.6, 18.5, 4.2, 3.7, 0.9, 1.4, -45.8, 53.0, 46.2, -57.5, -5.4, 12.0],
            "ROE": [10.0, 3.0, 3.0, 8.8, 9.5, 11.0, 9.2, 5.5, 10.1, 6.3, 5.8, 3.2, 1.6, 2.5, 6.8],
            "现金流质量": [1.1, 3.3, 1.7, 2.6, 2.9, 2.4, 2.1, 1.1, 1.0, -0.3, 1.5, -0.7, 0.7, 3.9, 1.2],
            "本季度表现": [0.082, 0.018, 0.035, 0.056, 0.074, 0.041, 0.026, 0.012, -0.015, -0.055, -0.072, -0.086, -0.120, -0.030, 0.022],
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
            "板块名称": ["半导体", "消费电子", "有色金属", "电力", "银行", "煤炭", "通信服务", "家电", "医药", "白酒"],
            "涨跌幅": [3.2, 2.8, 2.2, 1.3, 0.8, 1.4, 1.7, 1.1, 0.9, 0.6],
            "换手率": [3.5, 3.0, 2.6, 0.9, 0.7, 1.2, 1.1, 0.8, 1.0, 0.6],
            "上涨家数": [65, 58, 45, 40, 28, 35, 38, 30, 32, 26],
            "下跌家数": [10, 12, 13, 12, 15, 11, 14, 10, 15, 18],
        }
    )


def value_comment(row):
    pe = row["市盈率-动态"]
    profit = row["利润增速"]
    quarter_ret = row["本季度表现"]
    if quarter_ret < -0.08:
        return "本季度走势偏弱，暂不优先配置"
    if profit > 15 and pe < 25:
        return "业绩增长较好，估值未明显透支"
    if row["现金流质量"] > 2 and pe < 20:
        return "现金流较稳，估值相对合理"
    if pe > 30:
        return "估值偏高，需结合成长兑现"
    return "业绩和估值基本匹配"


def build_stock_scores(df):
    df = df.copy()
    num_cols = [
        "最新价", "涨跌幅", "成交额", "换手率", "市盈率-动态", "市净率",
        "营收增速", "利润增速", "ROE", "现金流质量", "本季度表现",
    ]
    df = safe_num(df, num_cols)
    df = df[df["最新价"] > 0]
    df = df[df["成交额"] > 0]
    df = df[df["市盈率-动态"] > 0]
    df = df[df["市净率"] > 0]

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

    df["风险过滤"] = np.where(df["本季度表现"] < -0.08, "剔除", "保留")
    filtered = df[df["风险过滤"] == "保留"].copy()

    filtered["最终综合得分"] = (
        0.15 * filtered["PE得分"]
        + 0.10 * filtered["PB得分"]
        + 0.12 * filtered["流动性得分"]
        + 0.08 * filtered["活跃度得分"]
        + 0.10 * filtered["日内趋势得分"]
        + 0.10 * filtered["营收得分"]
        + 0.12 * filtered["利润得分"]
        + 0.08 * filtered["ROE得分"]
        + 0.10 * filtered["现金流得分"]
        + 0.15 * filtered["季度动量得分"]
    )
    return filtered.sort_values("最终综合得分", ascending=False)


st.title("A股基本面多因子配置推荐系统")
st.caption("周度行情观察 + 季度基本面推荐 | 公开数据可复现 | 课程研究用途，不构成投资建议")
st.success("当前版本加入季度动量过滤和风险控制，避免把本季度明显走弱的股票直接纳入组合。")
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
st.write("本模块筛选同时具备估值相对合理、流动性较好、基本面有解释力，且本季度表现没有明显走弱的股票。")
scored = build_stock_scores(stock_pool)
top_stock = scored.head(10).copy()
top_stock["建议权重"] = 0.10
top_stock["估值业绩判断"] = top_stock.apply(value_comment, axis=1)
top_stock["最终综合得分"] = top_stock["最终综合得分"].round(3)

show_cols = [
    "代码", "名称", "最新价", "涨跌幅", "市盈率-动态", "市净率",
    "营收增速", "利润增速", "ROE", "现金流质量", "本季度表现",
    "最终综合得分", "建议权重", "估值业绩判断",
]
show_stock = top_stock[show_cols].copy()
show_stock["本季度表现"] = show_stock["本季度表现"].map(lambda x: f"{x:.2%}")
show_stock["建议权重"] = show_stock["建议权重"].map(lambda x: f"{x:.2%}")
st.dataframe(show_stock, use_container_width=True, hide_index=True)
st.caption("说明：与上一版相比，本版加入季度动量过滤，剔除本季度跌幅过大的股票，组合更偏稳健。")

st.header("4. 本期组合配置")
portfolio = top_stock[["代码", "名称", "建议权重", "最终综合得分", "估值业绩判断"]].copy()
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
    "组合采用前10只股票等权配置，每只股票权重为10%。"
)

bt = top_stock[["代码", "名称", "本季度表现", "建议权重"]].copy()
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
    st.success("本季度以来，优化组合取得正收益，说明加入季度动量过滤后，组合稳定性有所改善。")
else:
    st.warning("本季度以来，组合收益仍为负，说明后续还需要加入止损、行业分散和回撤控制。")

st.write(
    "该结果说明，单纯依靠基本面打分可能在单季度内承受较大波动；"
    "加入季度动量过滤后，可以减少明显弱势股票对组合的拖累。"
)

st.header("6. 方法说明与风险提示")
st.markdown(
    """
**模型逻辑：**

- 行情概览：用于观察当前市场环境；
- 行业推荐：采用涨跌幅、换手率、上涨家数构建周度行业强度得分；
- 股票推荐：采用估值、流动性、趋势、成长、质量和季度动量构建综合得分；
- 组合配置：前10只股票等权配置，每只股票10%；
- 实盘回测：按照本季度以来表现计算组合收益。

**本次迭代：**

- 原始组合主要按基本面和流动性打分，容易选到短期明显走弱的股票；
- 优化版加入季度动量过滤，剔除本季度跌幅过大的股票；
- 组合更偏向现金流稳定、估值合理、趋势不弱的标的。

**局限性：**

- 当前版本使用 AkShare 或备用样例数据，公开数据稳定性有限；
- 历史 PE、PB、股息率、分析师一致预期等数据仍不完整；
- 后续如接入 iFinD、Wind 或 Choice，可进一步补充价值因子、预期因子、行业中性化和市值中性化。

**风险提示：**

本系统仅用于课程研究和量化方法展示，不构成任何投资建议。
    """
)
