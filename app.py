import os
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-crm-key")

# 資料庫設定：自動相容 Neon (PostgreSQL) 與本地 SQLite 測試
db_url = os.environ.get("DATABASE_URL", "sqlite:///crm_local.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# -------------------------------------------------------------------------
# 資料庫模型 (Database Model)
# -------------------------------------------------------------------------
class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    company = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), default="新客戶")  # 新客戶, 洽談中, 已簽約, 已流失
    photo_base64 = db.Column(db.Text, nullable=True)     # 照片可有可無
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 確保資料表存在
with app.app_context():
    db.create_all()

# -------------------------------------------------------------------------
# HTML 樣式範本 (Embedded UI Templates via Tailwind CSS)
# -------------------------------------------------------------------------
BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enterprise CRM 系統</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-slate-50 font-sans text-slate-800 antialiased">
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <div class="fixed top-4 right-4 z-50 space-y-2">
          {% for category, message in messages %}
            <div class="p-4 rounded-lg shadow-lg text-white {% if category == 'error' %}bg-red-500{% else %}bg-emerald-500{% endif %} transition-all duration-300">
                {{ message }}
            </div>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}
    {% block content %}{% endblock %}
</body>
</html>
"""

FRONTEND_REGISTER_HTML = BASE_LAYOUT.replace("{% block content %}{% endblock %}", """
<div class="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-slate-900 to-slate-800">
    <div class="max-w-md w-full space-y-8 bg-white p-8 rounded-2xl shadow-xl">
        <div>
            <h2 class="text-center text-3xl font-extrabold text-slate-900">貴賓會員註冊</h2>
            <p class="mt-2 text-center text-sm text-slate-600">請填寫以下資訊，加入我們的商務生態圈</p>
        </div>
        <form id="registerForm" class="mt-8 space-y-6" action="{{ url_for('register') }}" method="POST">
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-slate-700">姓名 <span class="text-red-500">*</span></label>
                    <input type="text" name="name" required class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-lg shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div>
                    <label class="block text-sm font-medium text-slate-700">電子郵件 <span class="text-red-500">*</span></label>
                    <input type="email" name="email" required class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-lg shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div>
                    <label class="block text-sm font-medium text-slate-700">聯絡電話</label>
                    <input type="text" name="phone" class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-lg shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div>
                    <label class="block text-sm font-medium text-slate-700">公司名稱</label>
                    <input type="text" name="company" class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-lg shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div>
                    <label class="block text-sm font-medium text-slate-700">個人照片 <span class="text-xs text-slate-400">(選填)</span></label>
                    <input type="file" id="photo_file" accept="image/*" class="mt-1 block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100">
                    <input type="hidden" name="photo_base64" id="photo_base64">
                    <div id="preview_container" class="mt-3 hidden">
                        <img id="photo_preview" class="w-24 h-24 object-cover rounded-full border-2 border-indigo-500">
                    </div>
                </div>
            </div>
            <button type="submit" class="w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition duration-150">
                提交註冊資料
            </button>
        </form>
    </div>
</div>
<script>
document.getElementById('photo_file').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(event) {
            document.getElementById('photo_base64').value = event.target.result;
            document.getElementById('photo_preview').src = event.target.result;
            document.getElementById('preview_container').classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    }
});
</script>
""")

LOGIN_HTML = BASE_LAYOUT.replace("{% block content %}{% endblock %}", """
<div class="min-h-screen flex items-center justify-center bg-slate-900 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8 bg-white p-8 rounded-2xl shadow-xl">
        <div>
            <h2 class="text-center text-3xl font-extrabold text-slate-900">CRM 管理端登入</h2>
        </div>
        <form class="mt-8 space-y-6" action="{{ url_for('login') }}" method="POST">
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-slate-700">管理員帳號</label>
                    <input type="text" name="username" required class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-lg shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div>
                    <label class="block text-sm font-medium text-slate-700">密碼</label>
                    <input type="password" name="password" required class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-lg shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
            </div>
            <button type="submit" class="w-full py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-slate-800 hover:bg-slate-700 transition duration-150">
                登入系統
            </button>
        </form>
    </div>
