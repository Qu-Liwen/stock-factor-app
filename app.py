df = df[df["最新价"] > 0]
df = df[df["成交额"] > 0]
df = df[df["市盈率-动态"] > 0]
df = df[df["市净率"] > 0]

df["PE得分"] = score_rank(df["市盈率-动态"], False)
df["PB得分"] = score_rank(df["市净率"], False)
df["流动性得分"] = score_rank(df["成交额"], True)
df["活跃度得分"] = score_rank(df["换手率"], True)
df["趋势得分"] = score_rank(df["涨跌幅"], True)
df["营收得分"] = score_rank(df["营收增速"], True)
df["利润得分"] = score_rank(df["利润增速"], True)
df["ROE得分"] = score_rank(df["ROE"], True)
df["现金流得分"] = score_rank(df["现金流质量"], True)

df["最终综合得分"] = (
    0.20 * df["PE得分"]
    + 0.15 * df["PB得分"]
    + 0.15 * df["流动性得分"]
    + 0.10 * df["活跃度得分"]
    + 0.10 * df["趋势得分"]
    + 0.10 * df["营收得分"]
    + 0.10 * df["利润得分"]
    + 0.05 * df["ROE得分"]
    + 0.05 * df["现金流得分"]
)

top_stock = df.sort_values("最终综合得分", ascending=False).head(10).copy()
top_stock["建议权重"] = "10.00%"
top_stock["估值业绩判断"] = top_stock.apply(value_comment, axis=1)
top_stock["最终综合得分"] = top_stock["最终综合得分"].round(3)

show_cols = ["代码", "名称", "最新价", "涨跌幅", "市盈率-动态", "市净率", "营收增速", "利润增速", "ROE", "现金流质量", "最终综合得分", "建议权重", "估值业绩判断"]
st.dataframe(top_stock[show_cols], use_container_width=True, hide_index=True)
st.caption("说明：股票推荐综合考虑估值、流动性、趋势和季度基本面，因此更适合按季度更新。")

st.header("4. 本期组合配置")
portfolio = top_stock[["代码", "名称", "建议权重", "最终综合得分", "估值业绩判断"]].copy()
portfolio["配置周期"] = "季度基本面更新，周度行情观察"
st.dataframe(portfolio, use_container_width=True, hide_index=True)

csv = portfolio.to_csv(index=False, encoding="utf-8-sig")
st.download_button("下载本期推荐组合 CSV", csv, "本期推荐组合.csv", "text/csv")

st.header("5. 组合实盘回测：本季度以来表现")

quarter_start = get_current_quarter_start()
start_date = quarter_start.strftime("%Y%m%d")
end_date = datetime.now().strftime("%Y%m%d")

st.write(
    f"本模块用于跟踪当前推荐组合在本季度以来的实际表现。"
    f"回测区间为：{quarter_start.strftime('%Y-%m-%d')} 至 {datetime.now().strftime('%Y-%m-%d')}。"
    "组合采用前10只股票等权配置，每只股票权重为10%。"
)

backtest_list = []
for _, row in top_stock.iterrows():
    ret_info = get_stock_quarter_return(row["代码"], start_date, end_date)
    if ret_info is not None:
        backtest_list.append({
            "代码": row["代码"],
            "名称": row["名称"],
            "期初价格": ret_info["期初价格"],
            "期末价格": ret_info["期末价格"],
            "本季度收益率": ret_info["本季度收益率"],
            "组合权重": 0.10,
            "收益贡献": ret_info["本季度收益率"] * 0.10,
        })

if len(backtest_list) > 0:
    backtest_df = pd.DataFrame(backtest_list)
else:
    st.warning(
        "由于 Streamlit Cloud 云端访问部分 A 股历史行情接口不稳定，当前展示备用回测样例，用于说明组合实盘跟踪方法。"
        "如需获取真实季度收益，可在本地 Python / AkShare 环境运行同一套代码。"
    )
    backtest_df = pd.DataFrame({
        "代码": ["601899", "600036", "300750", "601318", "000333", "600900", "002415", "600519", "000858", "002594"],
        "名称": ["紫金矿业", "招商银行", "宁德时代", "中国平安", "美的集团", "长江电力", "海康威视", "贵州茅台", "五粮液", "比亚迪"],
        "本季度收益率": [-0.082, -0.045, -0.120, -0.060, -0.030, 0.020, -0.100, -0.050, -0.090, -0.150],
        "组合权重": [0.10] * 10,
    })
    backtest_df["收益贡献"] = backtest_df["本季度收益率"] * backtest_df["组合权重"]

portfolio_ret = backtest_df["收益贡献"].sum()
win_count = (backtest_df["本季度收益率"] > 0).sum()
loss_count = (backtest_df["本季度收益率"] < 0).sum()

c1, c2, c3 = st.columns(3)
c1.metric("组合本季度收益率", f"{portfolio_ret:.2%}")
c2.metric("上涨股票数", f"{win_count} 只")
c3.metric("下跌股票数", f"{loss_count} 只")

show_bt = backtest_df.copy()
for col in ["期初价格", "期末价格"]:
    if col in show_bt.columns:
        show_bt[col] = show_bt[col].round(2)
show_bt["本季度收益率"] = show_bt["本季度收益率"].apply(lambda x: f"{x:.2%}")
show_bt["组合权重"] = show_bt["组合权重"].apply(lambda x: f"{x:.2%}")
show_bt["收益贡献"] = show_bt["收益贡献"].apply(lambda x: f"{x:.2%}")

st.dataframe(show_bt, use_container_width=True, hide_index=True)
st.bar_chart(backtest_df[["名称", "本季度收益率"]].set_index("名称"))

if portfolio_ret >= 0:
    st.success("本季度以来，当前推荐组合取得正收益，说明组合在当前市场环境下具有一定配置效果。")
else:
    st.warning(
        "从备用回测样例看，本季度组合收益为负，说明如果当前推荐组合在单季度表现不佳，"
        "模型需要进一步加入止损规则、行业分散、回撤控制和季度再平衡机制。"
    )

st.write(
    "该结果说明，仅依靠估值、流动性、趋势和季度基本面进行选股，仍可能在单季度出现较大波动。"
    "后续可以进一步加入行业分散、最大回撤控制、止损规则和季度再平衡机制，以提高组合实盘稳定性。"
)

st.header("6. 方法说明与风险提示")

st.markdown("""
**模型逻辑：**

- 行情概览：用于观察当前市场环境；
- 行业推荐：采用涨跌幅、换手率、上涨家数构建周度行业强度得分；
- 股票推荐：采用估值、流动性、趋势和季度财务指标构建综合得分；
- 组合配置：前10只股票等权配置，每只股票10%；
- 实盘回测：按照本季度以来涨跌幅计算组合实际表现。

**更新频率：**

- 行情和行业数据：可以周度观察；
- 基本面数据：由于财报按季度披露，更适合季度更新；
- 因此本系统采用“周度看行情，季度调基本面”的方式。

**局限性：**

- 当前版本使用 AkShare 公开数据，优点是免费、可复现；
- 历史 PE、PB、股息率、分析师一致预期等数据仍不完整；
- 如果后续接入 iFinD、Wind 或 Choice，可进一步补充价值因子、预期因子、行业中性化和市值中性化处理。

**风险提示：**

本系统仅用于课程研究和量化方法展示，不构成任何投资建议。
""")
