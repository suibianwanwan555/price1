from decimal import Decimal, getcontext
import streamlit as st

getcontext().prec = 20

# CSS：控制输入框宽度，移动端紧凑
st.markdown("""
<style>
.stTextInput > div > div > input {
    max-width: 220px !important;
}
@media (max-width: 640px) {
    .stTextInput > div > div > input {
        max-width: 160px !important;
    }
    .row-wrap {
        gap: 4px;
    }
}
</style>
""", unsafe_allow_html=True)

# ===================== 核心计算函数【原样保留，一点没改】 =====================
def calc_total_after_group_reduce(selected_items, rule_list):
    g0_items = []
    g1_items = []
    g2_items = []
    g3_items = []
    g4_items = []
    g5_items = []
    for idx, orig, disc, price, sel in selected_items:
        if sel == 0:
            g0_items.append((orig, disc, price))
        elif sel == 1:
            g1_items.append((orig, disc, price))
        elif sel == 2:
            g2_items.append((orig, disc, price))
        elif sel == 3:
            g3_items.append((orig, disc, price))
        elif sel == 4:
            g4_items.append((orig, disc, price))
        elif sel == 5:
            g5_items.append((orig, disc, price))

    def sum_price(lst):
        return sum(p for o, d, p in lst)

    g0_sum = sum_price(g0_items)
    g1_sum = sum_price(g1_items)
    g2_sum = sum_price(g2_items)
    g3_sum = sum_price(g3_items)
    g4_sum = sum_price(g4_items)
    g5_sum = sum_price(g5_items)

    def apply_rule(total, rule):
        if rule is None:
            return total
        full, reduce_val = rule
        if full <= 0:
            return total
        cnt = int(total // full)
        return total - cnt * reduce_val

    r1 = apply_rule(g1_sum, rule_list[0])
    r2 = apply_rule(g2_sum, rule_list[1])
    r3 = apply_rule(g3_sum, rule_list[2])
    r4 = apply_rule(g4_sum, rule_list[3])
    r5 = apply_rule(g5_sum, rule_list[4])
    total = g0_sum + r1 + r2 + r3 + r4 + r5
    return total, (g0_sum, g1_sum, g2_sum, g3_sum, g4_sum, g5_sum, r1, r2, r3, r4, r5), (g0_items, g1_items, g2_items, g3_items, g4_items, g5_items)

def meet_in_the_middle(item_pool, rule_list, target):
    item_pool_sorted = sorted(item_pool, key=lambda x: x[0])
    n = len(item_pool_sorted)
    if n == 0:
        return None
    mid = n // 2
    left_arr = item_pool_sorted[:mid]
    right_arr = item_pool_sorted[mid:]

    def gen_subset(arr):
        res = []
        m = len(arr)
        for mask in range(0, 1 << m):
            pack = []
            for i in range(m):
                if mask & (1 << i):
                    pack.append(arr[i])
            sum_final, _, _ = calc_total_after_group_reduce(pack, rule_list)
            res.append((sum_final, pack))
        return res

    sub_left = gen_subset(left_arr)
    sub_right = gen_subset(right_arr)

    right_dict = {}
    for s_r, pack_r in sub_right:
        if s_r not in right_dict:
            right_dict[s_r] = []
        right_dict[s_r].append(pack_r)

    for s_l, pack_l in sub_left:
        need = target - s_l
        if need in right_dict:
            for pack_r in right_dict[need]:
                combined = pack_l + pack_r
                real_total, _, _ = calc_total_after_group_reduce(combined, rule_list)
                if real_total == target:
                    return combined
    return None

def fmt_group(items):
    parts = []
    for orig, disc, p in items:
        if disc == 100:
            parts.append(f"{orig}")
        else:
            rate_str = str(float(disc / 100)).rstrip('0').rstrip('.') if '.' in str(float(disc / 100)) else str(float(disc / 100))
            parts.append(f"[{orig}×{rate_str}={p}]")
    return "+".join(parts)

# ===================== 测试数据定义 =====================
test_rows = [
    (1, "100", "90", 2), (2, "20", "", 1), (3, "30", "", 1), (4, "40", "", 5), (5, "50", "", 1),
    (6, "60", "", 2), (7, "70", "", 2), (8, "80", "", 2), (9, "90", "", 2), (10, "10", "", 1),
    (11, "110", "90", 3), (12, "125", "88", 3), (13, "130", "50", 3), (14, "145", "88", 3), (15, "155", "88", 3),
    (16, "160", "80", 0), (17, "175", "88", 0), (18, "180", "80", 5), (19, "190", "", 5), (20, "200", "", 5),
    (21, "210", "", 5), (22, "88", "", 0), (23, "135", "80", 4), (24, "220", "85", 4), (25, "230", "90", 3),
    (26, "240", "88", 4), (27, "250", "82", 4), (28, "260", "", 4), (29, "270", "", 0), (30, "280", "", 1),
]
test_target = "1401"
test_rules = [["50","5"],["200","20"],["300","30"],["250","15"],["400","20"]]

# ===================== 初始化session =====================
if "reset_ver" not in st.session_state:
    st.session_state.reset_ver = 0
if "result_pack" not in st.session_state:
    st.session_state.result_pack = None
if "result_msg" not in st.session_state:
    st.session_state.result_msg = ""
if "hit_ids" not in st.session_state:
    st.session_state.hit_ids = set()

ver = st.session_state.reset_ver
is_first = (ver == 0)

st.set_page_config(page_title="价格计算（同活动只减一次）", layout="centered")
st.title("价格计算（同活动只减一次）")

# ==========【顶部：参数设置区】==========
st.subheader("参数设置")
target_default = test_target if is_first else ""
target_val = st.text_input("目标额度", value=target_default, key=f"target_{ver}")

st.markdown("#### 5 组满减规则")
rule_data = []
rule_texts = []
for i in range(5):
    c1, c2 = st.columns(2)
    f_def, r_def = test_rules[i]
    fv = f_def if is_first else ""
    rv = r_def if is_first else ""
    f_txt = c1.text_input(f"满减{i+1}：满", value=fv, key=f"rule_full_{ver}_{i}")
    r_txt = c2.text_input(f"满减{i+1}：减", value=rv, key=f"rule_reduce_{ver}_{i}")
    rule_data.append((f_txt, r_txt))
    if f_txt.strip() and r_txt.strip():
        rule_texts.append(f"满{f_txt}减{r_txt}")
    else:
        rule_texts.append("")

btn_col1, btn_col2 = st.columns(2)
run_btn = btn_col1.button("开始计算", type="primary")
clear_btn = btn_col2.button("清空全部")
st.divider()

# ==========【结果展示区】==========
result_area = st.container()

# ==========【商品列表】==========
st.subheader("商品列表（共 30 条）")
item_data = []

# 下拉选项
sel_options = ["无满减(0)", "满减1(1)", "满减2(2)", "满减3(3)", "满减4(4)", "满减5(5)"]
sel_map = {k:i for i,k in enumerate(sel_options)}
rev_map = {i:i for i in range(6)}

for idx in range(30):
    seq, p_def, d_def, sel_def = test_rows[idx]
    pv = p_def if is_first else ""
    dv = d_def if is_first else ""
    default_sel_str = sel_options[sel_def]

    r_cols = st.columns([0.35, 1, 1, 1.3, 0.4])
    r_cols[0].write(f"{seq:02d}")
    price_str = r_cols[1].text_input("单价", value=pv, key=f"p_{ver}_{idx}", label_visibility="collapsed")
    disc_str = r_cols[2].text_input("折扣", value=dv, key=f"d_{ver}_{idx}", label_visibility="collapsed")
    sel_str = r_cols[3].selectbox("活动", sel_options, index=sel_def if is_first else 0, key=f"sel_{ver}_{idx}", label_visibility="collapsed")
    final_sel = sel_map[sel_str]

    item_data.append((idx, price_str, disc_str, final_sel))
    if idx in st.session_state.hit_ids:
        r_cols[4].markdown("✅")
    else:
        r_cols[4].write("")

# ========== 清空逻辑 ==========
if clear_btn:
    st.session_state.reset_ver += 1
    st.session_state.result_pack = None
    st.session_state.result_msg = ""
    st.session_state.hit_ids = set()
    st.rerun()

# ========== 计算 ==========
if run_btn:
    with result_area:
        with st.spinner("正在计算，请稍候..."):
            try:
                target = Decimal(target_val.strip())
            except:
                st.session_state.result_msg = "❌ 目标额度输入错误！"
                st.session_state.result_pack = None
                st.session_state.hit_ids = set()
            else:
                rule_list = []
                rule_err = False
                for f_txt, r_txt in rule_data:
                    if f_txt.strip() == "" or r_txt.strip() == "":
                        rule_list.append(None)
                    else:
                        try:
                            f = Decimal(f_txt.strip())
                            r = Decimal(r_txt.strip())
                            rule_list.append((f, r))
                        except:
                            rule_err = True
                            break
                if rule_err:
                    st.session_state.result_msg = "❌ 满减规则数字非法！"
                    st.session_state.result_pack = None
                    st.session_state.hit_ids = set()
                else:
                    item_pool = []
                    item_err = False
                    for idx, price_str, disc_str, sel in item_data:
                        if price_str.strip() == "":
                            continue
                        try:
                            val = Decimal(price_str.strip())
                            disc = Decimal(disc_str.strip()) if disc_str.strip() else Decimal("100")
                            price_disc = val * disc / Decimal("100")
                            item_pool.append((idx, val, disc, price_disc, sel))
                        except:
                            st.session_state.result_msg = f"❌ 第{idx+1}行单价/折扣格式错误！"
                            st.session_state.result_pack = None
                            st.session_state.hit_ids = set()
                            item_err = True
                            break
                    if item_err:
                        pass
                    elif len(item_pool) == 0:
                        st.session_state.result_msg = "⚠️ 没有录入有效商品！"
                        st.session_state.result_pack = None
                        st.session_state.hit_ids = set()
                    else:
                        res_pack = meet_in_the_middle(item_pool, rule_list, target)
                        st.session_state.result_pack = res_pack
                        if res_pack is None:
                            st.session_state.result_msg = f"❌ **没有找到满减后正好等于 {target} 的商品组合！**"
                            st.session_state.hit_ids = set()
                        else:
                            hit_id_set = {x[0] for x in res_pack}
                            st.session_state.hit_ids = hit_id_set
                            total, detail, group_items = calc_total_after_group_reduce(res_pack, rule_list)
                            g0, g1, g2, g3, g4, g5, r1, r2, r3, r4, r5 = detail
                            g0_items, g1_items, g2_items, g3_items, g4_items, g5_items = group_items
                            selected_prices = [str(i[1]) for i in res_pack]
                            msg_lines = []
                            msg_lines.append(f"🎯 目标额度：**{target}**")
                            msg_lines.append(f"✅ 最终合计（分组汇总后分别满减）：**{total}**")
                            msg_lines.append("🔢 选中价格：<span style='color:red'>" + ",".join(selected_prices) + "</span>")
                            msg_lines.append("📋 分组明细：")
                            if g0_items:
                                msg_lines.append(f"<b>无满减组：</b>{fmt_group(g0_items)} = {g0} → 结算：{g0}")
                            if rule_texts[0] and g1_items:
                                msg_lines.append(f"<b>{rule_texts[0]}：</b>{fmt_group(g1_items)} = {g1} → 结算：{r1}")
                            if rule_texts[1] and g2_items:
                                msg_lines.append(f"<b>{rule_texts[1]}：</b>{fmt_group(g2_items)} = {g2} → 结算：{r2}")
                            if rule_texts[2] and g3_items:
                                msg_lines.append(f"<b>{rule_texts[2]}：</b>{fmt_group(g3_items)} = {g3} → 结算：{r3}")
                            if rule_texts[3] and g4_items:
                                msg_lines.append(f"<b>{rule_texts[3]}：</b>{fmt_group(g4_items)} = {g4} → 结算：{r4}")
                            if rule_texts[4] and g5_items:
                                msg_lines.append(f"<b>{rule_texts[4]}：</b>{fmt_group(g5_items)} = {g5} → 结算：{r5}")
                            st.session_state.result_msg = "\n\n".join(msg_lines)
                            st.rerun()

with result_area:
    if st.session_state.result_msg:
        st.markdown(st.session_state.result_msg, unsafe_allow_html=True)
