from decimal import Decimal, getcontext
import streamlit as st

getcontext().prec = 20

st.markdown("""
<style>
div[data-testid="stVerticalBlock"] { gap: 6px !important; }
.rule-wrap { margin-bottom:10px; }
.rule-label { font-size:15px; white-space:nowrap; }
.item-block { margin-top:14px; }
.item-title { font-weight:bold; font-size:16px; margin-bottom:4px; }
</style>
""", unsafe_allow_html=True)


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
    return total, (g0_sum, g1_sum, g2_sum, g3_sum, g4_sum, g5_sum, r1, r2, r3, r4, r5), (
        g0_items, g1_items, g2_items, g3_items, g4_items, g5_items
    )


def meet_in_the_middle(item_pool, rule_list, target):
    n = len(item_pool)
    if n == 0:
        return None
    mid = n // 2
    left_arr = item_pool[:mid]
    right_arr = item_pool[mid:]

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
        right_dict.setdefault(s_r, []).append(pack_r)

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
            s = str(float(disc / 100)).rstrip('0').rstrip('.') if '.' in str(float(disc / 100)) else str(
                float(disc / 100))
            parts.append(f"[{orig}×{s}={p}]")
    return "+".join(parts)


test_rows = [
    (1, "100", "90", 2), (2, "20", "", 1), (3, "30", "", 1), (4, "40", "", 5), (5, "50", "", 1),
    (6, "60", "", 2), (7, "70", "", 2), (8, "80", "", 2), (9, "90", "", 2), (10, "10", "", 1),
    (11, "110", "90", 3), (12, "125", "88", 3), (13, "130", "50", 3), (14, "145", "88", 3),
    (15, "155", "88", 3),
    (16, "160", "80", 0), (17, "175", "88", 0), (18, "180", "80", 5), (19, "190", "", 5),
    (20, "200", "", 5),
    (21, "210", "", 5), (22, "88", "", 0), (23, "135", "80", 4), (24, "220", "85", 4),
    (25, "230", "90", 3),
    (26, "240", "88", 4), (27, "250", "82", 4), (28, "260", "", 4), (29, "270", "", 0),
    (30, "280", "", 1),
]
test_target = "1401"
test_rules = [["50", "5"], ["200", "20"], ["300", "30"], ["250", "15"], ["400", "20"]]

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

st.subheader("参数设置")
target_val = st.text_input("目标额度", value=test_target if is_first else "", key=f"target_{ver}")

st.markdown("#### 5 组满减规则")
rule_data = []
rule_texts = []
for i in range(5):
    rid = i + 1
    f_def, r_def = test_rules[i]
    fv = f_def if is_first else ""
    rv = r_def if is_first else ""
    st.markdown(f'<div class="rule-wrap"><span class="rule-label">满{rid}</span></div>', unsafe_allow_html=True)
    f_txt = st.text_input("", value=fv, key=f"rf_{ver}_{i}", label_visibility="collapsed")
    st.markdown(f'<div class="rule-wrap"><span class="rule-label">减{rid}</span></div>', unsafe_allow_html=True)
    r_txt = st.text_input("", value=rv, key=f"rr_{ver}_{i}", label_visibility="collapsed")
    rule_data.append((f_txt, r_txt))
    if f_txt.strip() and r_txt.strip():
        rule_texts.append(f"满{f_txt}减{r_txt}")
    else:
        rule_texts.append("")

bc1, bc2 = st.columns(2)
run_btn = bc1.button("开始计算", type="primary")
clear_btn = bc2.button("清空全部")
st.divider()
result_area = st.container()

st.subheader("商品列表（共 30 条）")
sel_options = ["无满减", "满减1", "满减2", "满减3", "满减4", "满减5"]
sel_map = dict(zip(sel_options, range(6)))
item_data = []