</div>
""")

DASHBOARD_HTML = BASE_LAYOUT.replace("{% block content %}{% endblock %}", """
<div class="flex h-screen bg-slate-100">
    <div class="w-64 bg-slate-900 text-white flex flex-col justify-between">
        <div class="p-5">
            <h1 class="text-2xl font-bold tracking-wider text-indigo-400 mb-8"><i class="fa-solid fa-chart-line mr-2"></i>CORE CRM</h1>
            <nav class="space-y-2">
                <a href="#" class="flex items-center space-x-3 px-4 py-2.5 rounded-lg bg-indigo-600 text-white"><i class="fa-solid fa-users w-5"></i><span>客戶關係管理</span></a>
                <a href="{{ url_for('register') }}" target="_blank" class="flex items-center space-x-3 px-4 py-2.5 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white transition"><i class="fa-solid fa-link w-5"></i><span>前往前台註冊</span></a>
            </nav>
        </div>
        <div class="p-5 border-t border-slate-800">
            <a href="{{ url_for('logout') }}" class="flex items-center space-x-3 px-4 py-2.5 rounded-lg text-red-400 hover:bg-red-950/30 transition"><i class="fa-solid fa-right-from-bracket w-5"></i><span>登出系統</span></a>
        </div>
    </div>

    <div class="flex-1 flex flex-col overflow-y-auto">
        <header class="bg-white shadow-sm px-8 py-4 flex justify-between items-center">
            <h2 class="text-xl font-semibold text-slate-800">客戶名單總覽</h2>
            <div class="flex items-center space-x-3">
                <span class="text-sm bg-slate-100 text-slate-700 px-3 py-1 rounded-full font-medium">管理員: admin</span>
            </div>
        </header>

        <main class="p-8 space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                    <p class="text-sm text-slate-500 font-medium uppercase">總客戶數</p>
                    <p class="text-3xl font-bold text-slate-900 mt-1">{{ total_count }}</p>
                </div>
                <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                    <p class="text-sm text-slate-500 font-medium uppercase">新客戶</p>
                    <p class="text-3xl font-bold text-blue-600 mt-1">{{ status_counts['新客戶'] }}</p>
                </div>
                <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                    <p class="text-sm text-slate-500 font-medium uppercase">已簽約</p>
                    <p class="text-3xl font-bold text-emerald-600 mt-1">{{ status_counts['已簽約'] }}</p>
                </div>
                <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                    <p class="text-sm text-slate-500 font-medium uppercase">洽談中</p>
                    <p class="text-3xl font-bold text-amber-600 mt-1">{{ status_counts['洽談中'] }}</p>
                </div>
            </div>

            <div class="bg-white shadow-sm rounded-xl border border-slate-200 overflow-hidden">
                <table class="min-w-full divide-y divide-slate-200">
                    <thead class="bg-slate-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">會員</th>
                            <th class="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">聯絡資訊</th>
                            <th class="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">公司</th>
                            <th class="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">狀態管理</th>
                            <th class="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">操作</th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-slate-200">
                        {% for customer in customers %}
                        <tr>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <div class="flex items-center">
                                    <div class="h-10 w-10 flex-shrink-0">
                                        {% if customer.photo_base64 %}
                                        <img class="h-10 w-10 rounded-full object-cover border" src="{{ customer.photo_base64 }}" alt="">
                                        {% else %}
                                        <div class="h-10 w-10 rounded-full bg-slate-200 flex items-center justify-center text-slate-400 border"><i class="fa-solid fa-user"></i></div>
                                        {% endif %}
                                    </div>
                                    <div class="ml-4">
                                        <div class="text-sm font-semibold text-slate-900">{{ customer.name }}</div>
                                        <div class="text-xs text-slate-400">建立於 {{ customer.created_at.strftime('%Y-%m-%d') }}</div>
                                    </div>
                                </div>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <div class="text-sm text-slate-900"><i class="fa-regular fa-envelope mr-1 text-slate-400"></i>{{ customer.email }}</div>
                                <div class="text-xs text-slate-500"><i class="fa-solid fa-phone mr-1 text-slate-400"></i>{{ customer.phone or '無' }}</div>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                                {{ customer.company or '—' }}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <form action="{{ url_for('update_status', id=customer.id) }}" method="POST" class="inline-block">
                                    <select name="status" onchange="this.form.submit()" class="text-xs font-semibold rounded-full px-3 py-1 border {% if customer.status == '已簽約' %}bg-emerald-50 border-emerald-300 text-emerald-700{% elif customer.status == '洽談中' %}bg-amber-50 border-amber-300 text-amber-700{% elif customer.status == '已流失' %}bg-red-50 border-red-300 text-red-700{% else %}bg-blue-50 border-blue-300 text-blue-700{% endif %} focus:outline-none">
                                        <option value="新客戶" {% if customer.status == '新客戶' %}selected{% endif %}>新客戶</option>
                                        <option value="洽談中" {% if customer.status == '洽談中' %}selected{% endif %}>洽談中</option>
                                        <option value="已簽約" {% if customer.status == '已簽約' %}selected{% endif %}>已簽約</option>
                                        <option value="已流失" {% if customer.status == '已流失' %}selected{% endif %}>已流失</option>
                                    </select>
                                </form>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-3">
                                <button onclick="openEditModal({{ customer.id }}, '{{ customer.name }}', '{{ customer.email }}', '{{ customer.phone or '' }}', '{{ customer.company or '' }}', '{{ customer.status }}', '{{ customer.photo_base64 or '' }}')" class="text-indigo-600 hover:text-indigo-900 cursor-pointer"><i class="fa-solid fa-pen-to-square"></i> 編輯</button>
                                <a href="{{ url_for('delete_customer', id=customer.id) }}" onclick="return confirm('確定要刪除此客戶紀錄嗎？')" class="text-red-600 hover:text-red-900 transition"><i class="fa-solid fa-trash"></i> 刪除</a>
                            </td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="5" class="px-6 py-10 text-center text-sm text-slate-400">目前尚無會員註冊資料</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </main>
    </div>
