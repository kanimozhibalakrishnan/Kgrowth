import streamlit as st
import json
import os
import random
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURATION & CONSTANTS ---
DATA_FILE = "forest_data.json"
PRIMARY_GREEN = "#88B04B"
DARK_BG = "#0D0D0D"
CARD_BG = "#161B18"

# --- DATA PERSISTENCE ---
def load_data():
    """Loads user data from local JSON file or creates a new profile."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                # Ensure structure compatibility
                if "logs" not in data: data["logs"] = []
                return data
        except:
            pass
    return {
        "total_points": 0,
        "streak": 0,
        "last_post_date": None,
        "logs": []
    }

def save_data(data):
    """Saves the current state to forest_data.json."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# --- GAME & LEVELING LOGIC ---
def get_level(points):
    """Calculates level based on 500 points per level."""
    return (points // 500) + 1

def get_tree_for_level(level):
    """Unlocks rarer trees as the user levels up."""
    common = ['🌲', '🌳', '🌿']
    uncommon = ['🌴', '🌵', '🎍']
    rare = ['🌸', '🍂', '🍄', '🍀']
    legendary = ['🎋', '🎐', '⛲']
    
    pool = list(common)
    if level >= 3: pool += uncommon
    if level >= 7: pool += rare
    if level >= 15: pool += legendary
    return random.choice(pool)

def update_streak_logic(data):
    """Checks if the streak should be reset based on last post date."""
    if not data["last_post_date"]:
        return data
        
    last_date = datetime.strptime(data["last_post_date"], "%Y-%m-%d").date()
    today = datetime.now().date()
    diff = (today - last_date).days
    
    if diff > 1:
        data["streak"] = 0  # Reset streak if a day was skipped
    return data

# --- CUSTOM THEME (CSS) ---
def apply_custom_styles():
    st.markdown(f"""
        <style>
        /* Main Container */
        .stApp {{
            background-color: {DARK_BG};
            color: #E0E2DB;
        }}
        
        /* Metric Numbers */
        [data-testid="stMetricValue"] {{
            color: {PRIMARY_GREEN} !important;
            font-family: 'Courier New', Courier, monospace;
        }}
        
        /* Task Log Cards */
        .task-card {{
            background-color: {CARD_BG};
            border-radius: 15px;
            padding: 1.2rem;
            border-left: 5px solid #4E6E5D;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }}
        
        /* Visual Forest Containers */
        .forest-box {{
            background-color: #1B241E;
            border-radius: 25px;
            padding: 2rem;
            text-align: center;
            border: 1px solid #2D3A31;
            min-height: 150px;
        }}
        
        .tree-emoji {{
            font-size: 2.8rem;
            margin: 0.3rem;
            display: inline-block;
            transition: transform 0.2s;
        }}
        .tree-emoji:hover {{
            transform: scale(1.3);
        }}

        /* Navigation Tab Customization */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 10px;
        }}
        .stTabs [data-baseweb="tab"] {{
            background-color: #1B241E;
            border-radius: 10px 10px 0 0;
            padding: 10px 20px;
            color: #738276;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: #4E6E5D !important;
            color: white !important;
        }}
        </style>
    """, unsafe_allow_html=True)

# --- MAIN APPLICATION ---
def main():
    st.set_page_config(page_title="Forest Log", page_icon="🌲", layout="centered")
    apply_custom_styles()
    
    # Load session state
    if 'data' not in st.session_state:
        st.session_state.data = update_streak_logic(load_data())
    
    data = st.session_state.data
    current_level = get_level(data["total_points"])

    # Header Metrics
    st.title("🌲 Forest Done Log")
    m1, m2, m3 = st.columns(3)
    m1.metric("Points", f"{data['total_points']:,}")
    m2.metric("Level", current_level)
    m3.metric("Streak", f"{data['streak']} Days")

    # Tabbed Navigation
    tab_dash, tab_forest, tab_log = st.tabs(["🌱 Dashboard", "🌳 My Forest", "📜 Archive"])

    # --- TAB 1: DASHBOARD ---
    with tab_dash:
        # User Input Form
        with st.container():
            st.markdown("### Plant a Task")
            task_text = st.text_input("What did you accomplish?", placeholder="Describe your win...", label_visibility="collapsed")
            effort_type = st.select_slider(
                "Effort Level",
                options=["Seed (Quick)", "Sapling (Solid)", "Oak (Big Win)"],
                value="Sapling (Solid)"
            )
            
            if st.button("Post to Log", use_container_width=True):
                if task_text:
                    # Point assignment logic
                    points_map = {"Seed (Quick)": (5, 15), "Sapling (Solid)": (20, 50), "Oak (Big Win)": (60, 150)}
                    low, high = points_map[effort_type]
                    pts_earned = random.randint(low, high)
                    
                    # Streak increment logic
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    if data["last_post_date"] != today_str:
                        data["streak"] += 1
                    
                    # Entry creation
                    tree_icon = get_tree_for_level(current_level)
                    new_entry = {
                        "id": random.getrandbits(32),
                        "date": today_str,
                        "day_name": datetime.now().strftime("%A"),
                        "task": task_text,
                        "points": pts_earned,
                        "tree": tree_icon,
                        "effort": effort_type
                    }
                    
                    data["logs"].insert(0, new_entry)
                    data["total_points"] += pts_earned
                    data["last_post_date"] = today_str
                    
                    save_data(data)
                    st.toast(f"Planting Successful! +{pts_earned} points", icon=tree_icon)
                    st.rerun()
                else:
                    st.error("The forest needs a description to grow!")

        st.divider()

        # Weekly Momentum Graph (Pandas powered)
        st.subheader("📊 Weekly Momentum")
        if data["logs"]:
            df = pd.DataFrame(data["logs"])
            df['date'] = pd.to_datetime(df['date'])
            
            # Generate the last 7 days of dates
            last_7_days = [(datetime.now() - timedelta(days=i)).date() for i in range(6, -1, -1)]
            chart_data = []
            for d in last_7_days:
                pts = df[df['date'].dt.date == d]['points'].sum()
                chart_data.append({"Day": d.strftime("%a"), "Points": pts})
            
            st.bar_chart(pd.DataFrame(chart_data).set_index("Day"), color="#88B04B")
        else:
            st.info("Log a task to start tracking your weekly momentum.")

        # Visual Daily Forest
        st.subheader("🍃 Today's Growth")
        today_date = datetime.now().strftime("%Y-%m-%d")
        today_logs = [l for l in data["logs"] if l["date"] == today_date]
        
        if today_logs:
            trees_html = "".join([f'<span class="tree-emoji" title="{l["task"]}">{l["tree"]}</span>' for l in today_logs])
            st.markdown(f'<div class="forest-box">{trees_html}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="forest-box"><p style="color:#738276; padding-top:40px;">No growth recorded yet today.</p></div>', unsafe_allow_html=True)

    # --- TAB 2: MY FOREST (STREAK VISUALIZATION) ---
    with tab_forest:
        st.subheader("Your Living Streak")
        st.write(f"This ecosystem flourishes as long as you maintain your streak. Current: {data['streak']} days.")
        
        if data["streak"] > 0:
            forest_vis = ""
            for i in range(data["streak"]):
                # Every 10th tree is a milestone flower
                icon = "🌸" if (i+1) % 10 == 0 else "🌲"
                forest_vis += f'<span class="tree-emoji">{icon}</span>'
            st.markdown(f'<div class="forest-box">{forest_vis}</div>', unsafe_allow_html=True)
        else:
            st.warning("Your forest is waiting for its first streak tree!")
            
        st.info(f"Keep leveling up! Next rare tree tier unlocks at Level {current_level + 1}")

    # --- TAB 3: LOG ARCHIVE ---
    with tab_log:
        st.subheader("The Chronicles")
        if not data["logs"]:
            st.write("Your history is currently a blank page.")
        else:
            for log in data["logs"]:
                st.markdown(f"""
                    <div class="task-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 1.2rem;">{log['tree']} <strong>{log['task']}</strong></span>
                            <span style="color: {PRIMARY_GREEN}; font-weight: bold; font-family: monospace;">+{log['points']}</span>
                        </div>
                        <div style="font-size: 0.8rem; color: #738276; margin-top: 5px;">
                            {log['day_name']}, {log['date']} • {log['effort']}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