for idx in range(30):
    seq, p_def, d_def, sel_def = test_rows[idx]
    pv = p_def if is_first else ""
    dv = d_def if is_first else ""
    st.markdown(f'<div class="item-block"><div class="item-title">{seq:02d}</div></div>', unsafe_allow_html=True)
    st.markdown('<span class="rule-label">价格</span>', unsafe_allow_html=True)
    p_str = st.text_input("", value=pv, key=f"p_{ver}_{idx}", label_visibility="collapsed")
    st.markdown('<span class="rule-label">折扣</span>', unsafe_allow_html=True)
    d_str = st.text_input("", value=dv, key=f"d_{ver}_{idx}", label_visibility="collapsed")
    st.markdown('<span class="rule-label">活动</span>', unsafe_allow_html=True)
    sel_str = st.selectbox("", sel_options, index=sel_def if is_first else 0, key=f"s_{ver}_{idx}",
                           label_visibility="collapsed")
    if idx in st.session_state.hit_ids:
        st.markdown("✅")
    item_data.append((idx, p_str, d_str, sel_map[sel_str]))

if clear_btn:
    st.session_state.reset_ver += 1
    st.session_state.result_pack = None
    st.session_state.result_msg = ""
    st.session_state.hit_ids = set()
    st.rerun()

if run_btn:
    with result_area, st.spinner("计算中..."):
        try:
            target = Decimal(target_val.strip())
        except:
            st.session_state.result_msg = "❌ 目标额度错误"
            st.session_state.result_pack = None
            st.session_state.result_msg = ""
            st.session_state.hit_ids = set()
        else:
            rule_list = []
            bad_rule = False
            for f, r in rule_data:
                if not (f.strip() and r.strip()):
                    rule_list.append(None)
                    continue
                try:
                    rule_list.append((Decimal(f), Decimal(r)))
                except:
                    bad_rule = True
                    break
            if bad_rule:
                st.session_state.result_msg = "❌ 满减数字非法"
                st.rerun()
            item_pool = []
            bad_item = False
            for idx, p_str, d_str, sel in item_data:
                if not p_str.strip():
                    continue
                try:
                    orig = Decimal(p_str.strip())
                    disc = Decimal(d_str.strip()) if d_str.strip() else Decimal("100")
                    pd = orig * disc / Decimal("100")
                    item_pool.append((idx, orig, disc, pd, sel))
                except:
                    st.session_state.result_msg = f"❌ 第 {idx + 1} 行格式错"
                    bad_item = True
                    break
            if bad_item:
                st.rerun()
            if not item_pool:
                st.session_state.result_msg = "⚠️ 无有效商品"
                st.rerun()
            res_pack = meet_in_the_middle(item_pool, rule_list, target)
            st.session_state.result_pack = res_pack
            if res_pack is None:
                st.session_state.result_msg = f"❌ 没有找到正好等于 {target} 的组合"
                st.session_state.hit_ids = set()
            else:
                hit_set = {x[0] for x in res_pack}
                st.session_state.hit_ids = hit_set
                total, detail, groups = calc_total_after_group_reduce(res_pack, rule_list)
                g0, g1, g2, g3, g4, g5, r1, r2, r3, r4, r5 = detail
                g0i, g1i, g2i, g3i, g4i, g5i = groups
                sel_prices = [str(i[1]) for i in res_pack]
                lines = [
                    f"🎯 目标额度：**{target}**",
                    f"✅ 最终合计：**{total}**",
                    "🔢 选中价格：<span style='color:red'>" + ",".join(sel_prices) + "</span>",
                    "📋 分组明细："
                ]
                if g0i:
                    lines.append(f"<b>无满减组：</b>{fmt_group(g0i)} = {g0}")
                if g1i:
                    lines.append(f"<b>{rule_texts[0]}：</b>{fmt_group(g1i)} = {g1} → {r1}")
                if g2i:
                    lines.append(f"<b>{rule_texts[1]}：</b>{fmt_group(g2i)} = {g2} → {r2}")
                if g3i:
                    lines.append(f"<b>{rule_texts[2]}：</b>{fmt_group(g3i)} = {g3} → {r3}")
                if g4i:
                    lines.append(f"<b>{rule_texts[3]}：</b>{fmt_group(g4i)} = {g4} → {r4}")
                if g5i:
                    lines.append(f"<b>{rule_texts[4]}：</b>{fmt_group(g5i)} = {g5} → {r5}")
                st.session_state.result_msg = "\n\n".join(lines)
                st.rerun()

with result_area:
    if st.session_state.result_msg:
        st.markdown(st.session_state.result_msg, unsafe_allow_html=True)
