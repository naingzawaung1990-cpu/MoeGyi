import streamlit as st

# Page အပြင်အဆင်
st.set_page_config(page_title="My Store Manager", layout="wide")

# အချက်အလက်များ သိမ်းဆည်းရန် (Database အစား session_state သုံးထားသည်)
if 'store_items' not in st.session_state:
    st.session_state.store_items = [
        {"name": "Nescafe Coffee", "price": "၈၅၀၀", "img": "https://img.freepik.com/free-photo/coffee-glass-jar-with-dark-roasted-instant-coffee-granules-isolated-white-background_639032-482.jpg"},
        {"name": "Premier Milk Powder", "price": "၁၂၀၀၀", "img": "https://img.freepik.com/free-photo/milk-powder-bowl-with-spoon_23-2148827531.jpg"},
    ]

# --- Sidebar: ပစ္စည်းအသစ် ထည့်သွင်းခြင်း ---
st.sidebar.header("📦 ပစ္စည်းအသစ်ထည့်ရန်")
with st.sidebar.form("add_form", clear_on_submit=True):
    name = st.text_input("ပစ္စည်းအမည်")
    price = st.text_input("ဈေးနှုန်း (ကျပ်)")
    img_url = st.text_input("ပုံ Link (URL)", placeholder="https://example.com/image.jpg")
    submit = st.form_submit_button("စာရင်းသွင်းမည်")

    if submit:
        if name and price:
            # ပုံမထည့်ထားရင် Default ပုံတစ်ခု သုံးမည်
            final_img = img_url if img_url else "https://via.placeholder.com/150?text=No+Image"
            st.session_state.store_items.append({"name": name, "price": price, "img": final_img})
            st.rerun()

# --- Main Interface ---
st.title("🏪 Store Inventory Management")
st.write("လက်ရှိဆိုင်ထဲရှိ ပစ္စည်းများစာရင်း")

# ပစ္စည်းများကို Rows နဲ့ Columns များခွဲပြခြင်း
if not st.session_state.store_items:
    st.info("ပစ္စည်းစာရင်း မရှိသေးပါ။ Sidebar မှတစ်ဆင့် ထည့်သွင်းပါ။")
else:
    # တစ်တန်းမှာ ပစ္စည်း ၄ ခုပြမည်
    cols = st.columns(4)
    for index, item in enumerate(st.session_state.store_items):
        with cols[index % 4]:
            # ပစ္စည်း Card လေးများ
            with st.container(border=True):
                # ပုံပြသရန် (image URL ကို သုံးသည်)
                st.image(item['img'], use_container_width=True)
                st.subheader(f"{item['price']} KS")
                st.write(f"**{item['name']}**")
                
                # ခလုတ်များ
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Edit", key=f"edit_{index}"):
                        st.toast(f"{item['name']} ကို ပြင်ဆင်ရန် ရွေးချယ်ပြီး")
                with col2:
                    if st.button("Delete", key=f"del_{index}", type="primary"):
                        st.session_state.store_items.pop(index)
                        st.rerun()

st.divider()
st.caption("Developed with Cursor AI & Streamlit")