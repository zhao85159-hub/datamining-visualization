import sqlite3, os
db = os.path.join(os.path.dirname(__file__), 'data', 'app.db')
c = sqlite3.connect(db).cursor()
print('daily volume:')
for r in c.execute("select substr(listed_time,1,10) d, count(*) from postings where listed_time is not null group by d order by d").fetchall():
    print('  ', r)
print('experience levels:')
for r in c.execute('select formatted_experience_level, count(*) n from postings group by formatted_experience_level order by n desc').fetchall():
    print('  ', r)
