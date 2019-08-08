from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

# Kullanıcı Giriş Decoratoru ---> Bunu eklememizin sebebi dashboard sayfasının giriş yapılmadan da gösterilebilmesini engellemek.

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session: #Kullanıcı giriş yaptı mı yapmadı mı?
            return f(*args, **kwargs) #sayfayı çalıştırıyoruz.
        else:
             flash("Bu sayfayı görüntülemek için lütfen giriş yapın.","danger")
             return redirect (url_for("login"))
    return decorated_function

# Kullanıcı Kayıt Formu

class RegisterForm(Form):
    name = StringField("İsim Soyisim",validators=[validators.Length(min = 4,max = 25)])
    username = StringField("Kullanıcı Adı",validators=[validators.Length(min = 3,max = 20)])
    email = StringField("Email Adresi",validators=[validators.email(message = "Lütfen geçerli bir e-mail adresi giriniz!")])
    password = PasswordField("Parola",validators=[
        validators.data_required("Lütfen bir parola giriniz!"),
        validators.equal_to(fieldname = "confirm",message="Parola uyuşmuyor!")
    ])
    confirm = PasswordField("Parola Doğrula")
        
class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Şifre")


app = Flask(__name__)
app.secret_key = "ybblog" #flash mesajları için gerekli

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "burakblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

@app.route("/")

def index():
    
    
    
# articles = [
    
 #       {"id":
 # 1,"title":"Deneme1","content":"Deneme1İçerik1"},      
  #      {"id":
  # 2,"title":"Deneme2","content":"Deneme1İçerik2"},
   #     {"id":
   # 3,"title":"Deneme3","content":"Deneme1İçerik3"}]
    
    
    return render_template("index.html")


@app.route("/about")
def about():
    
    return render_template("about.html")


@app.route("/articles")
def articles():
    
    cursor = mysql.connection.cursor()

    sorgu = "Select * From yazilar"

    result = cursor.execute(sorgu)

    if result > 0:
        
        articles = cursor.fetchall() #Tüm yazıları veritabanından alır.
        
        return render_template("articles.html",articles = articles)

    else:
        return render_template("articles.html")
    

    return render_template("articles.html")




@app.route("/articles/<string:id>")
def detail(id):
    
    return "Article Id = " + id


@app.route("/register",methods=['GET', 'POST'])
def register():
    
    form = RegisterForm(request.form)


    if request.method == "POST" and form.validate():


        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        
        
        cursor = mysql.connection.cursor() #Veritabanına ekleyeceğimiz yapıları mysql için formdan alıyoruz.


        sorgu ="Insert into users(name,username,email,password) VALUES(%s,%s,%s,%s)" # Insert into = Veritabanına yeni veriler eklemek için kullanılır.


        cursor.execute(sorgu,(name,username,email,password))
        
        
        mysql.connection.commit() #Veritabanın da değişiklik yapılacaksa commit kesinlikle kullanılmalı.


        cursor.close()
        flash("Kayıt oldunuz!",category="success")

        return redirect(url_for("login")) #method post olduğunda bizi index(/) sayfasına götürür.
    else:
        
        return render_template("register.html",form = form)

@app.route("/dashboard")
@login_required #Decatorleri dashboarda uygulamak için kullandık.
def dashboard():

    cursor = mysql.connection.cursor()

    sorgu = "Select * From yazilar where author = %s"

    result = cursor.execute(sorgu,(session["username"],)) 
    
    #son virgülü tek elemanlı dizi olduğunu belirtmek için koyduk.

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else:
        return render_template("dashboard.html")

    return render_template("dashboard.html")




#login işlemi

@app.route("/login",methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()
        
        sorgu = "Select * From users where username = %s"
       
        
        result = cursor.execute(sorgu,(username,))
    

        if result > 0:
            data = cursor.fetchone() #fetchone sayesinde bir kullanıcın tüm bilgilerini string halinde çektik.
            real_password = data["password"] #gerçek parolayı aldık.
            if sha256_crypt.verify(password_entered,real_password): #şifrelenen şifreyi verify sayesinde dönüştürüp karşılaştırıyoruz.
                flash("Hoşgeldin!","success")

                session["logged_in"] = True #Giriş yapıldığını sessiona söylüyoruz.
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash("Hatalı Parola!","danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunmuyor!","danger")
            return redirect(url_for("login"))


    return render_template("login.html",form = form)
#Detay Sayfası
@app.route("/article/<string:id>")
def article(id):
    
    cursor = mysql.connection.cursor()

    sorgu =  "Select * from yazilar where id = %s"

    result = cursor.execute(sorgu,(id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html",article = article)
    else:
        return render_template("article.html")    
    
    

#logout
@app.route("/logout")
def logout():
    session.clear() # sessionu sıfırlar.
    return redirect(url_for("index"))

@app.route("/addarticle",methods=['GET', 'POST'])
def addarticle():
    
    form = ArticleForm(request.form)
    
    if request.method == "POST" and form.validate():
        
        title = form.title.data
        
        content = form.content.data

        cursor = mysql.connection.cursor()

        sorgu = "Insert into yazilar(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(sorgu,(title,session["username"],content))

        mysql.connection.commit()

        cursor.close()

        flash("Yazın Eklendi","success")

        return redirect(url_for("dashboard"))

    return render_template("addarticle.html",form = form)

#Makale Sil

@app.route("/delete/<string:id>")
@login_required #Decoratörleri tekrar çağırdık ki login olup olmadığını anlayabilelim.

def delete(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select * from yazilar where author = %s and id = %s"

    result = cursor.execute(sorgu,(session["username"],id))

    if result > 0:
        sorgu2 = "Delete from yazilar where id = %s"

        cursor.execute(sorgu2,(id,))

        mysql.connection.commit()

        return redirect(url_for("dashboard"))

    else:
        flash("Böyle bir makale bulamadım!","danger")
        return redirect(url_for("index"))


#Makale GÜncelleme

@app.route("/edit/<string:id>",methods=['GET', 'POST'])
@login_required
def update(id):

    if request.method == "GET":
        cursor = mysql.connection.cursor()

        sorgu = "Select * from yazilar where id = %s and author = %s"
        result = cursor.execute(sorgu,(id,session["username"]))

        if result == 0:
            flash("Böyle bir makale yok!","danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()

            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("uptade.html",form = form)

    else: 
        #Post request

        form = ArticleForm(request.form)

        newTitle = form.title.data
        newContent = form.content.data

        sorgu2 = "Update yazilar Set title = %s,content = %s where id = %s"

        cursor = mysql.connection.cursor()

        cursor.execute(sorgu2,(newTitle,newContent,id))

        mysql.connection.commit()

        flash("Makale başarıyla güncellendi","success")

        return redirect(url_for("dashboard"))
    


#Makale Form 
class ArticleForm(Form):
    title = StringField("Yazı Başlığı",validators=[validators.Length(min = 5,max = 100)])
    content = TextAreaField("Yazının İçeriği",validators=[validators.Length(min = 10)])

#Arama URL
@app.route("/search",methods = ["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword") #keyword inputta verildi.

        cursor = mysql.connection.cursor()

        sorgu = "Select * from yazilar where title like '%" + keyword + "%' " #***

        result = cursor.execute(sorgu)

        if result == 0:
            flash("Aranan yazi bulunamadı!","warning")
            return redirect(url_for("articles")) 
        else:
            articles = cursor.fetchall()
            return render_template("articles.html",articles = articles)

if  __name__ == "__main__": 
    app.run(debug=True)