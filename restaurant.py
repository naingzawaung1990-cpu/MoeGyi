import streamlit as st
import uuid
import qrcode
from io import BytesIO
from PIL import Image
import json
from pathlib import Path
import os

# -------- Store Name from File Name --------
# File name ကို store name အဖြစ် သုံးမယ်
# ဥပမာ: pyaungphyu_tea_shop.py → "Pyaungphyu Tea Shop"
#         yayoo_restaurant.py → "Yayoo Restaurant"
#         restaurant.py → "Restaurant"
SCRIPT_NAME = Path(__file__).stem  # .py မပါတဲ့ file name
STORE_NAME = SCRIPT_NAME.replace("_", " ").title()  # File name ကို store name အဖြစ် convert

# Page အပြင်အဆင်
st.set_page_config(
    page_title=f"{STORE_NAME} - Store Manager",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------- Auth / Mode --------
# Default = Customer view. Admin wants to edit => click Admin => enter key (12345)
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "show_admin_login" not in st.session_state:
    st.session_state.show_admin_login = False

ADMIN_KEY = "12345"

# -------- Data Storage: File name နဲ့ match လုပ်မယ် --------
# File name ကို store ID အဖြစ် သုံးမယ်
STORE_ID = SCRIPT_NAME  # File name ကို store ID အဖြစ် သုံး
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

# အချက်အလက်များ သိမ်းဆည်းရန် (File name နဲ့ match လုပ်ထားသော data file)
loaded_items, loaded_qr = _load_data()
if 'store_items' not in st.session_state:
    if loaded_items is not None:
        st.session_state.store_items = loaded_items
    else:
        st.session_state.store_items = [
            {
                "id": str(uuid.uuid4()),
                "name": "Nescafe Coffee",
                "price": "၈၅၀၀",
                "img": "https://img.freepik.com/free-photo/coffee-glass-jar-with-dark-roasted-instant-coffee-granules-isolated-white-background_639032-482.jpg"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Premier Milk Powder",
                "price": "၁၂၀၀၀",
                "img": "https://img.freepik.com/free-photo/milk-powder-bowl-with-spoon_23-2148827531.jpg"
            },
        ]

# QR prices storage (separate from main product prices)
if 'qr_prices' not in st.session_state:
    st.session_state.qr_prices = loaded_qr if loaded_qr is not None else {}  # {item_id: qr_price}

# Ensure data file exists after initialization
if loaded_items is None and loaded_qr is None:
    _save_data()

# Edit mode tracking
if 'editing_id' not in st.session_state:
    st.session_state.editing_id = None

# QR code generation tracking
if 'qr_generating_id' not in st.session_state:
    st.session_state.qr_generating_id = None

# Search query initialization
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""

# Base URL for QR codes (for production deployment)
if 'qr_base_url' not in st.session_state:
    st.session_state.qr_base_url = ""  # Leave empty for relative URLs, or set full domain

# Helper Functions
def validate_price(price_str):
    """ဈေးနှုန်းကို စစ်ဆေးရန်"""
    if not price_str or price_str.strip() == "":
        return False
    return True

def generate_qr_code(data):
    """QR Code ထုတ်လုပ်ရန်"""
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

# --- Sidebar / Header controls ---
query_params = st.query_params
is_product_page = "product_id" in query_params

if not is_product_page:
    st.sidebar.header("⚙️ စနစ်ထိန်းချုပ်မှု")
    st.sidebar.caption(f"🏪 **{STORE_NAME}**")
    st.sidebar.divider()

    colA, colB = st.sidebar.columns(2)
    with colA:
        if st.button("👤 Customer", use_container_width=True):
            st.session_state.is_admin = False
            st.session_state.show_admin_login = False
            st.rerun()
    with colB:
        if st.button("👨‍💼 Admin", use_container_width=True, type="primary"):
            st.session_state.show_admin_login = True
            st.rerun()

    # Admin login prompt
    if st.session_state.show_admin_login and not st.session_state.is_admin:
        st.sidebar.divider()
        st.sidebar.subheader("🔐 Admin Key ထည့်ပါ")
        key_input = st.sidebar.text_input("Key", type="password")
        if st.sidebar.button("Login", use_container_width=True):
            if (key_input or "").strip() == ADMIN_KEY:
                st.session_state.is_admin = True
                st.session_state.show_admin_login = False
                st.sidebar.success("✅ Admin Mode ဖွင့်ပြီးပါပြီ။")
                st.rerun()
            else:
                st.sidebar.error("❌ Key မှားနေပါတယ်။")

    if st.session_state.is_admin:
        st.sidebar.success("👨‍💼 Admin Mode")
        if st.sidebar.button("Logout", use_container_width=True):
            st.session_state.is_admin = False
            st.session_state.show_admin_login = False
            st.session_state.editing_id = None
            st.session_state.qr_generating_id = None
            st.rerun()

# Admin Mode Features (Only show in Admin Mode and not on product page)
if st.session_state.is_admin and not is_product_page:
    st.sidebar.header("📦 ပစ္စည်းစီမံခန့်ခွဲမှု")
    
    # Search/Filter
    st.sidebar.subheader("🔍 ရှာဖွေရန်")
    st.session_state.search_query = st.sidebar.text_input("ပစ္စည်းအမည် ရှာဖွေပါ", value=st.session_state.search_query)
    
    # Add New Item Form
    st.sidebar.subheader("➕ ပစ္စည်းအသစ်ထည့်ရန်")
    with st.sidebar.form("add_form", clear_on_submit=True):
        name = st.text_input("ပစ္စည်းအမည် *", placeholder="ဥပမာ: Nescafe Coffee")
        price = st.text_input("ဈေးနှုန်း (ကျပ်) *", placeholder="ဥပမာ: ၈၅၀၀")
        img_url = st.text_input("ပုံ Link (URL)", placeholder="https://example.com/image.jpg")
        submit = st.form_submit_button("✅ စာရင်းသွင်းမည်", use_container_width=True)
    
        if submit:
            if not name or not name.strip():
                st.sidebar.error("⚠️ ပစ္စည်းအမည် ထည့်သွင်းရန် လိုအပ်ပါသည်။")
            elif not validate_price(price):
                st.sidebar.error("⚠️ ဈေးနှုန်း ထည့်သွင်းရန် လိုအပ်ပါသည်။")
            else:
                # ပုံမထည့်ထားရင် Default ပုံတစ်ခု သုံးမည်
                final_img = img_url.strip() if img_url and img_url.strip() else "https://via.placeholder.com/300x200?text=No+Image"
                st.session_state.store_items.append({
                    "id": str(uuid.uuid4()),
                    "name": name.strip(),
                    "price": price.strip(),
                    "img": final_img
                })
                _save_data()
                st.sidebar.success(f"✅ {name} ကို အောင်မြင်စွာ ထည့်သွင်းပြီးပါပြီ။")
                st.rerun()
    
    # QR Code Base URL Configuration
    st.sidebar.divider()
    st.sidebar.subheader("🔗 QR Code URL Setting")
    qr_base_url = st.sidebar.text_input(
        "Base URL (Production)", 
        value=st.session_state.qr_base_url,
        placeholder="https://your-store.streamlit.app (သို့မဟုတ်) ဗလာထားပါ",
        help="Production deploy လုပ်လျှင် full URL ထည့်ပါ။ Local test အတွက် ဗလာထားနိုင်သည်။"
    )
    st.session_state.qr_base_url = qr_base_url.strip()
    
    # Statistics
    st.sidebar.divider()
    st.sidebar.metric("📊 စုစုပေါင်း ပစ္စည်းများ", len(st.session_state.store_items))
else:
    # Customer Mode - Simple Search Only (only if not on product page)
    if not is_product_page:
        st.sidebar.header("🔍 ရှာဖွေရန်")
        st.session_state.search_query = st.sidebar.text_input("ပစ္စည်းအမည် ရှာဖွေပါ", value=st.session_state.search_query)
        st.sidebar.divider()
        st.sidebar.metric("📊 စုစုပေါင်း ပစ္စည်းများ", len(st.session_state.store_items))

# --- Product Page (for QR Code) ---
# Check if this is a product page request (from QR code)
# Note: query_params already defined above
if 'product_id' in query_params:
    product_id = query_params['product_id']

    # Reload data from file to get latest updates (Admin ပြင်ထားတာတွေ ရောက်အောင်)
    fresh_items, fresh_qr = _load_data()
    if fresh_items is not None:
        st.session_state.store_items = fresh_items
    if fresh_qr is not None:
        st.session_state.qr_prices = fresh_qr
    
    product = next((item for item in st.session_state.store_items if item['id'] == product_id), None)
    
    if product:
        # Product page is customer view by default. Admin can click Admin and enter key to edit.
        is_admin_access = bool(st.session_state.is_admin)
        
        # Get QR price if exists, otherwise use main price
        display_price = st.session_state.qr_prices.get(product_id, product['price'])
        has_qr_price = product_id in st.session_state.qr_prices
        
        # Hide sidebar + header for customer view only
        if not is_admin_access:
            st.markdown(
                """
                <style>
                  [data-testid="stSidebar"] { display: none !important; }
                  [data-testid="stHeader"] { display: none !important; }
                  .stDeployButton { display: none !important; }
                </style>
                """,
                unsafe_allow_html=True,
            )
        
        # Product Page Display
        st.title(f"📦 {product['name']}")
        st.divider()
        
        col1, col2 = st.columns([1, 1])
        with col1:
            try:
                st.image(product['img'], use_container_width=True)
            except:
                st.image("https://via.placeholder.com/400x400?text=Image+Error", use_container_width=True)
        
        with col2:
            st.markdown(f"## {product['name']}")
            st.markdown(f"### 💰 {display_price} KS")
            if has_qr_price:
                st.caption(f"💡 QR Code ဈေးနှုန်း (မူလဈေးနှုန်း: {product['price']} KS)")
            st.divider()
            
            if is_admin_access:
                st.warning("🔐 Admin Mode - ပြင်ဆင်နိုင်ပါသည်။")
            else:
                st.success("📱 QR Code ဖြင့် ရောက်ရှိလာသော ပစ္စည်းဖြစ်ပါသည်။")
                st.info("🏪 ဆိုင်သို့ လာရောက်ဝယ်ယူနိုင်ပါသည်။")
                # Customer page "Admin" button (prompts key via sidebar if not product page;
                # here we show an inline login prompt)
                with st.expander("👨‍💼 Admin (Edit)"):
                    key_inline = st.text_input("Admin Key", type="password", key=f"inline_admin_key_{product_id}")
                    if st.button("Login as Admin", key=f"inline_admin_login_{product_id}", type="primary"):
                        if (key_inline or "").strip() == ADMIN_KEY:
                            st.session_state.is_admin = True
                            st.success("✅ Admin Mode ဖွင့်ပြီးပါပြီ။")
                            st.rerun()
                        else:
                            st.error("❌ Key မှားနေပါတယ်။")
        
        # Admin Edit Section (only if admin access)
        if is_admin_access:
            st.divider()
            st.subheader("✏️ Admin: ပြင်ဆင်ရန်")
            with st.form(f"admin_edit_{product_id}", clear_on_submit=False):
                new_name = st.text_input("ပစ္စည်းအမည်", value=product['name'], key=f"admin_name_{product_id}")
                new_price = st.text_input("ဈေးနှုန်း", value=product['price'], key=f"admin_price_{product_id}")
                new_qr_price = st.text_input("QR Code ဈေးနှုန်း", value=display_price, key=f"admin_qr_price_{product_id}")
                new_img = st.text_input("ပုံ Link", value=product['img'], key=f"admin_img_{product_id}")
                
                col_save, col_cancel = st.columns(2)
                with col_save:
                    save_btn = st.form_submit_button("💾 သိမ်းဆည်းမည်", use_container_width=True, type="primary")
                with col_cancel:
                    cancel_btn = st.form_submit_button("❌ ပယ်ဖျက်မည်", use_container_width=True)
                
                if save_btn:
                    if new_name.strip() and validate_price(new_price):
                        # Update main product
                        for i, store_item in enumerate(st.session_state.store_items):
                            if store_item['id'] == product_id:
                                st.session_state.store_items[i] = {
                                    "id": product_id,
                                    "name": new_name.strip(),
                                    "price": new_price.strip(),
                                    "img": new_img.strip() if new_img.strip() else "https://via.placeholder.com/300x200?text=No+Image"
                                }
                                break
                        
                        # Update QR price if different
                        if validate_price(new_qr_price):
                            st.session_state.qr_prices[product_id] = new_qr_price.strip()
                        elif product_id in st.session_state.qr_prices:
                            del st.session_state.qr_prices[product_id]
                        
                        _save_data()
                        st.success("✅ အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ။")
                        st.rerun()
                    else:
                        st.error("⚠️ အချက်အလက်များ ပြည့်စုံစွာ ဖြည့်သွင်းပါ။")
        
        # Back button
        if st.button("← နောက်သို့ ပြန်သွားမည်"):
            st.query_params.clear()
            st.rerun()

        st.stop()  # Stop here, don't show main interface

# --- Main Interface ---
# Reload data from file to get latest updates (Admin ပြင်ထားတာတွေ ရောက်အောင်)
if not is_product_page:
    fresh_items, fresh_qr = _load_data()
    if fresh_items is not None:
        st.session_state.store_items = fresh_items
    if fresh_qr is not None:
        st.session_state.qr_prices = fresh_qr

st.title(f"🏪 {STORE_NAME}" if not st.session_state.is_admin else f"🏪 {STORE_NAME} - Inventory Management")
st.write("လက်ရှိဆိုင်ထဲရှိ ပစ္စည်းများစာရင်း")

# Filter items based on search
filtered_items = st.session_state.store_items
if st.session_state.search_query:
    filtered_items = [
        item for item in st.session_state.store_items
        if st.session_state.search_query.lower() in item['name'].lower()
    ]

# ပစ္စည်းများကို Rows နဲ့ Columns များခွဲပြခြင်း
if not st.session_state.store_items:
    st.info("ℹ️ ပစ္စည်းစာရင်း မရှိသေးပါ။ Sidebar မှတစ်ဆင့် ထည့်သွင်းပါ။")
elif not filtered_items:
    st.warning(f"⚠️ '{st.session_state.search_query}' နှင့် ကိုက်ညီသော ပစ္စည်းများ မတွေ့ရှိပါ။")
else:
    # တစ်တန်းမှာ ပစ္စည်း ၄ ခုပြမည်
    items_per_row = 4
    for row_start in range(0, len(filtered_items), items_per_row):
        cols = st.columns(items_per_row)
        row_items = filtered_items[row_start:row_start + items_per_row]
        
        for col_idx, item in enumerate(row_items):
            item_id = item['id']
            
            with cols[col_idx]:
                # ပစ္စည်း Card လေးများ
                with st.container(border=True):
                    # Edit Mode Check
                    is_editing = st.session_state.editing_id == item_id
                    
                    # QR Code Generation Mode
                    if st.session_state.qr_generating_id == item_id:
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
                                    # Store QR price separately (doesn't affect main product price)
                                    st.session_state.qr_prices[item_id] = qr_price.strip()
                                    _save_data()
                                    
                                    # Product page URL (file name က store name ဖြစ်သွားတော့ store_id မလိုတော့ဘူး)
                                    product_url = f"?product_id={item_id}"
                                    if st.session_state.qr_base_url:
                                        base_url = st.session_state.qr_base_url.rstrip('/')
                                        full_url = f"{base_url}{product_url}"
                                    else:
                                        full_url = product_url
                                    
                                    # Generate QR Code with URL
                                    qr_img = generate_qr_code(full_url)
                                    
                                    # Convert to bytes for download
                                    buf = BytesIO()
                                    qr_img.save(buf, format='PNG')
                                    buf.seek(0)
                                    
                                    st.success("✅ QR Code အောင်မြင်စွာ ထုတ်လုပ်ပြီးပါပြီ။")
                                    st.info(f"📱 QR Code ကို scan လုပ်လျှင် product page သို့ ရောက်ရှိမည်။\n💡 QR Code ဈေးနှုန်း: {qr_price} KS\n📝 မှတ်ချက်: ဈေးနှုန်းပြောင်းလျှင် QR Code အသစ် ထုတ်လုပ်ရန် လိုအပ်ပါသည်။")
                                    st.image(qr_img, caption=f"{qr_name} - {qr_price} KS", use_container_width=True)
                                    
                                    # Show the URL for reference
                                    with st.expander("🔗 Product Page URL (Reference)"):
                                        st.markdown("**Customer URL (QR Code):**")
                                        st.code(full_url, language=None)
                                        st.caption("ဤ URL ကို QR Code တွင် သိမ်းဆည်းထားပါသည်။")
                                        st.warning("⚠️ Production တွင် deploy လုပ်လျှင် full domain URL ကို သုံးရန် လိုအပ်ပါသည်။")
                                    
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
                    
                    # Edit Mode (Admin Only)
                    elif is_editing and st.session_state.is_admin:
                        # Edit Form
                        st.subheader("✏️ ပြင်ဆင်နေသည်")
                        with st.form(f"edit_form_{item_id}", clear_on_submit=False):
                            new_name = st.text_input("ပစ္စည်းအမည်", value=item['name'], key=f"edit_name_{item_id}")
                            new_price = st.text_input("ဈေးနှုန်း", value=item['price'], key=f"edit_price_{item_id}")
                            new_img = st.text_input("ပုံ Link", value=item['img'], key=f"edit_img_{item_id}")
                            
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                save_btn = st.form_submit_button("💾 သိမ်းဆည်းမည်", use_container_width=True)
                            with col_cancel:
                                cancel_btn = st.form_submit_button("❌ ပယ်ဖျက်မည်", use_container_width=True)
                            
                            if save_btn:
                                if new_name.strip() and validate_price(new_price):
                                    # Find and update item by ID
                                    for i, store_item in enumerate(st.session_state.store_items):
                                        if store_item['id'] == item_id:
                                            st.session_state.store_items[i] = {
                                                "id": item_id,
                                                "name": new_name.strip(),
                                                "price": new_price.strip(),
                                                "img": new_img.strip() if new_img.strip() else "https://via.placeholder.com/300x200?text=No+Image"
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
                        # Display Mode
                        # ပုံပြသရန် (image URL ကို သုံးသည်)
                        try:
                            st.image(item['img'], use_container_width=True, caption=item['name'])
                        except Exception as e:
                            st.image("https://via.placeholder.com/300x200?text=Image+Error", use_container_width=True)
                            st.caption(item['name'])
                        
                        # Price and Name
                        st.markdown(f"### 💰 {item['price']} KS")
                        st.markdown(f"**📦 {item['name']}**")
                        
                        # Admin Mode Buttons (Edit, Delete, QR Code)
                        if st.session_state.is_admin:
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if st.button("✏️ Edit", key=f"edit_{item_id}", use_container_width=True):
                                    st.session_state.editing_id = item_id
                                    st.rerun()
                            with col2:
                                if st.button("🗑️ Delete", key=f"del_{item_id}", type="primary", use_container_width=True):
                                    # Confirmation
                                    st.session_state.delete_confirm_id = item_id
                                    st.rerun()
                            with col3:
                                if st.button("📱 QR Code", key=f"qr_{item_id}", use_container_width=True):
                                    st.session_state.qr_generating_id = item_id
                                    st.rerun()

# Delete Confirmation Dialog
if 'delete_confirm_id' in st.session_state:
    item_id_to_delete = st.session_state.delete_confirm_id
    item_to_delete = next((item for item in st.session_state.store_items if item['id'] == item_id_to_delete), None)
    
    if item_to_delete:
        item_name = item_to_delete['name']
        st.warning(f"⚠️ သေချာပါသလား? '{item_name}' ကို ဖျက်မည်လား?")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("✅ ဟုတ်ကဲ့၊ ဖျက်မည်", key="confirm_delete", type="primary", use_container_width=True):
                st.session_state.store_items = [item for item in st.session_state.store_items if item['id'] != item_id_to_delete]
                if st.session_state.editing_id == item_id_to_delete:
                    st.session_state.editing_id = None
                del st.session_state.delete_confirm_id
                # also remove QR price if exists
                if item_id_to_delete in st.session_state.qr_prices:
                    del st.session_state.qr_prices[item_id_to_delete]
                _save_data()
                st.success(f"✅ {item_name} ကို အောင်မြင်စွာ ဖျက်ပြီးပါပြီ။")
                st.rerun()
        with col_no:
            if st.button("❌ မဖျက်တော့ပါ", key="cancel_delete", use_container_width=True):
                del st.session_state.delete_confirm_id
                st.rerun()

# Footer
st.divider()
st.caption("💻 Developed with Cursor AI & Streamlit | 🏪 Store Inventory Management System")
