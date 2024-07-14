import streamlit as st
import streamlit_antd_components as sac
from dashboard.home import home
from dashboard.portfolio import portfolio
from helpers.data import load_portfolios
from helpers.login_form import login_form
from streamlit_cookies_manager import EncryptedCookieManager
import json

# Set the page config as the very first Streamlit command
st.set_page_config(page_title="DeepStocks", layout="centered")

# Create a cookie manager
cookies = EncryptedCookieManager(
    prefix='deepstocks',  # optional prefix to distinguish your cookies
    password="your_secret_password"  # change this to a strong secret password
)

if not cookies.ready():
    st.stop()  # wait for the cookies manager to be ready

# Function to set authentication status
def set_auth_status(authenticated, username):
    st.session_state.auth_status = {"authenticated": authenticated, "username": username}
    cookies["auth_status"] = json.dumps({"authenticated": authenticated, "username": username})
    cookies.save()

# Initialize session state
if "auth_status" not in st.session_state:
    auth_status = cookies.get("auth_status")
    if auth_status:
        st.session_state.auth_status = json.loads(auth_status)
    else:
        st.session_state.auth_status = {"authenticated": False, "username": None}

# Custom CSS for the login page
st.markdown("""
    <style>
    .login-box {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
        margin: auto;        
        border-radius: 50px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .login-left {
        text-align: center;
        background-color: transparent;
        color: white;
        border-radius: 30px;
        padding: 50px;
        width: 100%;
    }
    .login-title {
        font-size: 2.5em;    
        font-weight: bold;
        color: white;
    }
    .login-logo {
        width: 170px;
        margin-bottom: 0px;
        border-radius: 2px;
    }
    .login-button {
        background-color: #ff4b4b;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        cursor: pointer;
    }
    </style>
""", unsafe_allow_html=True)

# Check authentication status
if not st.session_state.auth_status["authenticated"]:
    st.markdown("""
        <div class="login-box">
            <div class="login-left">
                <img src="https://i.ibb.co/RSbPFh1/candlestick-svgrepo-com.png" class="login-logo" alt="DeepStocks Logo">
                <h1 class="login-title">Welcome to Deep<span style='color: #ff4b4b;'>Stocks!</span></h1>
            </div>
    """, unsafe_allow_html=True)

    client = login_form(
        title="Sign In",
        user_tablename="users",
        username_col="username",
        password_col="password",
        create_title="Create an account 🚀",
        login_title="Login to your account 🔑",
        allow_guest=False,
        allow_create=True,
        guest_title="Guest login 🥷",
        create_username_label="Create a username",
        create_username_placeholder="JohnDoe123",
        create_password_label="Create a password",
        create_password_help="Password cannot be recovered if lost",
        create_submit_label="Continue",
        create_success_message="Account created and logged-in 🎉",
        login_username_label="Username",
        login_password_label="Password",
        login_success_message="Login succeeded 🎉",
        login_error_message="Wrong username/password ❌",
        guest_submit_label="Guest login"
    )

    if st.session_state.get("authenticated"):
        set_auth_status(st.session_state["authenticated"], st.session_state["username"])
        st.experimental_rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

else:
    username = st.session_state.auth_status["username"]

    portfolios = load_portfolios(username)

    with st.sidebar:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(
                f"""
                <div>
                    <h1 style='font-size: 2.5em; margin-top: -0.7em;'>
                        Deep<span style='color: #ff4b4b;'>Stocks</span>
                    </h1>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                f"""
                <div style='text-align: right;'>
                    <img src='https://i.ibb.co/RSbPFh1/candlestick-svgrepo-com.png' width='35' height='35'>
                </div>
                """,
                unsafe_allow_html=True
            )

        portfolio_items = [sac.MenuItem(name, icon='briefcase-fill') for name in portfolios.keys()]
        menu_items = [
            sac.MenuItem('Home', icon='house-fill'),
            sac.MenuItem('Portfolios', icon='box-fill', children=portfolio_items)
        ]
        selected_item = sac.menu(menu_items, open_all=True)

        st.markdown("---")
        if st.button("Logout"):
            set_auth_status(False, None)
            st.experimental_rerun()

    if selected_item == 'Home':
        home(username)
    elif selected_item in portfolios:
        portfolio(username, selected_item)

# Save cookies after every interaction
cookies.save()