</div>

<div id="editModal" class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center hidden">
    <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 overflow-hidden relative">
        <div class="flex justify-between items-center border-b pb-4 mb-6">
            <h3 class="text-xl font-bold text-slate-900">修改客戶基本資料</h3>
            <button onclick="closeEditModal()" class="text-slate-400 hover:text-slate-600 text-xl cursor-pointer"><i class="fa-solid fa-xmark"></i></button>
        </div>
        <form id="editForm" action="" method="POST" class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-slate-700">姓名 <span class="text-red-500">*</span></label>
                <input type="text" id="modal_name" name="name" required class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-lg shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
            </div>
            <div>
                <label class="block text-sm font-medium text-slate-700">電子郵件 <span class="text-red-500">*</span></label>
                <input type="email" id="modal_email" name="email" required class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-lg shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
            </div>
            <div>
                <label class="block text-sm font-medium text-slate-700">聯絡電話</label>
                <input type="text" id="modal_phone" name="phone" class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-lg shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
            </div>
            <div>
                <label class="block text-sm font-medium text-slate-700">公司名稱</label>
                <input type="text" id="modal_company" name="company" class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-lg shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
            </div>
            <div>
                <label class="block text-sm font-medium text-slate-700">客戶狀態</label>
                <select id="modal_status" name="status" class="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-lg shadow-sm bg-white focus:outline-none">
                    <option value="新客戶">新客戶</option>
                    <option value="洽談中">洽談中</option>
                    <option value="已簽約">已簽約</option>
                    <option value="已流失">已流失</option>
                </select>
            </div>
            <div>
                <label class="block text-sm font-medium text-slate-700">更換大頭貼 <span class="text-xs text-slate-400">(不選則維持原圖)</span></label>
                <input type="file" id="modal_photo_file" accept="image/*" class="mt-1 block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100">
                <input type="hidden" id="modal_photo_base64" name="photo_base64">
                <div class="mt-3 flex items-center space-x-4">
                    <img id="modal_photo_preview" class="w-16 h-16 object-cover rounded-full border bg-slate-100">
                    <span class="text-xs text-slate-400">目前預覽</span>
                </div>
            </div>
            <div class="flex justify-end space-x-3 pt-4 border-t mt-6">
                <button type="button" onclick="closeEditModal()" class="px-4 py-2 border border-slate-300 rounded-lg text-slate-700 bg-white hover:bg-slate-50 cursor-pointer">取消</button>
                <button type="submit" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg shadow-sm cursor-pointer">儲存變更</button>
            </div>
        </form>
    </div>
</div>

