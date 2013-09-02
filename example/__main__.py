from basemain import app, db

db.open()
db.reindex()
app.run()
