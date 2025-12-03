from passlib.context import CryptContext

# Initialize the password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Users and their passwords
users = [
    ("apazarbasilar", "Arda123"),
    ("abbas.kizil", "Abbas456"),
    ("sina.yanar", "Sina789"),
    ("efe.saribay", "Efe234"),
    ("simay.aslan", "Simay567"),
    ("ada.sarabil", "Ada890"),
    ("azra.altiparmak", "Azra123"),
    ("buke.karamustafa", "Buke456"),
    ("naz.topcuoglu", "Naz789"),
    ("semih.gulkesen", "Semih234"),
    ("nehir.cicekdag", "Nehir567"),
    ("arhan.soylu", "Arhan890"),
    ("efe.yurdsever", "Efe123"),
    ("seyhan.kasap", "Seyhan456"),
    ("sude.temizkan", "Sude789"),
    ("zeynep.taygar", "Zeynep234"),
    ("merve.goktanir", "Merve567"),
    ("wojood.sadaf", "Wojood890"),
    ("yigit.tanriverdi", "Yigit123"),
    ("ada.yenici", "Ada456"),
    ("batuhan.ozel", "Batuhan789"),
    ("beril.baydar", "Beril234"),
    ("cansu.okur", "Cansu567"),
    ("melis.turkoglu", "Melis890"),
    ("ceylin.sarisahin", "Ceylin123"),
    ("duru.arca", "Duru456"),
]

# Generate SQL INSERT statements
with open("insert_users.sql", "w") as sql_file:
    for username, password in users:
        hashed_password = pwd_context.hash(password)
        sql = f"INSERT INTO users (username, hashed_password, is_active) VALUES ('{username}', '{hashed_password}', true);\n"
        sql_file.write(sql)
        print(sql)

print("SQL statements with hashed passwords have been saved to 'insert_users.sql'")
