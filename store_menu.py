import streamlit as st
import uuid
import qrcode
import html
from io import BytesIO
from PIL import Image
import json
from pathlib import Path
import os

# -------- Store Name from File Name --------
SCRIPT_NAME = Path(__file__).stem
STORE_NAME = SCRIPT_NAME.replace("_", " ").title()

# Page အပြင်အဆင်
st.set_page_config(
    page_title=f"{STORE_NAME} - Menu",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------- Auth / Mode --------
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "show_admin_login" not in st.session_state:
    st.session_state.show_admin_login = False

ADMIN_KEY = "12345"

# -------- Data Storage --------
STORE_ID = SCRIPT_NAME
DATA_FILE = Path(f"store_data_{STORE_ID}.json")

def _load_data():
    try:
        if DATA_FILE.exists():
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            items = data.get("store_items", [])
            qr_prices = data.get("qr_prices", {})
            return items, qr_prices
    except Exception:
        pass
    return None, None

def _save_data():
    try:
        payload = {
            "store_items": st.session_state.store_items,
            "qr_prices": st.session_state.qr_prices,
        }
        DATA_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception as e:
        if st.session_state.get("is_admin"):
            st.error(f"Data save error: {e}")

# အချက်အလက်များ သိမ်းဆည်းရန်
loaded_items, loaded_qr = _load_data()
if 'store_items' not in st.session_state:
    if loaded_items is not None:
        st.session_state.store_items = loaded_items
    else:
        # Default items with categories
        st.session_state.store_items = [
            {"id": str(uuid.uuid4()), "name": "TEA", "price": "10", "category": "tea"},
            {"id": str(uuid.uuid4()), "name": "MASALA TEA", "price": "10", "category": "tea"},
            {"id": str(uuid.uuid4()), "name": "GINGER TEA", "price": "10", "category": "tea"},
            {"id": str(uuid.uuid4()), "name": "LEMON TEA", "price": "20", "category": "tea"},
            {"id": str(uuid.uuid4()), "name": "GREEN TEA", "price": "20", "category": "tea"},
            {"id": str(uuid.uuid4()), "name": "COFFEE", "price": "15", "category": "juice"},
            {"id": str(uuid.uuid4()), "name": "BLACK COFFEE", "price": "15", "category": "juice"},
            {"id": str(uuid.uuid4()), "name": "MILK", "price": "15", "category": "juice"},
            {"id": str(uuid.uuid4()), "name": "SAMOSA", "price": "20", "category": "snack"},
            {"id": str(uuid.uuid4()), "name": "BISCUIT", "price": "10", "category": "snack"},
        ]

if 'qr_prices' not in st.session_state:
    st.session_state.qr_prices = loaded_qr if loaded_qr is not None else {}

if loaded_items is None and loaded_qr is None:
    _save_data()

if 'editing_id' not in st.session_state:
    st.session_state.editing_id = None
if 'qr_generating_id' not in st.session_state:
    st.session_state.qr_generating_id = None
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'qr_base_url' not in st.session_state:
    st.session_state.qr_base_url = ""
if 'category_images' not in st.session_state:
    st.session_state.category_images = {
        "tea": "https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=400",
        "juice": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=400",
        "snack": "https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=400"
    }

def validate_price(price_str):
    if not price_str or price_str.strip() == "":
        return False
    return True

def generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

def get_category_name(category):
    category_names = {"tea": "TEA", "juice": "JUICE", "snack": "SNACK"}
    return category_names.get(category, category.upper())

# --- Sidebar / Header controls ---
query_params = st.query_params
is_product_page = "product_id" in query_params

if not is_product_page:
    # Admin Login / Logout
    if not st.session_state.is_admin:
        st.sidebar.header("⚙️ Admin Settings")
        key_input = st.sidebar.text_input("Enter Key", type="password")
        if st.sidebar.button("Login"):
            if (key_input or "").strip() == ADMIN_KEY:
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.sidebar.error("❌ Key မှားနေပါတယ်။")
    else:
        st.sidebar.header(f"🏪 {STORE_NAME}")
        st.sidebar.success("👨‍💼 Admin Mode")
        if st.sidebar.button("Logout", use_container_width=True):
            st.session_state.is_admin = False
            st.session_state.editing_id = None
            st.session_state.qr_generating_id = None
            st.rerun()

if st.session_state.is_admin and not is_product_page:
    st.sidebar.header("📦 ပစ္စည်းစီမံခန့်ခွဲမှု")
    st.sidebar.subheader("🔍 ရှာဖွေရန်")
    st.session_state.search_query = st.sidebar.text_input("ပစ္စည်းအမည် ရှာဖွေပါ", value=st.session_state.search_query)
    st.sidebar.subheader("➕ ပစ္စည်းအသစ်ထည့်ရန်")
    with st.sidebar.form("add_form", clear_on_submit=True):
        name = st.text_input("ပစ္စည်းအမည် *", placeholder="ဥပမာ: TEA")
        price = st.text_input("ဈေးနှုန်း *", placeholder="ဥပမာ: 10")
        category = st.selectbox("အမျိုးအစား *", ["tea", "juice", "snack"], format_func=get_category_name)
        submit = st.form_submit_button("✅ စာရင်းသွင်းမည်", use_container_width=True)
        if submit:
            if not name or not name.strip():
                st.sidebar.error("⚠️ ပစ္စည်းအမည် ထည့်သွင်းရန် လိုအပ်ပါသည်။")
            elif not validate_price(price):
                st.sidebar.error("⚠️ ဈေးနှုန်း ထည့်သွင်းရန် လိုအပ်ပါသည်။")
            else:
                st.session_state.store_items.append({
                    "id": str(uuid.uuid4()),
                    "name": name.strip(),
                    "price": price.strip(),
                    "category": category
                })
                _save_data()
                st.sidebar.success(f"✅ {name} ကို အောင်မြင်စွာ ထည့်သွင်းပြီးပါပြီ။")
                st.rerun()

    st.sidebar.divider()
    st.sidebar.subheader("🖼️ Category Images")
    for cat in ["tea", "juice", "snack"]:
        cat_name = get_category_name(cat)
        img_url = st.sidebar.text_input(
            f"{cat_name} Image URL",
            value=st.session_state.category_images.get(cat, ""),
            key=f"cat_img_{cat}",
            help=f"Image URL for {cat_name} category"
        )
        if img_url:
            st.session_state.category_images[cat] = img_url

    st.sidebar.divider()
    st.sidebar.subheader("🔗 QR Code URL Setting")
    qr_base_url = st.sidebar.text_input(
        "Base URL (Production)",
        value=st.session_state.qr_base_url,
        placeholder="https://your-store.streamlit.app (သို့မဟုတ်) ဗလာထားပါ",
        help="Production deploy လုပ်လျှင် full URL ထည့်ပါ။ Local test အတွက် ဗလာထားနိုင်သည်။"
    )
    st.session_state.qr_base_url = qr_base_url.strip()
    st.sidebar.divider()
    st.sidebar.metric("📊 စုစုပေါင်း ပစ္စည်းများ", len(st.session_state.store_items))
else:
    # Customer mode - show Admin Settings login only
    pass

# --- Product Page (for QR Code) ---
if 'product_id' in query_params:
    product_id = query_params['product_id']
    fresh_items, fresh_qr = _load_data()
    if fresh_items is not None:
        st.session_state.store_items = fresh_items
    if fresh_qr is not None:
        st.session_state.qr_prices = fresh_qr

    product = next((item for item in st.session_state.store_items if item['id'] == product_id), None)

    if product:
        is_admin_access = bool(st.session_state.is_admin)
        display_price = st.session_state.qr_prices.get(product_id, product['price'])
        has_qr_price = product_id in st.session_state.qr_prices
        product_category = product.get('category', 'tea')
        cat_img_url = st.session_state.category_images.get(product_category, "")

        # Menu style - ပုံနဲ့ ဈေးနှုန်း ဘေးတိုက် (ဖုန်းမှာပါ fix)
        name_esc = html.escape(product['name'])
        price_esc = html.escape(str(display_price))
        cat_name = get_category_name(product_category)
        
        caption_html = ""
        if has_qr_price:
            orig_esc = html.escape(str(product['price']))
            caption_html = f'<p class="qr-caption">QR ဈေးနှုန်း (မူလ: {orig_esc})</p>'
        
        img_html = ""
        if cat_img_url:
            url_esc = html.escape(cat_img_url)
            img_html = f'<img src="{url_esc}" alt="{name_esc}" class="menu-product-img" />'
        
        # Full page HTML with inline CSS (mobile-fixed side-by-side)
        menu_html = f'''
        <style>
            /* Reset & Base */
            .menu-page-container {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #f5f0e1;
                min-height: 100vh;
                padding: 0;
                margin: -1rem;
                width: calc(100% + 2rem);
            }}
            .menu-page-inner {{
                max-width: 500px;
                margin: 0 auto;
                padding: 16px;
            }}
            /* Category Header */
            .menu-cat-header {{
                background: #b8860b;
                color: #fff;
                text-align: center;
                padding: 10px 16px;
                border-radius: 20px;
                font-size: 1.1em;
                font-weight: 600;
                margin-bottom: 16px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            }}
            /* Product Card - FORCED side-by-side */
            .menu-product-card {{
                display: flex !important;
                flex-direction: row !important;
                flex-wrap: nowrap !important;
                align-items: flex-start !important;
                gap: 12px !important;
                background: #fff;
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 12px;
                box-shadow: 0 2px 12px rgba(0,0,0,0.08);
                width: 100% !important;
                box-sizing: border-box !important;
            }}
            /* Info Section */
            .menu-product-info {{
                flex: 1 1 0% !important;
                min-width: 0 !important;
                display: flex !important;
                flex-direction: column !important;
            }}
            .menu-product-name {{
                color: #8b4513;
                font-size: 1.15em;
                font-weight: 600;
                margin: 0 0 8px 0;
                word-wrap: break-word;
            }}
            .menu-price-row {{
                display: flex !important;
                align-items: center !important;
                gap: 8px !important;
                flex-wrap: nowrap !important;
            }}
            .menu-dotted {{
                flex: 1 !important;
                min-width: 20px !important;
                border-bottom: 2px dotted #b8860b !important;
                height: 0 !important;
            }}
            .menu-price {{
                color: #b8860b;
                font-size: 1.2em;
                font-weight: bold;
                white-space: nowrap !important;
            }}
            .qr-caption {{
                color: #888;
                font-size: 0.8em;
                margin-top: 6px;
            }}
            /* Image Section */
            .menu-img-wrap {{
                flex: 0 0 auto !important;
                width: 100px !important;
                min-width: 100px !important;
                max-width: 100px !important;
            }}
            .menu-product-img {{
                width: 100% !important;
                height: auto !important;
                border-radius: 8px;
                display: block !important;
                object-fit: cover;
            }}
            /* Footer */
            .menu-footer {{
                background: #b8860b;
                color: #fff;
                text-align: center;
                padding: 12px;
                border-radius: 0 0 12px 12px;
                margin-top: 16px;
                font-size: 0.9em;
            }}
            .menu-footer a {{
                color: #fff;
                text-decoration: none;
            }}
            /* Mobile fixes - FORCE side-by-side */
            @media screen and (max-width: 768px) {{
                .menu-page-inner {{ padding: 12px; }}
                .menu-product-card {{
                    display: flex !important;
                    flex-direction: row !important;
                    flex-wrap: nowrap !important;
                    padding: 12px !important;
                    gap: 10px !important;
                }}
                .menu-product-name {{ font-size: 1.05em; }}
                .menu-price {{ font-size: 1.1em; }}
                .menu-img-wrap {{
                    width: 90px !important;
                    min-width: 90px !important;
                    max-width: 90px !important;
                }}
            }}
            @media screen and (max-width: 480px) {{
                .menu-page-inner {{ padding: 10px; }}
                .menu-product-card {{
                    display: flex !important;
                    flex-direction: row !important;
                    flex-wrap: nowrap !important;
                    padding: 10px !important;
                    gap: 8px !important;
                }}
                .menu-product-name {{ font-size: 1em; }}
                .menu-price {{ font-size: 1em; }}
                .menu-img-wrap {{
                    width: 80px !important;
                    min-width: 80px !important;
                    max-width: 80px !important;
                }}
                .menu-cat-header {{ font-size: 1em; padding: 8px 12px; }}
            }}
        </style>
        <div class="menu-page-container">
            <div class="menu-page-inner">
                <div class="menu-cat-header">{cat_name}</div>
                <div class="menu-product-card">
                    <div class="menu-product-info">
                        <p class="menu-product-name">{name_esc}</p>
                        <div class="menu-price-row">
                            <span class="menu-dotted"></span>
                            <span class="menu-price">{price_esc}</span>
                        </div>
                        {caption_html}
                    </div>
                    <div class="menu-img-wrap">
                        {img_html}
                    </div>
                </div>
                <div class="menu-footer">
                    🏪 {html.escape(STORE_NAME)}
                </div>
            </div>
        </div>
        '''
        
        if not is_admin_access:
            # Hide sidebar/header for customer
            st.markdown(
                """
                <style>
                    [data-testid="stSidebar"] { display: none !important; }
                    [data-testid="stHeader"] { display: none !important; }
                    .stDeployButton { display: none !important; }
                    section.main .block-container {
                        padding: 0 !important;
                        max-width: 100% !important;
                    }
                    .stApp { background: #f5f0e1 !important; }
                </style>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(menu_html, unsafe_allow_html=True)
        else:
            st.title(f"📦 {product['name']}")
            st.divider()
            st.markdown(menu_html, unsafe_allow_html=True)
        st.divider()

        if is_admin_access:
            st.warning("🔐 Admin Mode - ပြင်ဆင်နိုင်ပါသည်။")
        else:
            st.success("📱 QR Code ဖြင့် ရောက်ရှိလာသော ပစ္စည်းဖြစ်ပါသည်။")
            st.info("🏪 ဆိုင်သို့ လာရောက်ဝယ်ယူနိုင်ပါသည်။")
            with st.expander("👨‍💼 Admin (Edit)"):
                key_inline = st.text_input("Admin Key", type="password", key=f"inline_admin_key_{product_id}")
                if st.button("Login as Admin", key=f"inline_admin_login_{product_id}", type="primary"):
                    if (key_inline or "").strip() == ADMIN_KEY:
                        st.session_state.is_admin = True
                        st.success("✅ Admin Mode ဖွင့်ပြီးပါပြီ။")
                        st.rerun()
                    else:
                        st.error("❌ Key မှားနေပါတယ်။")

        if is_admin_access:
            st.divider()
            st.subheader("✏️ Admin: ပြင်ဆင်ရန်")
            with st.form(f"admin_edit_{product_id}", clear_on_submit=False):
                new_name = st.text_input("ပစ္စည်းအမည်", value=product['name'], key=f"admin_name_{product_id}")
                new_price = st.text_input("ဈေးနှုန်း", value=product['price'], key=f"admin_price_{product_id}")
                new_qr_price = st.text_input("QR Code ဈေးနှုန်း", value=display_price, key=f"admin_qr_price_{product_id}")
                new_category = st.selectbox(
                    "အမျိုးအစား", ["tea", "juice", "snack"],
                    index=["tea", "juice", "snack"].index(product.get('category', 'tea')),
                    format_func=get_category_name,
                    key=f"admin_category_{product_id}"
                )
                col_save, col_cancel = st.columns(2)
                with col_save:
                    save_btn = st.form_submit_button("💾 သိမ်းဆည်းမည်", use_container_width=True, type="primary")
                with col_cancel:
                    cancel_btn = st.form_submit_button("❌ ပယ်ဖျက်မည်", use_container_width=True)
                if save_btn:
                    if new_name.strip() and validate_price(new_price):
                        for i, store_item in enumerate(st.session_state.store_items):
                            if store_item['id'] == product_id:
                                st.session_state.store_items[i] = {
                                    "id": product_id,
                                    "name": new_name.strip(),
                                    "price": new_price.strip(),
                                    "category": new_category
                                }
                                break
                        if validate_price(new_qr_price):
                            st.session_state.qr_prices[product_id] = new_qr_price.strip()
                        elif product_id in st.session_state.qr_prices:
                            del st.session_state.qr_prices[product_id]
                        _save_data()
                        st.success("✅ အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ။")
                        st.rerun()
                    else:
                        st.error("⚠️ အချက်အလက်များ ပြည့်စုံစွာ ဖြည့်သွင်းပါ။")

        if st.button("← နောက်သို့ ပြန်သွားမည်"):
            st.query_params.clear()
            st.rerun()

        st.stop()

# --- Main Interface ---
if not is_product_page:
    fresh_items, fresh_qr = _load_data()
    if fresh_items is not None:
        st.session_state.store_items = fresh_items
    if fresh_qr is not None:
        st.session_state.qr_prices = fresh_qr

st.title(f"🏪 {STORE_NAME}")
st.write("**Menu List**")

filtered_items = st.session_state.store_items
if st.session_state.search_query:
    filtered_items = [
        item for item in st.session_state.store_items
        if st.session_state.search_query.lower() in item['name'].lower()
    ]

categories = ["tea", "juice", "snack"]
category_items = {cat: [] for cat in categories}
for item in filtered_items:
    cat = item.get('category', 'tea')
    if cat in category_items:
        category_items[cat].append(item)

if not st.session_state.store_items:
    st.info("ℹ️ ပစ္စည်းစာရင်း မရှိသေးပါ။ Sidebar မှတစ်ဆင့် ထည့်သွင်းပါ။")
elif not filtered_items:
    st.warning(f"⚠️ '{st.session_state.search_query}' နှင့် ကိုက်ညီသော ပစ္စည်းများ မတွေ့ရှိပါ။")
else:
    st.markdown("""
    <style>
    .stApp { background-color: #f5f5e8; }
    .menu-category-header {
        color: #1a5f1a; font-size: 1.8em; font-weight: bold;
        margin: 30px 0 15px 0; padding-bottom: 10px; border-bottom: 2px solid #1a5f1a;
    }
    .menu-item-row {
        display: flex; justify-content: space-between; align-items: center;
        padding: 8px 0; margin: 5px 0; color: #1a5f1a; font-size: 1.1em;
        border-bottom: 1px dotted #1a5f1a;
    }
    .menu-item-name { flex: 1; color: #1a5f1a; font-weight: 500; }
    .menu-item-price { color: #1a5f1a; font-weight: bold; margin-left: 20px; }
    .category-layout { display: block !important; width: 100% !important; margin: 10px 0 !important; }
    .category-layout [data-testid="column-container"] {
        display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important;
        width: 100% !important; gap: 10px !important;
    }
    .category-layout [data-testid="column"] {
        display: flex !important; flex-direction: column !important;
        flex: 1 1 auto !important; min-width: 0 !important; max-width: 100% !important; overflow: hidden !important;
    }
    @media screen and (max-width: 768px) {
        .category-layout [data-testid="column-container"] { gap: 8px !important; }
        .category-layout [data-testid="column"] { max-width: 50% !important; padding: 0 4px !important; }
    }
    @media screen and (max-width: 480px) {
        .category-layout [data-testid="column-container"] { gap: 5px !important; }
        .category-layout [data-testid="column"] { max-width: 50% !important; padding: 0 3px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

    for category in categories:
        items_in_category = category_items[category]
        if not items_in_category:
            continue
        category_name = get_category_name(category)
        st.markdown(f'<div class="menu-category-header">{category_name}</div>', unsafe_allow_html=True)
        if category == "juice":
            st.markdown('<div class="category-layout">', unsafe_allow_html=True)
            col_img, col_items = st.columns([1, 2])
        else:
            st.markdown('<div class="category-layout">', unsafe_allow_html=True)
            col_items, col_img = st.columns([2, 1])

        with col_items:
            for item in items_in_category:
                item_id = item['id']
                is_editing = st.session_state.editing_id == item_id
                if st.session_state.qr_generating_id == item_id:
                    with st.container(border=True):
                        st.subheader("📱 QR Code ထုတ်လုပ်နေသည်")
                        with st.form(f"qr_form_{item_id}", clear_on_submit=False):
                            qr_name = st.text_input("ပစ္စည်းအမည်", value=item['name'], key=f"qr_name_{item_id}")
                            qr_price = st.text_input("ဈေးနှုန်း (ပြင်ဆင်နိုင်သည်)", value=item['price'], key=f"qr_price_{item_id}")
                            col_generate, col_cancel_qr = st.columns(2)
                            with col_generate:
                                generate_btn = st.form_submit_button("📱 QR Code ထုတ်မည်", use_container_width=True, type="primary")
                            with col_cancel_qr:
                                cancel_qr_btn = st.form_submit_button("❌ ပယ်ဖျက်မည်", use_container_width=True)
                            if generate_btn:
                                if qr_name.strip() and validate_price(qr_price):
                                    st.session_state.qr_prices[item_id] = qr_price.strip()
                                    _save_data()
                                    product_url = f"?product_id={item_id}"
                                    base = st.session_state.qr_base_url.rstrip('/') if st.session_state.qr_base_url else ""
                                    full_url = f"{base}{product_url}" if base else product_url
                                    qr_img = generate_qr_code(full_url)
                                    buf = BytesIO()
                                    qr_img.save(buf, format='PNG')
                                    buf.seek(0)
                                    st.success("✅ QR Code အောင်မြင်စွာ ထုတ်လုပ်ပြီးပါပြီ။")
                                    st.info(f"📱 QR Code ကို scan လုပ်လျှင် product page သို့ ရောက်ရှိမည်။\n💡 QR Code ဈေးနှုန်း: {qr_price}")
                                    st.image(qr_img, caption=f"{qr_name} - {qr_price}", use_container_width=True)
                                    with st.expander("🔗 Product Page URL (Reference)"):
                                        st.markdown("**Customer URL (QR Code):**")
                                        st.code(full_url, language=None)
                                    st.download_button(
                                        label="⬇️ QR Code ဒေါင်းလုဒ်လုပ်မည်",
                                        data=buf,
                                        file_name=f"QR_{qr_name.replace(' ', '_')}.png",
                                        mime="image/png",
                                        use_container_width=True
                                    )
                                    st.session_state.qr_generating_id = None
                                else:
                                    st.error("⚠️ အချက်အလက်များ ပြည့်စုံစွာ ဖြည့်သွင်းပါ။")
                            if cancel_qr_btn:
                                st.session_state.qr_generating_id = None
                                st.rerun()
                elif is_editing and st.session_state.is_admin:
                    with st.container(border=True):
                        st.subheader("✏️ ပြင်ဆင်နေသည်")
                        with st.form(f"edit_form_{item_id}", clear_on_submit=False):
                            new_name = st.text_input("ပစ္စည်းအမည်", value=item['name'], key=f"edit_name_{item_id}")
                            new_price = st.text_input("ဈေးနှုန်း", value=item['price'], key=f"edit_price_{item_id}")
                            new_category = st.selectbox("အမျိုးအစား", ["tea", "juice", "snack"],
                                index=["tea", "juice", "snack"].index(item.get('category', 'tea')),
                                format_func=get_category_name, key=f"edit_category_{item_id}")
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                save_btn = st.form_submit_button("💾 သိမ်းဆည်းမည်", use_container_width=True)
                            with col_cancel:
                                cancel_btn = st.form_submit_button("❌ ပယ်ဖျက်မည်", use_container_width=True)
                            if save_btn:
                                if new_name.strip() and validate_price(new_price):
                                    for i, store_item in enumerate(st.session_state.store_items):
                                        if store_item['id'] == item_id:
                                            st.session_state.store_items[i] = {
                                                "id": item_id, "name": new_name.strip(),
                                                "price": new_price.strip(), "category": new_category
                                            }
                                            break
                                    _save_data()
                                    st.session_state.editing_id = None
                                    st.rerun()
                                else:
                                    st.error("⚠️ အချက်အလက်များ ပြည့်စုံစွာ ဖြည့်သွင်းပါ။")
                            if cancel_btn:
                                st.session_state.editing_id = None
                                st.rerun()
                else:
                    st.markdown(
                        f'<div class="menu-item-row">'
                        f'<span class="menu-item-name">{html.escape(item["name"])}</span>'
                        f'<span class="menu-item-price">{html.escape(item["price"])}</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                    if st.session_state.is_admin:
                        col_edit, col_del, col_qr = st.columns(3)
                        with col_edit:
                            if st.button("✏️", key=f"edit_{item_id}", use_container_width=True):
                                st.session_state.editing_id = item_id
                                st.rerun()
                        with col_del:
                            if st.button("🗑️", key=f"del_{item_id}", use_container_width=True):
                                st.session_state.delete_confirm_id = item_id
                                st.rerun()
                        with col_qr:
                            if st.button("📱", key=f"qr_{item_id}", use_container_width=True):
                                st.session_state.qr_generating_id = item_id
                                st.rerun()
        with col_img:
            cat_img_url = st.session_state.category_images.get(category, "")
            if cat_img_url:
                try:
                    st.image(cat_img_url, use_container_width=True, caption="")
                except Exception:
                    st.write("")
            else:
                st.write("")
        st.markdown('</div>', unsafe_allow_html=True)
        st.divider()

if 'delete_confirm_id' in st.session_state:
    item_id_to_delete = st.session_state.delete_confirm_id
    item_to_delete = next((item for item in st.session_state.store_items if item['id'] == item_id_to_delete), None)
    if item_to_delete:
        item_name = item_to_delete['name']
        st.warning(f"⚠️ သေချာပါသလား? '{item_name}' ကို ဖျက်မည်လား?")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("✅ ဟုတ်ကဲ့၊ ဖျက်မည်", key="confirm_delete", type="primary", use_container_width=True):
                st.session_state.store_items = [i for i in st.session_state.store_items if i['id'] != item_id_to_delete]
                if st.session_state.editing_id == item_id_to_delete:
                    st.session_state.editing_id = None
                del st.session_state.delete_confirm_id
                if item_id_to_delete in st.session_state.qr_prices:
                    del st.session_state.qr_prices[item_id_to_delete]
                _save_data()
                st.success(f"✅ {item_name} ကို အောင်မြင်စွာ ဖျက်ပြီးပါပြီ။")
                st.rerun()
        with col_no:
            if st.button("❌ မဖျက်တော့ပါ", key="cancel_delete", use_container_width=True):
                del st.session_state.delete_confirm_id
                st.rerun()

st.divider()
st.caption("💻 Developed with Cursor AI & Streamlit | 🏪 Store Inventory Management System")
