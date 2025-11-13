from flask import Flask, render_template_string, jsonify
import mysql.connector
from datetime import datetime

app = Flask(__name__)

TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Current DB Time</title>
  <style>
    :root{
      --bg:#0f1724;
      --card:#0b1220;
      --accent:#7c3aed;
      --muted:#9ca3af;
      --glass: rgba(255,255,255,0.03);
      --glow: 0 6px 30px rgba(124,58,237,0.18);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
    }
    html,body{
      height:100%;
      margin:0;
      background:
        radial-gradient(1000px 500px at 10% 10%, rgba(124,58,237,0.08), transparent 10%),
        radial-gradient(800px 400px at 90% 90%, rgba(14,165,233,0.03), transparent 8%),
        var(--bg);
      color:#e6eef8;
      -webkit-font-smoothing:antialiased;
      -moz-osx-font-smoothing:grayscale;
    }
    .menu-bar{
      width:100%;
      background:rgba(255,255,255,0.02);
      backdrop-filter:blur(6px);
      border-bottom:1px solid rgba(255,255,255,0.05);
      display:flex;
      justify-content:space-between;
      align-items:center;
      padding:12px 24px;
      box-sizing:border-box;
      position:fixed;
      top:0;
      left:0;
      z-index:10;
    }
    .menu-title{
      font-weight:600;
      font-size:16px;
      color:#e6eef8;
      letter-spacing:-0.01em;
    }
    .menu-button{
      padding:8px 14px;
      background:linear-gradient(135deg,var(--accent),#2563eb);
      color:white;
      border:none;
      border-radius:8px;
      font-weight:600;
      cursor:pointer;
      transition:opacity 0.15s ease, transform 0.15s ease;
    }
    .menu-button:hover{
      opacity:0.9;
      transform:translateY(-1px);
    }
    .wrap{
      min-height:100%;
      display:flex;
      align-items:center;
      justify-content:center;
      padding:100px 32px 32px;
      box-sizing:border-box;
    }
    .card{
      width:100%;
      max-width:760px;
      background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
      border-radius:16px;
      padding:28px;
      box-shadow:var(--glow);
      backdrop-filter: blur(6px) saturate(120%);
      border:1px solid rgba(255,255,255,0.04);
    }
    .header{
      display:flex;
      align-items:center;
      gap:16px;
    }
    .logo{
      width:56px;
      height:56px;
      border-radius:12px;
      display:grid;
      place-items:center;
      background:linear-gradient(135deg,var(--accent),#2563eb);
      box-shadow:0 6px 18px rgba(0,0,0,0.4), inset 0 -6px 12px rgba(255,255,255,0.02);
      font-weight:700;
      font-size:20px;
      color:white;
    }
    h1{
      margin:0;
      font-size:20px;
      letter-spacing:-0.02em;
    }
    p.lead{
      margin:6px 0 0 0;
      color:var(--muted);
      font-size:14px;
    }
    .time{
      margin-top:20px;
      display:flex;
      gap:18px;
      flex-wrap:wrap;
      align-items:center;
    }
    .big{
      font-size:48px;
      font-weight:700;
      line-height:1;
      min-width:1ch;
      font-feature-settings:"tnum";
    }
    .meta{
      color:var(--muted);
      font-size:14px;
    }
    .badge{
      padding:6px 10px;
      border-radius:999px;
      background:var(--glass);
      color:var(--muted);
      font-weight:600;
      font-size:13px;
      border:1px solid rgba(255,255,255,0.02);
    }
    .dot{
      width:10px;
      height:10px;
      border-radius:50%;
      background:linear-gradient(180deg, #34d399, #10b981);
      box-shadow:0 4px 18px rgba(16,185,129,0.18);
      display:inline-block;
      vertical-align:middle;
      margin-right:8px;
    }
    .footer{
      margin-top:18px;
      display:flex;
      justify-content:space-between;
      align-items:center;
      gap:12px;
      flex-wrap:wrap;
    }
    .small{
      color:var(--muted);
      font-size:13px;
    }
    @media (max-width:520px){
      .big{ font-size:36px; }
      .card{ padding:20px; border-radius:12px; }
    }
  </style>
</head>
<body>
  <div class="menu-bar">
    <div class="menu-title">DB Monitor</div>
    <button class="menu-button" onclick="window.location.href='/data-analysis/'">Go to Data Analysis</button>
  </div>

  <div class="wrap">
    <div class="card" role="main" aria-live="polite">
      <div class="header">
        <div class="logo">DB</div>
        <div>
          <h1>Database time</h1>
          <p class="lead">Showing the current time reported by your MySQL server</p>
        </div>
      </div>

      <div class="time" id="timeBlock">
        <div>
          <div class="big" id="timeText">{{ time_str }}</div>
        </div>

        <div style="margin-left:auto; text-align:right;">
          <div class="small"><span class="dot" id="statusDot"></span><span id="statusText">loaded</span></div>
          <div class="small" id="updatedAt">last updated: {{ fetched_at }}</div>
        </div>
      </div>

      <div class="footer">
        <div class="small">Auto-refreshes every 5 seconds (client-side).</div>
      </div>
    </div>
  </div>

  <script>
    const statusDot = document.getElementById("statusDot");
    const statusText = document.getElementById("statusText");
    const timeText = document.getElementById("timeText");
    const updatedAt = document.getElementById("updatedAt");

    function setStatus(ok){
      if(ok){
        statusDot.style.background = "linear-gradient(180deg,#34d399,#10b981)";
        statusText.textContent = "connected";
      } else {
        statusDot.style.background = "linear-gradient(180deg,#f472b6,#fb7185)";
        statusText.textContent = "error";
      }
    }

    async function fetchNow(){
      try{
        const resp = await fetch("/now", { cache: "no-store" });
        if(!resp.ok) throw new Error("non-200 response");
        const data = await resp.json();
        timeText.textContent = data.time;
        updatedAt.textContent = "last updated: " + new Date().toLocaleString();
        setStatus(true);
      } catch(err){
        console.error(err);
        setStatus(false);
      }
    }

    setInterval(fetchNow, 5000);
    window.addEventListener("load", () => setTimeout(fetchNow, 200));
  </script>
</body>
</html>
"""

def get_db_now():
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="juho",
            database="co_concentration",
            connection_timeout=5
        )
        cursor = conn.cursor()
        cursor.execute("SELECT NOW(), @@global.time_zone, @@session.time_zone")
        row = cursor.fetchone()
        if row and row[0]:
            db_time = row[0]
            tz_global = row[1] or "SYSTEM"
            tz_session = row[2] or "SYSTEM"
            return db_time, tz_global, tz_session
    except Exception as e:
        return datetime.utcnow(), "ERROR", "ERROR"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/")
def home():
    db_time, tz_global, tz_session = get_db_now()
    # Format human friendly and ISO for JS
    time_str = db_time.strftime("%Y-%m-%d %H:%M:%S")
    fetched_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    tz_display = f"global={tz_global} session={tz_session}"
    return render_template_string(
        TEMPLATE,
        time_str=time_str,
        fetched_at=fetched_at,
        tz=tz_display
    )

@app.route("/now")
def now_json():
    db_time, tz_global, tz_session = get_db_now()
    # return ISO-like string that client can display directly
    return jsonify({
        "time": db_time.strftime("%Y-%m-%d %H:%M:%S"),
        "tz": {"global": tz_global, "session": tz_session},
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