<script>
// 開啟編輯彈窗並填入舊資料
function openEditModal(id, name, email, phone, company, status, photoBase64) {
    document.getElementById('editForm').action = "/admin/customer/" + id + "/edit";
    document.getElementById('modal_name').value = name;
    document.getElementById('modal_email').value = email;
    document.getElementById('modal_phone').value = phone;
    document.getElementById('modal_company').value = company;
    document.getElementById('modal_status').value = status;
    document.getElementById('modal_photo_base64').value = photoBase64; // 保留原圖 Base64
    
    const previewImg = document.getElementById('modal_photo_preview');
    if(photoBase64) {
        previewImg.src = photoBase64;
    } else {
        previewImg.src = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 24 24' fill='none' stroke='%23cbd5e1' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2'/><circle cx='12' cy='7' r='4'/></svg>";
    }
    
    document.getElementById('editModal').classList.remove('hidden');
}

// 關閉編輯彈窗
function closeEditModal() {
    document.getElementById('editModal').classList.add('hidden');
    document.getElementById('modal_photo_file').value = ''; // 清空檔案選擇器
}

// 監聽彈窗內的照片選擇器轉 Base64
document.getElementById('modal_photo_file').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(event) {
            document.getElementById('modal_photo_base64').value = event.target.result;
            document.getElementById('modal_photo_preview').src = event.target.result;
        };
        reader.readAsDataURL(file);
    }
});
</script>
""")

# -------------------------------------------------------------------------
# 路由邏輯 (Routes & Controllers)
# -------------------------------------------------------------------------

# 前台：會員註冊
@app.route("/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        company = request.form.get("company")
        photo_base64 = request.form.get("photo_base64")

        existing = Customer.query.filter_by(email=email).first()
        if existing:
            flash("該 Email 已經註冊過！", "error")
            return render_template_string(FRONTEND_REGISTER_HTML)

        new_customer = Customer(
            name=name, email=email, phone=phone, company=company, photo_base64=photo_base64 if photo_base64 else None
        )
        db.session.add(new_customer)
        db.session.commit()
        flash("註冊成功！請登入管理系統。", "success")
        return redirect(url_for("login"))

    return render_template_string(FRONTEND_REGISTER_HTML)


# 後台：登入頁
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "admin":
            session["admin_logged_in"] = True
            flash("成功登入管理系統", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("帳號或密碼錯誤！", "error")

    return render_template_string(LOGIN_HTML)


# 後台：登出
@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    flash("已登出系統", "success")
    return redirect(url_for("login"))


# 後台：CRM 主儀表板
@app.route("/admin/dashboard")
def dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    customers = Customer.query.order_by(Customer.created_at.desc()).all()
    total_count = len(customers)

    status_counts = {"新客戶": 0, "洽談中": 0, "已簽約": 0, "已流失": 0}
    for c in customers:
        if c.status in status_counts:
            status_counts[c.status] += 1

    return render_template_string(
        DASHBOARD_HTML,
        customers=customers,
        total_count=total_count,
        status_counts=status_counts,
    )


# 路由 A：單純下拉選單快速變更「狀態」
@app.route("/admin/customer/<int:id>/status", methods=["POST"])
def update_status(id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    customer = db.session.get(Customer, id)
    if customer:
        customer.status = request.form.get("status")
        db.session.commit()
        flash(f"已更新 {customer.name} 的狀態。", "success")
    return redirect(url_for("dashboard"))


# 路由 B【全新完整功能】：後台彈出視窗提交「修改所有欄位」
@app.route("/admin/customer/<int:id>/edit", methods=["POST"])
def edit_customer(id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    customer = db.session.get(Customer, id)
    if customer:
        email = request.form.get("email")
        
        # 檢查是否有跟別人的 Email 衝突
        existing = Customer.query.filter(Customer.email == email, Customer.id != id).first()
        if existing:
            flash(f"更新失敗！Email '{email}' 已被其他客戶使用。", "error")
            return redirect(url_for("dashboard"))
            
        customer.name = request.form.get("name")
        customer.email = email
        customer.phone = request.form.get("phone")
        customer.company = request.form.get("company")
        customer.status = request.form.get("status")
        
        # 處理照片：如果有新轉換的 Base64 則覆蓋，沒有則不更動
        photo_base64 = request.form.get("photo_base64")
        if photo_base64:
            customer.photo_base64 = photo_base64

        db.session.commit()
        flash(f"已成功更新 {customer.name} 的資料！", "success")
        
    return redirect(url_for("dashboard"))


# 後台：刪除資料
@app.route("/admin/customer/<int:id>/delete")
def delete_customer(id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("login"))

    customer = db.session.get(Customer, id)
    if customer:
        db.session.delete(customer)
        db.session.commit()
        flash("客戶紀錄已成功移除。", "success")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True)
